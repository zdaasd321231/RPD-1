import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Optional, BinaryIO
from datetime import datetime
import aiofiles
import aiofiles.os
from fastapi import UploadFile, HTTPException
from models import FileItem, FileOperation, FileType, LogEntry, LogLevel, LogSource
from database import db
import asyncio
from cryptography.fernet import Fernet
import base64

class FileManagerService:
    def __init__(self):
        self.base_path = Path("/app/file_storage")  # Base directory for file operations
        self.upload_path = self.base_path / "uploads"
        self.download_path = self.base_path / "downloads"
        self.temp_path = self.base_path / "temp"
        
        # Create directories if they don't exist
        asyncio.create_task(self.init_directories())
        
        # Encryption key for file encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    async def init_directories(self):
        """Initialize required directories"""
        for path in [self.base_path, self.upload_path, self.download_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for file encryption"""
        key_file = self.base_path / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    async def list_files(self, path: str = "/", user_id: str = None) -> List[FileItem]:
        """List files and directories in the specified path"""
        try:
            # Sanitize path
            if path.startswith("/"):
                path = path[1:]
            
            full_path = self.base_path / path
            
            # Security check - prevent directory traversal
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
            
            if not full_path.exists():
                raise HTTPException(status_code=404, detail="Path not found")
            
            if not full_path.is_dir():
                raise HTTPException(status_code=400, detail="Path is not a directory")
            
            files = []
            
            for item in full_path.iterdir():
                try:
                    stat = item.stat()
                    
                    file_item = FileItem(
                        name=item.name,
                        path=str(item.relative_to(self.base_path)),
                        type=FileType.folder if item.is_dir() else FileType.file,
                        size=stat.st_size if item.is_file() else None,
                        modified=datetime.fromtimestamp(stat.st_mtime),
                        permissions=oct(stat.st_mode)[-3:],
                        owner=str(stat.st_uid),
                        is_encrypted=item.name.endswith('.encrypted')
                    )
                    
                    # Calculate checksum for files
                    if item.is_file() and file_item.size and file_item.size < 10 * 1024 * 1024:  # < 10MB
                        file_item.checksum = await self._calculate_file_checksum(item)
                    
                    files.append(file_item)
                    
                except (OSError, PermissionError):
                    continue
            
            # Sort: directories first, then files
            files.sort(key=lambda x: (x.type == FileType.file, x.name.lower()))
            
            await self._log_file_operation(
                user_id, "LIST", path, success=True
            )
            
            return files
            
        except HTTPException:
            raise
        except Exception as e:
            await self._log_file_operation(
                user_id, "LIST", path, success=False, error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")
    
    async def upload_file(self, file: UploadFile, path: str, user_id: str, encrypt: bool = True) -> FileItem:
        """Upload a file to the specified path"""
        try:
            # Validate file size
            await self._validate_file_upload(file)
            
            # Sanitize path and filename
            if path.startswith("/"):
                path = path[1:]
            
            filename = self._sanitize_filename(file.filename)
            full_path = self.upload_path / path / filename
            
            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            if full_path.exists():
                # Create unique filename
                base, ext = os.path.splitext(filename)
                counter = 1
                while full_path.exists():
                    filename = f"{base}_{counter}{ext}"
                    full_path = self.upload_path / path / filename
                    counter += 1
            
            # Save file
            file_size = 0
            checksum_hash = hashlib.sha256()
            
            async with aiofiles.open(full_path, 'wb') as f:
                while chunk := await file.read(8192):  # Read in 8KB chunks
                    file_size += len(chunk)
                    checksum_hash.update(chunk)
                    
                    if encrypt:
                        chunk = self.cipher.encrypt(chunk)
                    
                    await f.write(chunk)
            
            checksum = checksum_hash.hexdigest()
            
            # If encrypted, rename file
            if encrypt:
                encrypted_path = full_path.with_suffix(full_path.suffix + '.encrypted')
                full_path.rename(encrypted_path)
                full_path = encrypted_path
            
            # Create file item
            stat = full_path.stat()
            file_item = FileItem(
                name=full_path.name,
                path=str(full_path.relative_to(self.base_path)),
                type=FileType.file,
                size=file_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                permissions=oct(stat.st_mode)[-3:],
                is_encrypted=encrypt,
                checksum=checksum
            )
            
            await self._log_file_operation(
                user_id, "UPLOAD", str(full_path.relative_to(self.base_path)), 
                file_size=file_size, success=True
            )
            
            return file_item
            
        except HTTPException:
            raise
        except Exception as e:
            await self._log_file_operation(
                user_id, "UPLOAD", path, success=False, error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    
    async def download_file(self, file_path: str, user_id: str) -> tuple[BinaryIO, str, int]:
        """Download a file"""
        try:
            # Sanitize path
            if file_path.startswith("/"):
                file_path = file_path[1:]
            
            full_path = self.base_path / file_path
            
            # Security check
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
            
            if not full_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            if not full_path.is_file():
                raise HTTPException(status_code=400, detail="Path is not a file")
            
            file_size = full_path.stat().st_size
            filename = full_path.name
            
            # If file is encrypted, decrypt it
            if filename.endswith('.encrypted'):
                filename = filename[:-10]  # Remove .encrypted extension
                
                # Create temporary decrypted file
                temp_file = self.temp_path / f"temp_{datetime.now().timestamp()}_{filename}"
                
                async with aiofiles.open(full_path, 'rb') as encrypted_file:
                    async with aiofiles.open(temp_file, 'wb') as decrypted_file:
                        while chunk := await encrypted_file.read(8192):
                            decrypted_chunk = self.cipher.decrypt(chunk)
                            await decrypted_file.write(decrypted_chunk)
                
                full_path = temp_file
                file_size = full_path.stat().st_size
            
            await self._log_file_operation(
                user_id, "DOWNLOAD", file_path, file_size=file_size, success=True
            )
            
            # Return file handle, filename, and size
            return open(full_path, 'rb'), filename, file_size
            
        except HTTPException:
            raise
        except Exception as e:
            await self._log_file_operation(
                user_id, "DOWNLOAD", file_path, success=False, error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")
    
    async def delete_file(self, file_path: str, user_id: str) -> bool:
        """Delete a file or directory"""
        try:
            # Sanitize path
            if file_path.startswith("/"):
                file_path = file_path[1:]
            
            full_path = self.base_path / file_path
            
            # Security check
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
            
            if not full_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            file_size = 0
            if full_path.is_file():
                file_size = full_path.stat().st_size
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(full_path)
            
            await self._log_file_operation(
                user_id, "DELETE", file_path, file_size=file_size, success=True
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            await self._log_file_operation(
                user_id, "DELETE", file_path, success=False, error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
    
    async def create_directory(self, dir_path: str, user_id: str) -> FileItem:
        """Create a new directory"""
        try:
            # Sanitize path
            if dir_path.startswith("/"):
                dir_path = dir_path[1:]
            
            full_path = self.base_path / dir_path
            
            # Security check
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
            
            if full_path.exists():
                raise HTTPException(status_code=400, detail="Directory already exists")
            
            full_path.mkdir(parents=True, exist_ok=True)
            
            stat = full_path.stat()
            file_item = FileItem(
                name=full_path.name,
                path=str(full_path.relative_to(self.base_path)),
                type=FileType.folder,
                modified=datetime.fromtimestamp(stat.st_mtime),
                permissions=oct(stat.st_mode)[-3:]
            )
            
            await self._log_file_operation(
                user_id, "CREATE_DIR", dir_path, success=True
            )
            
            return file_item
            
        except HTTPException:
            raise
        except Exception as e:
            await self._log_file_operation(
                user_id, "CREATE_DIR", dir_path, success=False, error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Error creating directory: {str(e)}")
    
    async def move_file(self, source_path: str, dest_path: str, user_id: str) -> bool:
        """Move/rename a file or directory"""
        try:
            # Sanitize paths
            if source_path.startswith("/"):
                source_path = source_path[1:]
            if dest_path.startswith("/"):
                dest_path = dest_path[1:]
            
            source_full = self.base_path / source_path
            dest_full = self.base_path / dest_path
            
            # Security checks
            if not str(source_full.resolve()).startswith(str(self.base_path.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
            if not str(dest_full.resolve()).startswith(str(self.base_path.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
            
            if not source_full.exists():
                raise HTTPException(status_code=404, detail="Source file not found")
            
            if dest_full.exists():
                raise HTTPException(status_code=400, detail="Destination already exists")
            
            # Create destination directory if needed
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file/directory
            shutil.move(str(source_full), str(dest_full))
            
            await self._log_file_operation(
                user_id, "MOVE", f"{source_path} -> {dest_path}", success=True
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            await self._log_file_operation(
                user_id, "MOVE", f"{source_path} -> {dest_path}", success=False, error=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Error moving file: {str(e)}")
    
    async def get_file_operations_history(self, user_id: str, limit: int = 100) -> List[FileOperation]:
        """Get file operations history for a user"""
        try:
            cursor = db.file_operations.find(
                {"user_id": user_id},
                sort=[("timestamp", -1)],
                limit=limit
            )
            
            operations = []
            async for doc in cursor:
                operations.append(FileOperation(**doc))
            
            return operations
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting file operations: {str(e)}")
    
    async def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        try:
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for root, dirs, files in os.walk(self.base_path):
                dir_count += len(dirs)
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except OSError:
                        continue
            
            # Get disk usage
            disk_usage = shutil.disk_usage(self.base_path)
            
            return {
                "total_files": file_count,
                "total_directories": dir_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "disk_total_gb": round(disk_usage.total / (1024 * 1024 * 1024), 2),
                "disk_used_gb": round(disk_usage.used / (1024 * 1024 * 1024), 2),
                "disk_free_gb": round(disk_usage.free / (1024 * 1024 * 1024), 2)
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting storage stats: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues"""
        # Remove path separators and other dangerous characters
        filename = os.path.basename(filename)
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename or "unnamed_file"
    
    async def _validate_file_upload(self, file: UploadFile):
        """Validate file upload against settings"""
        # Get settings
        settings = await db.settings.find_one({})
        if not settings:
            max_size_mb = 100
            allowed_extensions = ["pdf", "doc", "docx", "txt", "jpg", "png", "zip"]
        else:
            file_settings = settings.get('files', {})
            max_size_mb = file_settings.get('max_file_size', 100)
            allowed_extensions = file_settings.get('allowed_extensions', [])
        
        # Check file size
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if len(content) > max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413, 
                detail=f"File size exceeds limit of {max_size_mb}MB"
            )
        
        # Check file extension
        if file.filename:
            ext = file.filename.split('.')[-1].lower()
            if allowed_extensions and ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
                )
    
    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ""
    
    async def _log_file_operation(self, user_id: str, operation: str, file_path: str, 
                                 file_size: int = None, success: bool = True, error: str = None):
        """Log file operation"""
        try:
            operation_record = FileOperation(
                user_id=user_id,
                operation_type=operation,
                file_path=file_path,
                file_size=file_size,
                success=success,
                error_message=error
            )
            
            await db.file_operations.insert_one(operation_record.dict())
            
            # Also log to main logs
            log_entry = LogEntry(
                level=LogLevel.INFO if success else LogLevel.ERROR,
                source=LogSource.FILE_MANAGER,
                message=f"File operation: {operation} {file_path}" + (f" - {error}" if error else ""),
                details={
                    "operation": operation,
                    "file_path": file_path,
                    "file_size": file_size,
                    "success": success
                },
                user_id=user_id
            )
            
            await db.logs.insert_one(log_entry.dict())
            
        except Exception as e:
            print(f"Error logging file operation: {e}")

# Create global instance
file_manager = FileManagerService()