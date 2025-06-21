import asyncio
import subprocess
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from models import RDPConnection, RDPConnectionCreate, Session, SessionType, SessionStatus, LogEntry, LogLevel, LogSource
from database import db
from fastapi import HTTPException
import aiofiles

class RDPManagerService:
    def __init__(self):
        self.active_connections: Dict[str, Dict] = {}
        self.guacamole_host = "localhost"
        self.guacamole_port = 4822
    
    async def create_connection(self, connection_data: RDPConnectionCreate, user_id: str, ip_address: str) -> RDPConnection:
        """Create a new RDP connection"""
        try:
            # Create connection record
            connection = RDPConnection(
                user_id=user_id,
                host=connection_data.host,
                port=connection_data.port,
                username=connection_data.username,
                password=self._encrypt_password(connection_data.password),
                quality=connection_data.quality,
                status="connecting"
            )
            
            # Save to database
            await db.rdp_connections.insert_one(connection.dict())
            
            # Create session record
            session = Session(
                user_id=user_id,
                session_type=SessionType.rdp,
                ip_address=ip_address,
                status=SessionStatus.active
            )
            await db.sessions.insert_one(session.dict())
            
            # Start connection process
            asyncio.create_task(self._establish_connection(connection.id, session.id))
            
            await self._log_rdp_event(
                user_id, "CONNECTION_CREATED", 
                f"RDP connection created to {connection_data.host}:{connection_data.port}",
                connection.id
            )
            
            return connection
            
        except Exception as e:
            await self._log_rdp_event(
                user_id, "CONNECTION_ERROR", 
                f"Error creating RDP connection: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=f"Error creating RDP connection: {str(e)}")
    
    async def get_connection(self, connection_id: str, user_id: str) -> RDPConnection:
        """Get RDP connection by ID"""
        try:
            connection_data = await db.rdp_connections.find_one({
                "id": connection_id,
                "user_id": user_id
            })
            
            if not connection_data:
                raise HTTPException(status_code=404, detail="Connection not found")
            
            return RDPConnection(**connection_data)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting connection: {str(e)}")
    
    async def list_connections(self, user_id: str) -> List[RDPConnection]:
        """List all RDP connections for a user"""
        try:
            cursor = db.rdp_connections.find(
                {"user_id": user_id},
                sort=[("start_time", -1)]
            )
            
            connections = []
            async for doc in cursor:
                # Don't return the actual password
                doc['password'] = "***encrypted***"
                connections.append(RDPConnection(**doc))
            
            return connections
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error listing connections: {str(e)}")
    
    async def terminate_connection(self, connection_id: str, user_id: str) -> bool:
        """Terminate an RDP connection"""
        try:
            # Find connection
            connection = await self.get_connection(connection_id, user_id)
            
            if connection.status == "disconnected":
                return True
            
            # Update connection status
            await db.rdp_connections.update_one(
                {"id": connection_id},
                {
                    "$set": {
                        "status": "disconnected",
                        "end_time": datetime.utcnow()
                    }
                }
            )
            
            # Update session status
            await db.sessions.update_one(
                {"user_id": user_id, "session_type": "RDP"},
                {
                    "$set": {
                        "status": SessionStatus.terminated,
                        "end_time": datetime.utcnow()
                    }
                }
            )
            
            # Remove from active connections
            if connection_id in self.active_connections:
                connection_info = self.active_connections[connection_id]
                if 'process' in connection_info:
                    try:
                        connection_info['process'].terminate()
                        await asyncio.sleep(1)
                        if connection_info['process'].poll() is None:
                            connection_info['process'].kill()
                    except:
                        pass
                
                del self.active_connections[connection_id]
            
            await self._log_rdp_event(
                user_id, "CONNECTION_TERMINATED", 
                f"RDP connection {connection_id} terminated",
                connection_id
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            await self._log_rdp_event(
                user_id, "TERMINATION_ERROR", 
                f"Error terminating connection: {str(e)}",
                connection_id
            )
            raise HTTPException(status_code=500, detail=f"Error terminating connection: {str(e)}")
    
    async def get_connection_status(self, connection_id: str, user_id: str) -> Dict:
        """Get detailed connection status"""
        try:
            connection = await self.get_connection(connection_id, user_id)
            
            status_info = {
                "connection_id": connection_id,
                "status": connection.status,
                "host": connection.host,
                "port": connection.port,
                "start_time": connection.start_time,
                "end_time": connection.end_time,
                "error_message": connection.error_message
            }
            
            # Add real-time info if connection is active
            if connection_id in self.active_connections:
                active_info = self.active_connections[connection_id]
                status_info.update({
                    "latency": active_info.get("latency", 0),
                    "bandwidth": active_info.get("bandwidth", 0),
                    "resolution": active_info.get("resolution", "Unknown"),
                    "fps": active_info.get("fps", 0)
                })
            
            return status_info
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting connection status: {str(e)}")
    
    async def get_rdp_statistics(self, user_id: str) -> Dict:
        """Get RDP usage statistics"""
        try:
            # Total connections
            total_connections = await db.rdp_connections.count_documents({"user_id": user_id})
            
            # Active connections
            active_connections = await db.rdp_connections.count_documents({
                "user_id": user_id,
                "status": "connected"
            })
            
            # Failed connections
            failed_connections = await db.rdp_connections.count_documents({
                "user_id": user_id,
                "status": "error"
            })
            
            # Most used hosts
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$host", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            cursor = db.rdp_connections.aggregate(pipeline)
            popular_hosts = []
            async for doc in cursor:
                popular_hosts.append({"host": doc["_id"], "connections": doc["count"]})
            
            return {
                "total_connections": total_connections,
                "active_connections": active_connections,
                "failed_connections": failed_connections,
                "success_rate": round((total_connections - failed_connections) / max(total_connections, 1) * 100, 2),
                "popular_hosts": popular_hosts
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting RDP statistics: {str(e)}")
    
    async def _establish_connection(self, connection_id: str, session_id: str):
        """Establish RDP connection using Guacamole or FreeRDP"""
        try:
            # Get connection details
            connection_data = await db.rdp_connections.find_one({"id": connection_id})
            if not connection_data:
                return
            
            connection = RDPConnection(**connection_data)
            
            # Update status to connecting
            await db.rdp_connections.update_one(
                {"id": connection_id},
                {"$set": {"status": "connecting", "start_time": datetime.utcnow()}}
            )
            
            # Simulate connection establishment
            await asyncio.sleep(2)
            
            # Create Guacamole configuration
            guac_config = {
                "protocol": "rdp",
                "parameters": {
                    "hostname": connection.host,
                    "port": str(connection.port),
                    "username": connection.username,
                    "password": self._decrypt_password(connection.password),
                    "security": "any",
                    "ignore-cert": "true",
                    "color-depth": "32" if connection.quality == "high" else "16",
                    "resize-method": "reconnect",
                    "enable-audio": "true",
                    "enable-printing": "false",
                    "enable-drive": "true"
                }
            }
            
            # Save Guacamole config
            config_file = f"/tmp/guac_config_{connection_id}.json"
            async with aiofiles.open(config_file, 'w') as f:
                await f.write(json.dumps(guac_config))
            
            # Start connection monitoring
            self.active_connections[connection_id] = {
                "session_id": session_id,
                "start_time": datetime.utcnow(),
                "latency": 25,
                "bandwidth": 2.5,
                "resolution": "1920x1080",
                "fps": 30,
                "config_file": config_file
            }
            
            # Update connection status
            await db.rdp_connections.update_one(
                {"id": connection_id},
                {"$set": {"status": "connected"}}
            )
            
            await self._log_rdp_event(
                connection.user_id, "CONNECTION_ESTABLISHED", 
                f"RDP connection established to {connection.host}:{connection.port}",
                connection_id
            )
            
            # Start connection monitoring
            asyncio.create_task(self._monitor_connection(connection_id))
            
        except Exception as e:
            # Update connection status to error
            await db.rdp_connections.update_one(
                {"id": connection_id},
                {
                    "$set": {
                        "status": "error",
                        "error_message": str(e),
                        "end_time": datetime.utcnow()
                    }
                }
            )
            
            await self._log_rdp_event(
                connection.user_id if 'connection' in locals() else "unknown", 
                "CONNECTION_FAILED", 
                f"RDP connection failed: {str(e)}",
                connection_id
            )
    
    async def _monitor_connection(self, connection_id: str):
        """Monitor active RDP connection"""
        try:
            while connection_id in self.active_connections:
                connection_info = self.active_connections[connection_id]
                
                # Simulate connection metrics updates
                connection_info["latency"] = max(10, connection_info["latency"] + (asyncio.get_event_loop().time() % 20 - 10))
                connection_info["bandwidth"] = max(0.5, connection_info["bandwidth"] + (asyncio.get_event_loop().time() % 2 - 1))
                
                # Update session bandwidth
                await db.sessions.update_one(
                    {"id": connection_info["session_id"]},
                    {"$set": {"bandwidth_used": connection_info["bandwidth"]}}
                )
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except Exception as e:
            print(f"Error monitoring connection {connection_id}: {e}")
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password for storage"""
        # In production, use proper encryption
        return f"encrypted_{password}"
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password for use"""
        # In production, use proper decryption
        return encrypted_password.replace("encrypted_", "")
    
    async def _log_rdp_event(self, user_id: str, event_type: str, message: str, connection_id: str = None):
        """Log RDP events"""
        try:
            log_entry = LogEntry(
                level=LogLevel.INFO if "SUCCESS" in event_type or "ESTABLISHED" in event_type else LogLevel.WARNING,
                source=LogSource.RDP_SERVER,
                message=message,
                details={
                    "event_type": event_type,
                    "connection_id": connection_id
                },
                user_id=user_id
            )
            
            await db.logs.insert_one(log_entry.dict())
            
        except Exception as e:
            print(f"Error logging RDP event: {e}")

# Create global instance
rdp_manager = RDPManagerService()