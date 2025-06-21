from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from models import User, Session, SessionStatus, SuccessResponse
from auth import get_current_user
from database import db

router = APIRouter(prefix="/sessions", tags=["Session Management"])

@router.get("/active")
async def get_active_sessions(current_user: User = Depends(get_current_user)):
    """Get all active sessions"""
    try:
        cursor = db.sessions.find(
            {"status": "active"},
            sort=[("start_time", -1)]
        )
        
        sessions = []
        async for doc in cursor:
            session = Session(**doc)
            
            # Calculate duration
            duration_seconds = (datetime.utcnow() - session.start_time).total_seconds()
            duration_minutes = int(duration_seconds / 60)
            duration_hours = int(duration_minutes / 60)
            
            if duration_hours > 0:
                duration_str = f"{duration_hours}h {duration_minutes % 60}m"
            else:
                duration_str = f"{duration_minutes}m"
            
            # Add geolocation info (mock data for now)
            country = session.country or "Unknown"
            city = session.city or "Unknown"
            
            session_data = {
                **session.dict(),
                "duration_seconds": int(duration_seconds),
                "duration_string": duration_str,
                "location": f"{city}, {country}"
            }
            
            sessions.append(session_data)
        
        return {"sessions": sessions, "count": len(sessions)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting active sessions: {str(e)}")

@router.get("/history")
async def get_session_history(
    limit: int = 100,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get session history"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        cursor = db.sessions.find(
            {
                "start_time": {"$gte": start_date, "$lte": end_date},
                "status": {"$ne": "active"}
            },
            sort=[("start_time", -1)],
            limit=limit
        )
        
        sessions = []
        async for doc in cursor:
            session = Session(**doc)
            
            # Calculate duration
            end_time = session.end_time or datetime.utcnow()
            duration_seconds = (end_time - session.start_time).total_seconds()
            
            # Format duration
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            session_data = {
                **session.dict(),
                "duration_seconds": int(duration_seconds),
                "duration_string": duration_str,
                "location": f"{session.city or 'Unknown'}, {session.country or 'Unknown'}"
            }
            
            sessions.append(session_data)
        
        return {"sessions": sessions, "count": len(sessions)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session history: {str(e)}")

@router.delete("/terminate/{session_id}", response_model=SuccessResponse)
async def terminate_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Terminate an active session"""
    try:
        # Find the session
        session_data = await db.sessions.find_one({"id": session_id})
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = Session(**session_data)
        
        if session.status != SessionStatus.active:
            raise HTTPException(status_code=400, detail="Session is not active")
        
        # Update session status
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "status": SessionStatus.terminated,
                    "end_time": datetime.utcnow()
                }
            }
        )
        
        # If it's an RDP session, also terminate the RDP connection
        if session.session_type == "RDP":
            # Find and terminate related RDP connection
            rdp_connection = await db.rdp_connections.find_one({
                "user_id": session.user_id,
                "status": "connected"
            })
            
            if rdp_connection:
                await db.rdp_connections.update_one(
                    {"id": rdp_connection["id"]},
                    {
                        "$set": {
                            "status": "disconnected",
                            "end_time": datetime.utcnow()
                        }
                    }
                )
        
        return SuccessResponse(message="Session terminated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error terminating session: {str(e)}")

@router.post("/block-ip", response_model=SuccessResponse)
async def block_ip_address(
    ip_address: str,
    current_user: User = Depends(get_current_user)
):
    """Block an IP address"""
    try:
        # Terminate all active sessions from this IP
        await db.sessions.update_many(
            {"ip_address": ip_address, "status": "active"},
            {
                "$set": {
                    "status": SessionStatus.terminated,
                    "end_time": datetime.utcnow()
                }
            }
        )
        
        # Add IP to blocked list (you would implement this in your firewall/security system)
        # For now, we'll just log it
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.WARNING,
            source=LogSource.AUTH_SERVICE,
            message=f"IP address {ip_address} blocked by {current_user.username}",
            details={"blocked_ip": ip_address, "blocked_by": current_user.id},
            user_id=current_user.id,
            ip_address=ip_address
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message=f"IP address {ip_address} blocked successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error blocking IP: {str(e)}")

@router.get("/statistics")
async def get_session_statistics(current_user: User = Depends(get_current_user)):
    """Get session statistics"""
    try:
        # Total sessions
        total_sessions = await db.sessions.count_documents({})
        
        # Active sessions
        active_sessions = await db.sessions.count_documents({"status": "active"})
        
        # Sessions today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        sessions_today = await db.sessions.count_documents({
            "start_time": {"$gte": today_start}
        })
        
        # Sessions by type
        pipeline = [
            {"$group": {"_id": "$session_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        cursor = db.sessions.aggregate(pipeline)
        sessions_by_type = {}
        async for doc in cursor:
            sessions_by_type[doc["_id"]] = doc["count"]
        
        # Top IPs
        pipeline = [
            {"$group": {"_id": "$ip_address", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        cursor = db.sessions.aggregate(pipeline)
        top_ips = []
        async for doc in cursor:
            top_ips.append({"ip": doc["_id"], "sessions": doc["count"]})
        
        # Average session duration (for completed sessions)
        pipeline = [
            {"$match": {"end_time": {"$exists": True}}},
            {
                "$addFields": {
                    "duration": {
                        "$subtract": ["$end_time", "$start_time"]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_duration": {"$avg": "$duration"}
                }
            }
        ]
        
        cursor = db.sessions.aggregate(pipeline)
        avg_duration_ms = 0
        async for doc in cursor:
            avg_duration_ms = doc.get("avg_duration", 0)
        
        avg_duration_minutes = int(avg_duration_ms / 1000 / 60) if avg_duration_ms else 0
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "sessions_today": sessions_today,
            "sessions_by_type": sessions_by_type,
            "top_ips": top_ips,
            "average_duration_minutes": avg_duration_minutes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session statistics: {str(e)}")

@router.get("/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific session"""
    try:
        session_data = await db.sessions.find_one({"id": session_id})
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = Session(**session_data)
        
        # Calculate duration
        end_time = session.end_time or datetime.utcnow()
        duration_seconds = (end_time - session.start_time).total_seconds()
        
        # Get user info
        user_data = await db.users.find_one({"id": session.user_id})
        user_info = {"username": user_data.get("username", "Unknown")} if user_data else {"username": "Unknown"}
        
        # Additional session details
        session_details = {
            **session.dict(),
            "duration_seconds": int(duration_seconds),
            "user_info": user_info,
            "is_active": session.status == SessionStatus.active
        }
        
        return session_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session details: {str(e)}")

@router.get("/by-ip/{ip_address}")
async def get_sessions_by_ip(
    ip_address: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get all sessions from a specific IP address"""
    try:
        cursor = db.sessions.find(
            {"ip_address": ip_address},
            sort=[("start_time", -1)],
            limit=limit
        )
        
        sessions = []
        async for doc in cursor:
            session = Session(**doc)
            
            # Calculate duration if session has ended
            if session.end_time:
                duration_seconds = (session.end_time - session.start_time).total_seconds()
            else:
                duration_seconds = (datetime.utcnow() - session.start_time).total_seconds()
            
            session_data = {
                **session.dict(),
                "duration_seconds": int(duration_seconds)
            }
            
            sessions.append(session_data)
        
        return {
            "ip_address": ip_address,
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sessions by IP: {str(e)}")