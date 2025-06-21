from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from models import User, LogEntry, LogLevel, LogSource, LogQuery, SuccessResponse
from auth import get_current_user
from database import db

router = APIRouter(prefix="/logs", tags=["Logging"])

@router.get("/", response_model=List[LogEntry])
async def get_logs(
    level: Optional[LogLevel] = None,
    source: Optional[LogSource] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search_term: Optional[str] = None,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get logs with filtering options"""
    try:
        # Build query
        query = {}
        
        if level:
            query["level"] = level
        
        if source:
            query["source"] = source
        
        if start_date or end_date:
            timestamp_query = {}
            if start_date:
                timestamp_query["$gte"] = start_date
            if end_date:
                timestamp_query["$lte"] = end_date
            query["timestamp"] = timestamp_query
        
        if search_term:
            query["$or"] = [
                {"message": {"$regex": search_term, "$options": "i"}},
                {"source": {"$regex": search_term, "$options": "i"}}
            ]
        
        # Execute query
        cursor = db.logs.find(
            query,
            sort=[("timestamp", -1)],
            limit=limit
        )
        
        logs = []
        async for doc in cursor:
            logs.append(LogEntry(**doc))
        
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

@router.get("/levels")
async def get_log_levels(current_user: User = Depends(get_current_user)):
    """Get available log levels with counts"""
    try:
        pipeline = [
            {"$group": {"_id": "$level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        cursor = db.logs.aggregate(pipeline)
        levels = {}
        async for doc in cursor:
            levels[doc["_id"]] = doc["count"]
        
        return {"levels": levels}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting log levels: {str(e)}")

@router.get("/sources")
async def get_log_sources(current_user: User = Depends(get_current_user)):
    """Get available log sources with counts"""
    try:
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        cursor = db.logs.aggregate(pipeline)
        sources = {}
        async for doc in cursor:
            sources[doc["_id"]] = doc["count"]
        
        return {"sources": sources}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting log sources: {str(e)}")

@router.get("/statistics")
async def get_log_statistics(
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """Get log statistics for the specified number of days"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total logs in date range
        total_logs = await db.logs.count_documents({
            "timestamp": {"$gte": start_date, "$lte": end_date}
        })
        
        # Logs by level
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": "$level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        cursor = db.logs.aggregate(pipeline)
        logs_by_level = {}
        async for doc in cursor:
            logs_by_level[doc["_id"]] = doc["count"]
        
        # Logs by source
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        cursor = db.logs.aggregate(pipeline)
        logs_by_source = {}
        async for doc in cursor:
            logs_by_source[doc["_id"]] = doc["count"]
        
        # Logs by day
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        cursor = db.logs.aggregate(pipeline)
        logs_by_day = {}
        async for doc in cursor:
            logs_by_day[doc["_id"]] = doc["count"]
        
        # Error rate
        error_logs = logs_by_level.get("ERROR", 0) + logs_by_level.get("CRITICAL", 0)
        error_rate = round((error_logs / max(total_logs, 1)) * 100, 2)
        
        return {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "total_logs": total_logs,
            "logs_by_level": logs_by_level,
            "logs_by_source": logs_by_source,
            "logs_by_day": logs_by_day,
            "error_rate_percent": error_rate
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting log statistics: {str(e)}")

@router.delete("/clear", response_model=SuccessResponse)
async def clear_logs(
    older_than_days: int = 0,
    level: Optional[LogLevel] = None,
    source: Optional[LogSource] = None,
    current_user: User = Depends(get_current_user)
):
    """Clear logs with optional filtering"""
    try:
        # Build delete query
        query = {}
        
        if older_than_days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            query["timestamp"] = {"$lt": cutoff_date}
        
        if level:
            query["level"] = level
        
        if source:
            query["source"] = source
        
        # Execute delete
        result = await db.logs.delete_many(query)
        
        # Log the clearing action
        log_entry = LogEntry(
            level=LogLevel.INFO,
            source=LogSource.SYSTEM,
            message=f"Logs cleared by {current_user.username}. Deleted {result.deleted_count} entries.",
            details={
                "cleared_by": current_user.id,
                "deleted_count": result.deleted_count,
                "filter": query
            },
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(
            message=f"Successfully cleared {result.deleted_count} log entries"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing logs: {str(e)}")

@router.get("/export")
async def export_logs(
    format: str = "json",  # json, csv
    level: Optional[LogLevel] = None,
    source: Optional[LogSource] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(1000, le=10000),
    current_user: User = Depends(get_current_user)
):
    """Export logs in specified format"""
    try:
        # Build query (same as get_logs)
        query = {}
        
        if level:
            query["level"] = level
        
        if source:
            query["source"] = source
        
        if start_date or end_date:
            timestamp_query = {}
            if start_date:
                timestamp_query["$gte"] = start_date
            if end_date:
                timestamp_query["$lte"] = end_date
            query["timestamp"] = timestamp_query
        
        # Get logs
        cursor = db.logs.find(
            query,
            sort=[("timestamp", -1)],
            limit=limit
        )
        
        logs = []
        async for doc in cursor:
            log_entry = LogEntry(**doc)
            logs.append(log_entry.dict())
        
        if format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            if logs:
                writer.writerow(logs[0].keys())
                
                # Write data
                for log in logs:
                    # Convert complex fields to strings
                    row = []
                    for value in log.values():
                        if isinstance(value, dict):
                            row.append(str(value))
                        elif isinstance(value, datetime):
                            row.append(value.isoformat())
                        else:
                            row.append(str(value) if value is not None else "")
                    writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=logs.csv"}
            )
        
        else:  # JSON format
            import json
            from fastapi.responses import Response
            
            # Convert datetime objects to strings for JSON serialization
            for log in logs:
                if 'timestamp' in log and isinstance(log['timestamp'], datetime):
                    log['timestamp'] = log['timestamp'].isoformat()
            
            json_content = json.dumps(logs, indent=2, default=str)
            
            return Response(
                content=json_content,
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=logs.json"}
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting logs: {str(e)}")

@router.get("/realtime")
async def get_realtime_logs(
    since: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get logs since the specified timestamp for real-time updates"""
    try:
        # If no timestamp provided, get logs from last 5 minutes
        if not since:
            since = datetime.utcnow() - timedelta(minutes=5)
        
        cursor = db.logs.find(
            {"timestamp": {"$gte": since}},
            sort=[("timestamp", 1)]
        )
        
        logs = []
        async for doc in cursor:
            logs.append(LogEntry(**doc).dict())
        
        return {
            "logs": logs,
            "since": since.isoformat(),
            "count": len(logs),
            "last_update": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting realtime logs: {str(e)}")

@router.post("/add", response_model=SuccessResponse)
async def add_log_entry(
    level: LogLevel,
    source: LogSource,
    message: str,
    details: Optional[dict] = None,
    current_user: User = Depends(get_current_user)
):
    """Add a custom log entry"""
    try:
        log_entry = LogEntry(
            level=level,
            source=source,
            message=message,
            details=details,
            user_id=current_user.id
        )
        
        await db.logs.insert_one(log_entry.dict())
        
        return SuccessResponse(message="Log entry added successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding log entry: {str(e)}")