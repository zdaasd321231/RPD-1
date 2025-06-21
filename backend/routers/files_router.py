from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from models import User, FileItem, FileOperation, SuccessResponse
from auth import get_current_user
from services.file_manager import file_manager
import os
import tempfile

router = APIRouter(prefix="/files", tags=["File Management"])

@router.get("/list", response_model=List[FileItem])
async def list_files(
    path: str = "/",
    current_user: User = Depends(get_current_user)
):
    """List files and directories in the specified path"""
    return await file_manager.list_files(path, current_user.id)

@router.post("/upload", response_model=FileItem)
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form("/"),
    encrypt: bool = Form(True),
    current_user: User = Depends(get_current_user)
):
    """Upload a file to the specified path"""
    return await file_manager.upload_file(file, path, current_user.id, encrypt)

@router.get("/download/{file_path:path}")
async def download_file(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """Download a file"""
    try:
        file_handle, filename, file_size = await file_manager.download_file(file_path, current_user.id)
        
        def file_generator():
            try:
                while True:
                    chunk = file_handle.read(8192)
                    if not chunk:
                        break
                    yield chunk
            finally:
                file_handle.close()
                # Clean up temporary file if it exists
                if hasattr(file_handle, 'name') and 'temp_' in file_handle.name:
                    try:
                        os.unlink(file_handle.name)
                    except:
                        pass
        
        return StreamingResponse(
            file_generator(),
            media_type='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(file_size)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@router.delete("/delete", response_model=SuccessResponse)
async def delete_file(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a file or directory"""
    success = await file_manager.delete_file(file_path, current_user.id)
    
    if success:
        return SuccessResponse(message="File deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file")

@router.post("/create-directory", response_model=FileItem)
async def create_directory(
    path: str,
    current_user: User = Depends(get_current_user)
):
    """Create a new directory"""
    return await file_manager.create_directory(path, current_user.id)

@router.post("/move", response_model=SuccessResponse)
async def move_file(
    source_path: str,
    dest_path: str,
    current_user: User = Depends(get_current_user)
):
    """Move/rename a file or directory"""
    success = await file_manager.move_file(source_path, dest_path, current_user.id)
    
    if success:
        return SuccessResponse(message="File moved successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to move file")

@router.get("/operations", response_model=List[FileOperation])
async def get_file_operations(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get file operations history"""
    return await file_manager.get_file_operations_history(current_user.id, limit)

@router.get("/storage-stats")
async def get_storage_stats(current_user: User = Depends(get_current_user)):
    """Get storage statistics"""
    return await file_manager.get_storage_stats()

@router.post("/bulk-delete", response_model=SuccessResponse)
async def bulk_delete_files(
    file_paths: List[str],
    current_user: User = Depends(get_current_user)
):
    """Delete multiple files"""
    try:
        deleted_count = 0
        errors = []
        
        for file_path in file_paths:
            try:
                success = await file_manager.delete_file(file_path, current_user.id)
                if success:
                    deleted_count += 1
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
        
        message = f"Deleted {deleted_count} files successfully"
        if errors:
            message += f". Errors: {'; '.join(errors)}"
        
        return SuccessResponse(
            message=message,
            data={"deleted_count": deleted_count, "errors": errors}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk delete: {str(e)}")

@router.post("/bulk-download")
async def bulk_download_files(
    file_paths: List[str],
    current_user: User = Depends(get_current_user)
):
    """Download multiple files as a ZIP archive"""
    try:
        import zipfile
        import io
        
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in file_paths:
                try:
                    file_handle, filename, _ = await file_manager.download_file(file_path, current_user.id)
                    
                    # Read file content
                    content = file_handle.read()
                    file_handle.close()
                    
                    # Add to ZIP
                    zip_file.writestr(filename, content)
                    
                    # Clean up temporary file if exists
                    if hasattr(file_handle, 'name') and 'temp_' in file_handle.name:
                        try:
                            os.unlink(file_handle.name)
                        except:
                            pass
                            
                except Exception as e:
                    # Add error file to ZIP
                    error_content = f"Error downloading {file_path}: {str(e)}"
                    zip_file.writestr(f"ERROR_{file_path.replace('/', '_')}.txt", error_content)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type='application/zip',
            headers={"Content-Disposition": "attachment; filename=files.zip"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {str(e)}")

@router.get("/search")
async def search_files(
    query: str,
    path: str = "/",
    current_user: User = Depends(get_current_user)
):
    """Search for files and directories"""
    try:
        all_files = await file_manager.list_files(path, current_user.id)
        
        # Simple search in file names
        query_lower = query.lower()
        results = [
            file for file in all_files 
            if query_lower in file.name.lower()
        ]
        
        return {"results": [file.dict() for file in results], "count": len(results)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")

@router.get("/info/{file_path:path}")
async def get_file_info(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed file information"""
    try:
        files = await file_manager.list_files("/", current_user.id)
        
        # Find the specific file
        for file in files:
            if file.path == file_path:
                return file.dict()
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")