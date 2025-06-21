from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models import User, DashboardStats, SystemMetrics, Session
from auth import get_current_user
from services.system_monitor import system_monitor
from database import db
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics"""
    try:
        # Get active sessions count
        active_sessions = await db.sessions.count_documents({"status": "active"})
        
        # Get today's connections
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        total_connections_today = await db.sessions.count_documents({
            "start_time": {"$gte": today_start}
        })
        
        # Get latest system metrics
        latest_metrics = await db.system_metrics.find_one(
            {},
            sort=[("timestamp", -1)]
        )
        
        if latest_metrics:
            metrics = SystemMetrics(**latest_metrics)
            cpu_usage = metrics.cpu_usage
            memory_usage = (metrics.memory_used / metrics.memory_total) * 100
            disk_usage = (metrics.disk_used / metrics.disk_total) * 100
        else:
            # Get current metrics if no stored metrics
            current_metrics = await system_monitor.get_current_metrics()
            cpu_usage = current_metrics.cpu_usage
            memory_usage = (current_metrics.memory_used / current_metrics.memory_total) * 100
            disk_usage = (current_metrics.disk_used / current_metrics.disk_total) * 100
        
        # Calculate uptime
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_delta = datetime.utcnow() - boot_time
        uptime_str = f"{uptime_delta.days}d {uptime_delta.seconds // 3600}h {(uptime_delta.seconds % 3600) // 60}m"
        
        # Network status
        network_status = "connected" if active_sessions > 0 else "idle"
        
        # Security alerts (count warning/error logs from last 24h)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        security_alerts = await db.logs.count_documents({
            "timestamp": {"$gte": yesterday},
            "level": {"$in": ["WARNING", "ERROR", "CRITICAL"]},
            "source": "AUTH_SERVICE"
        })
        
        return DashboardStats(
            active_sessions=active_sessions,
            total_connections_today=total_connections_today,
            system_uptime=uptime_str,
            disk_usage_percent=round(disk_usage, 1),
            memory_usage_percent=round(memory_usage, 1),
            cpu_usage_percent=round(cpu_usage, 1),
            network_status=network_status,
            security_alerts=security_alerts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard stats: {str(e)}")

@router.get("/metrics/current", response_model=SystemMetrics)
async def get_current_metrics(current_user: User = Depends(get_current_user)):
    """Get current system metrics"""
    try:
        metrics = await system_monitor.get_current_metrics()
        # Store metrics for future reference
        await system_monitor.store_metrics(metrics)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting current metrics: {str(e)}")

@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """Get metrics history for specified hours"""
    try:
        metrics = await system_monitor.get_metrics_history(hours)
        return {"metrics": [metric.dict() for metric in metrics]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics history: {str(e)}")

@router.get("/sessions/active")
async def get_active_sessions(current_user: User = Depends(get_current_user)):
    """Get active sessions"""
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
            session_dict = session.dict()
            session_dict["duration_seconds"] = int(duration_seconds)
            sessions.append(session_dict)
        
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting active sessions: {str(e)}")

@router.get("/health")
async def get_system_health(current_user: User = Depends(get_current_user)):
    """Get system health status"""
    try:
        health = await system_monitor.check_system_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system health: {str(e)}")

@router.get("/system-info")
async def get_system_info(current_user: User = Depends(get_current_user)):
    """Get system information"""
    try:
        info = await system_monitor.get_system_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system info: {str(e)}")

@router.get("/processes")
async def get_top_processes(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get top processes by CPU usage"""
    try:
        processes = await system_monitor.get_running_processes(limit)
        return {"processes": processes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting processes: {str(e)}")

@router.post("/monitoring/start")
async def start_monitoring(current_user: User = Depends(get_current_user)):
    """Start system monitoring"""
    try:
        await system_monitor.start_monitoring()
        return {"message": "System monitoring started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_user)):
    """Stop system monitoring"""
    try:
        await system_monitor.stop_monitoring()
        return {"message": "System monitoring stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping monitoring: {str(e)}")