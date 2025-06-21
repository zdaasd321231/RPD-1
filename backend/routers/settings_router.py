from fastapi import APIRouter, Depends, HTTPException
from models import User, AppSettings, SecuritySettings, RDPSettings, FileSettings, NotificationSettings, SystemSettings, SuccessResponse
from auth import get_current_user
from database import db
from datetime import datetime

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=AppSettings)
async def get_settings(current_user: User = Depends(get_current_user)):
    """Get current application settings"""
    try:
        settings_data = await db.settings.find_one({})
        
        if not settings_data:
            # Create default settings if none exist
            default_settings = AppSettings(
                notifications=NotificationSettings(
                    notification_email=current_user.email
                ),
                updated_by=current_user.id
            )
            
            await db.settings.insert_one(default_settings.dict())
            return default_settings
        
        return AppSettings(**settings_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")

@router.put("/", response_model=SuccessResponse)
async def update_settings(
    settings: AppSettings,
    current_user: User = Depends(get_current_user)
):
    """Update application settings"""
    try:
        # Update metadata
        settings.updated_at = datetime.utcnow()
        settings.updated_by = current_user.id
        
        # Update or insert settings
        await db.settings.replace_one(
            {},
            settings.dict(),
            upsert=True
        )
        
        # Log the settings update
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.INFO,
            source=LogSource.SYSTEM,
            message=f"Application settings updated by {current_user.username}",
            details={"updated_by": current_user.id},
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message="Settings updated successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")

@router.get("/security", response_model=SecuritySettings)
async def get_security_settings(current_user: User = Depends(get_current_user)):
    """Get security settings"""
    try:
        settings = await get_settings(current_user)
        return settings.security
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting security settings: {str(e)}")

@router.put("/security", response_model=SuccessResponse)
async def update_security_settings(
    security_settings: SecuritySettings,
    current_user: User = Depends(get_current_user)
):
    """Update security settings"""
    try:
        # Get current settings
        current_settings = await get_settings(current_user)
        
        # Update security section
        current_settings.security = security_settings
        current_settings.updated_at = datetime.utcnow()
        current_settings.updated_by = current_user.id
        
        # Save to database
        await db.settings.replace_one(
            {},
            current_settings.dict(),
            upsert=True
        )
        
        # Log the security update
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.WARNING,
            source=LogSource.AUTH_SERVICE,
            message=f"Security settings updated by {current_user.username}",
            details={
                "updated_by": current_user.id,
                "changes": security_settings.dict()
            },
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message="Security settings updated successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating security settings: {str(e)}")

@router.get("/rdp", response_model=RDPSettings)
async def get_rdp_settings(current_user: User = Depends(get_current_user)):
    """Get RDP settings"""
    try:
        settings = await get_settings(current_user)
        return settings.rdp
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting RDP settings: {str(e)}")

@router.put("/rdp", response_model=SuccessResponse)
async def update_rdp_settings(
    rdp_settings: RDPSettings,
    current_user: User = Depends(get_current_user)
):
    """Update RDP settings"""
    try:
        # Get current settings
        current_settings = await get_settings(current_user)
        
        # Update RDP section
        current_settings.rdp = rdp_settings
        current_settings.updated_at = datetime.utcnow()
        current_settings.updated_by = current_user.id
        
        # Save to database
        await db.settings.replace_one(
            {},
            current_settings.dict(),
            upsert=True
        )
        
        # Log the RDP settings update
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.INFO,
            source=LogSource.RDP_SERVER,
            message=f"RDP settings updated by {current_user.username}",
            details={
                "updated_by": current_user.id,
                "changes": rdp_settings.dict()
            },
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message="RDP settings updated successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating RDP settings: {str(e)}")

@router.get("/files", response_model=FileSettings)
async def get_file_settings(current_user: User = Depends(get_current_user)):
    """Get file management settings"""
    try:
        settings = await get_settings(current_user)
        return settings.files
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file settings: {str(e)}")

@router.put("/files", response_model=SuccessResponse)
async def update_file_settings(
    file_settings: FileSettings,
    current_user: User = Depends(get_current_user)
):
    """Update file management settings"""
    try:
        # Get current settings
        current_settings = await get_settings(current_user)
        
        # Update files section
        current_settings.files = file_settings
        current_settings.updated_at = datetime.utcnow()
        current_settings.updated_by = current_user.id
        
        # Save to database
        await db.settings.replace_one(
            {},
            current_settings.dict(),
            upsert=True
        )
        
        # Log the file settings update
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.INFO,
            source=LogSource.FILE_MANAGER,
            message=f"File settings updated by {current_user.username}",
            details={
                "updated_by": current_user.id,
                "changes": file_settings.dict()
            },
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message="File settings updated successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating file settings: {str(e)}")

@router.get("/notifications", response_model=NotificationSettings)
async def get_notification_settings(current_user: User = Depends(get_current_user)):
    """Get notification settings"""
    try:
        settings = await get_settings(current_user)
        return settings.notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notification settings: {str(e)}")

@router.put("/notifications", response_model=SuccessResponse)
async def update_notification_settings(
    notification_settings: NotificationSettings,
    current_user: User = Depends(get_current_user)
):
    """Update notification settings"""
    try:
        # Get current settings
        current_settings = await get_settings(current_user)
        
        # Update notifications section
        current_settings.notifications = notification_settings
        current_settings.updated_at = datetime.utcnow()
        current_settings.updated_by = current_user.id
        
        # Save to database
        await db.settings.replace_one(
            {},
            current_settings.dict(),
            upsert=True
        )
        
        return SuccessResponse(message="Notification settings updated successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating notification settings: {str(e)}")

@router.get("/system", response_model=SystemSettings)
async def get_system_settings(current_user: User = Depends(get_current_user)):
    """Get system settings"""
    try:
        settings = await get_settings(current_user)
        return settings.system
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system settings: {str(e)}")

@router.put("/system", response_model=SuccessResponse)
async def update_system_settings(
    system_settings: SystemSettings,
    current_user: User = Depends(get_current_user)
):
    """Update system settings"""
    try:
        # Get current settings
        current_settings = await get_settings(current_user)
        
        # Update system section
        current_settings.system = system_settings
        current_settings.updated_at = datetime.utcnow()
        current_settings.updated_by = current_user.id
        
        # Save to database
        await db.settings.replace_one(
            {},
            current_settings.dict(),
            upsert=True
        )
        
        # Log the system settings update
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.INFO,
            source=LogSource.SYSTEM,
            message=f"System settings updated by {current_user.username}",
            details={
                "updated_by": current_user.id,
                "changes": system_settings.dict()
            },
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message="System settings updated successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating system settings: {str(e)}")

@router.post("/reset", response_model=SuccessResponse)
async def reset_settings(current_user: User = Depends(get_current_user)):
    """Reset all settings to defaults"""
    try:
        # Create default settings
        default_settings = AppSettings(
            notifications=NotificationSettings(
                notification_email=current_user.email
            ),
            updated_by=current_user.id
        )
        
        # Replace current settings
        await db.settings.replace_one(
            {},
            default_settings.dict(),
            upsert=True
        )
        
        # Log the reset
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.WARNING,
            source=LogSource.SYSTEM,
            message=f"All settings reset to defaults by {current_user.username}",
            details={"reset_by": current_user.id},
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message="Settings reset to defaults successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting settings: {str(e)}")

@router.get("/backup")
async def backup_settings(current_user: User = Depends(get_current_user)):
    """Backup current settings"""
    try:
        settings = await get_settings(current_user)
        
        # Create backup with timestamp
        backup_data = {
            "backup_timestamp": datetime.utcnow().isoformat(),
            "backup_by": current_user.username,
            "settings": settings.dict()
        }
        
        import json
        from fastapi.responses import Response
        
        json_content = json.dumps(backup_data, indent=2, default=str)
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=rdp_stealth_settings_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error backing up settings: {str(e)}")

@router.post("/restore", response_model=SuccessResponse)
async def restore_settings(
    settings_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Restore settings from backup"""
    try:
        # Validate backup data
        if "settings" not in settings_data:
            raise HTTPException(status_code=400, detail="Invalid backup data")
        
        # Create AppSettings from backup
        restored_settings = AppSettings(**settings_data["settings"])
        
        # Update metadata
        restored_settings.updated_at = datetime.utcnow()
        restored_settings.updated_by = current_user.id
        
        # Save to database
        await db.settings.replace_one(
            {},
            restored_settings.dict(),
            upsert=True
        )
        
        # Log the restore
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.WARNING,
            source=LogSource.SYSTEM,
            message=f"Settings restored from backup by {current_user.username}",
            details={
                "restored_by": current_user.id,
                "backup_timestamp": settings_data.get("backup_timestamp"),
                "original_backup_by": settings_data.get("backup_by")
            },
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message="Settings restored from backup successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restoring settings: {str(e)}")