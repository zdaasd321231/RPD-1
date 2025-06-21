from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from models import User, RDPConnection, RDPConnectionCreate, SuccessResponse
from auth import get_current_user
from services.rdp_manager import rdp_manager

router = APIRouter(prefix="/rdp", tags=["RDP Management"])

@router.post("/connections", response_model=RDPConnection)
async def create_rdp_connection(
    connection_data: RDPConnectionCreate,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Create a new RDP connection"""
    # Get client IP
    client_ip = request.client.host
    if hasattr(request, 'headers') and 'x-forwarded-for' in request.headers:
        client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()
    
    return await rdp_manager.create_connection(connection_data, current_user.id, client_ip)

@router.get("/connections", response_model=List[RDPConnection])
async def list_rdp_connections(current_user: User = Depends(get_current_user)):
    """List all RDP connections for the current user"""
    return await rdp_manager.list_connections(current_user.id)

@router.get("/connections/{connection_id}", response_model=RDPConnection)
async def get_rdp_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get RDP connection details"""
    return await rdp_manager.get_connection(connection_id, current_user.id)

@router.delete("/connections/{connection_id}", response_model=SuccessResponse)
async def terminate_rdp_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """Terminate an RDP connection"""
    success = await rdp_manager.terminate_connection(connection_id, current_user.id)
    
    if success:
        return SuccessResponse(message="RDP connection terminated successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to terminate connection")

@router.get("/connections/{connection_id}/status")
async def get_connection_status(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed connection status"""
    return await rdp_manager.get_connection_status(connection_id, current_user.id)

@router.get("/statistics")
async def get_rdp_statistics(current_user: User = Depends(get_current_user)):
    """Get RDP usage statistics"""
    return await rdp_manager.get_rdp_statistics(current_user.id)

@router.post("/connections/{connection_id}/screenshot")
async def take_screenshot(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """Take a screenshot of the RDP session"""
    try:
        # Verify connection exists and belongs to user
        connection = await rdp_manager.get_connection(connection_id, current_user.id)
        
        if connection.status != "connected":
            raise HTTPException(status_code=400, detail="Connection is not active")
        
        # In a real implementation, this would capture the actual RDP screen
        # For now, return a placeholder response
        return {
            "message": "Screenshot taken successfully",
            "connection_id": connection_id,
            "timestamp": "2024-01-01T00:00:00Z",
            "format": "png",
            "size": "1920x1080"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error taking screenshot: {str(e)}")

@router.post("/connections/{connection_id}/send-keys")
async def send_key_combination(
    connection_id: str,
    keys: str,  # e.g., "ctrl+alt+del", "alt+tab"
    current_user: User = Depends(get_current_user)
):
    """Send key combination to RDP session"""
    try:
        # Verify connection exists and belongs to user
        connection = await rdp_manager.get_connection(connection_id, current_user.id)
        
        if connection.status != "connected":
            raise HTTPException(status_code=400, detail="Connection is not active")
        
        # In a real implementation, this would send keys to the RDP session
        valid_combinations = [
            "ctrl+alt+del", "alt+tab", "alt+f4", "win+r", "win+l",
            "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z", "ctrl+s"
        ]
        
        if keys.lower() not in valid_combinations:
            raise HTTPException(status_code=400, detail="Invalid key combination")
        
        return {
            "message": f"Key combination '{keys}' sent successfully",
            "connection_id": connection_id,
            "keys": keys
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending keys: {str(e)}")

@router.post("/connections/{connection_id}/clipboard")
async def set_clipboard_content(
    connection_id: str,
    content: str,
    current_user: User = Depends(get_current_user)
):
    """Set clipboard content in RDP session"""
    try:
        # Verify connection exists and belongs to user
        connection = await rdp_manager.get_connection(connection_id, current_user.id)
        
        if connection.status != "connected":
            raise HTTPException(status_code=400, detail="Connection is not active")
        
        # Limit clipboard content size
        if len(content) > 10000:  # 10KB limit
            raise HTTPException(status_code=400, detail="Clipboard content too large")
        
        # In a real implementation, this would set the clipboard in the RDP session
        return {
            "message": "Clipboard content set successfully",
            "connection_id": connection_id,
            "content_length": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting clipboard: {str(e)}")

@router.get("/connections/{connection_id}/clipboard")
async def get_clipboard_content(
    connection_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get clipboard content from RDP session"""
    try:
        # Verify connection exists and belongs to user
        connection = await rdp_manager.get_connection(connection_id, current_user.id)
        
        if connection.status != "connected":
            raise HTTPException(status_code=400, detail="Connection is not active")
        
        # In a real implementation, this would get the clipboard from the RDP session
        return {
            "content": "",  # Placeholder
            "content_type": "text/plain",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting clipboard: {str(e)}")

@router.post("/connections/{connection_id}/resize")
async def resize_rdp_session(
    connection_id: str,
    width: int,
    height: int,
    current_user: User = Depends(get_current_user)
):
    """Resize RDP session display"""
    try:
        # Verify connection exists and belongs to user
        connection = await rdp_manager.get_connection(connection_id, current_user.id)
        
        if connection.status != "connected":
            raise HTTPException(status_code=400, detail="Connection is not active")
        
        # Validate resolution
        if width < 800 or height < 600 or width > 4096 or height > 2160:
            raise HTTPException(status_code=400, detail="Invalid resolution")
        
        # In a real implementation, this would resize the RDP session
        return {
            "message": "RDP session resized successfully",
            "connection_id": connection_id,
            "resolution": f"{width}x{height}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resizing session: {str(e)}")

@router.get("/active-connections")
async def get_active_connections(current_user: User = Depends(get_current_user)):
    """Get all active RDP connections for monitoring"""
    try:
        # Get active connections from rdp_manager
        active_connections = []
        
        for conn_id, conn_info in rdp_manager.active_connections.items():
            # Get connection details from database
            connection = await rdp_manager.get_connection(conn_id, current_user.id)
            
            if connection:
                active_connections.append({
                    "connection_id": conn_id,
                    "host": connection.host,
                    "port": connection.port,
                    "start_time": conn_info["start_time"].isoformat(),
                    "latency": conn_info.get("latency", 0),
                    "bandwidth": conn_info.get("bandwidth", 0),
                    "resolution": conn_info.get("resolution", "Unknown"),
                    "fps": conn_info.get("fps", 0)
                })
        
        return {"active_connections": active_connections}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting active connections: {str(e)}")