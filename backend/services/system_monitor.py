import psutil
import asyncio
import platform
from datetime import datetime, timedelta
from typing import Dict, Any
from models import SystemMetrics, LogEntry, LogLevel, LogSource
from database import db

class SystemMonitorService:
    def __init__(self):
        self.monitoring = False
        self.monitor_task = None
    
    async def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # CPU temperature (Linux only)
            cpu_temp = None
            try:
                if platform.system() == "Linux":
                    temps = psutil.sensors_temperatures()
                    if 'coretemp' in temps:
                        cpu_temp = temps['coretemp'][0].current
            except:
                pass
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_total_mb = round(memory.total / (1024 * 1024))
            memory_used_mb = round(memory.used / (1024 * 1024))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_total_gb = round(disk.total / (1024 * 1024 * 1024))
            disk_used_gb = round(disk.used / (1024 * 1024 * 1024))
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Get previous network stats to calculate speed
            previous_stats = await self.get_previous_network_stats()
            
            upload_speed = 0
            download_speed = 0
            
            if previous_stats:
                time_diff = (datetime.utcnow() - previous_stats['timestamp']).total_seconds()
                if time_diff > 0:
                    upload_speed = (network.bytes_sent - previous_stats['bytes_sent']) / time_diff / 1024  # KB/s
                    download_speed = (network.bytes_recv - previous_stats['bytes_recv']) / time_diff / 1024  # KB/s
            
            # Store current network stats for next calculation
            await self.store_network_stats(network.bytes_sent, network.bytes_recv)
            
            # Active connections
            active_sessions = await db.sessions.count_documents({"status": "active"})
            
            metrics = SystemMetrics(
                cpu_usage=cpu_percent,
                cpu_temperature=cpu_temp,
                memory_total=memory_total_mb,
                memory_used=memory_used_mb,
                disk_total=disk_total_gb,
                disk_used=disk_used_gb,
                network_upload_speed=max(0, upload_speed),
                network_download_speed=max(0, download_speed),
                network_total_sent=round(network.bytes_sent / (1024 * 1024 * 1024), 2),  # GB
                network_total_received=round(network.bytes_recv / (1024 * 1024 * 1024), 2),  # GB
                active_connections=active_sessions
            )
            
            return metrics
            
        except Exception as e:
            await self.log_error(f"Error getting system metrics: {str(e)}")
            raise
    
    async def get_previous_network_stats(self) -> Dict[str, Any]:
        """Get previous network statistics for speed calculation"""
        try:
            # Get the last network stats from a temporary collection or cache
            result = await db.system_metrics.find_one(
                {},
                sort=[("timestamp", -1)]
            )
            
            if result:
                return {
                    'timestamp': result['timestamp'],
                    'bytes_sent': result.get('_network_bytes_sent', 0),
                    'bytes_recv': result.get('_network_bytes_recv', 0)
                }
            
            return None
        except:
            return None
    
    async def store_network_stats(self, bytes_sent: int, bytes_recv: int):
        """Store current network stats for next speed calculation"""
        try:
            # Store in the latest metrics document
            await db.system_metrics.update_one(
                {},
                {
                    "$set": {
                        "_network_bytes_sent": bytes_sent,
                        "_network_bytes_recv": bytes_recv,
                        "_network_timestamp": datetime.utcnow()
                    }
                },
                upsert=True
            )
        except:
            pass
    
    async def store_metrics(self, metrics: SystemMetrics):
        """Store metrics in database"""
        try:
            await db.system_metrics.insert_one(metrics.dict())
        except Exception as e:
            await self.log_error(f"Error storing system metrics: {str(e)}")
    
    async def get_metrics_history(self, hours: int = 24) -> list:
        """Get metrics history for the specified number of hours"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            cursor = db.system_metrics.find(
                {"timestamp": {"$gte": start_time}},
                sort=[("timestamp", 1)]
            )
            
            metrics = []
            async for doc in cursor:
                metrics.append(SystemMetrics(**doc))
            
            return metrics
        except Exception as e:
            await self.log_error(f"Error getting metrics history: {str(e)}")
            return []
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get static system information"""
        try:
            info = {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "architecture": platform.architecture()[0],
                "cpu_cores": psutil.cpu_count(),
                "cpu_logical": psutil.cpu_count(logical=True),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "python_version": platform.python_version()
            }
            
            return info
        except Exception as e:
            await self.log_error(f"Error getting system info: {str(e)}")
            return {}
    
    async def get_running_processes(self, limit: int = 10) -> list:
        """Get top running processes by CPU usage"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] is not None:
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage and return top processes
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
            
        except Exception as e:
            await self.log_error(f"Error getting running processes: {str(e)}")
            return []
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check system health and return alerts"""
        try:
            metrics = await self.get_current_metrics()
            alerts = []
            status = "healthy"
            
            # CPU usage alerts
            if metrics.cpu_usage > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"High CPU usage: {metrics.cpu_usage:.1f}%",
                    "threshold": 90
                })
                status = "critical"
            elif metrics.cpu_usage > 80:
                alerts.append({
                    "type": "warning",
                    "message": f"High CPU usage: {metrics.cpu_usage:.1f}%",
                    "threshold": 80
                })
                if status == "healthy":
                    status = "warning"
            
            # Memory usage alerts
            memory_percent = (metrics.memory_used / metrics.memory_total) * 100
            if memory_percent > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"High memory usage: {memory_percent:.1f}%",
                    "threshold": 90
                })
                status = "critical"
            elif memory_percent > 80:
                alerts.append({
                    "type": "warning",
                    "message": f"High memory usage: {memory_percent:.1f}%",
                    "threshold": 80
                })
                if status == "healthy":
                    status = "warning"
            
            # Disk usage alerts
            disk_percent = (metrics.disk_used / metrics.disk_total) * 100
            if disk_percent > 95:
                alerts.append({
                    "type": "critical",
                    "message": f"High disk usage: {disk_percent:.1f}%",
                    "threshold": 95
                })
                status = "critical"
            elif disk_percent > 85:
                alerts.append({
                    "type": "warning",
                    "message": f"High disk usage: {disk_percent:.1f}%",
                    "threshold": 85
                })
                if status == "healthy":
                    status = "warning"
            
            # CPU temperature alerts (if available)
            if metrics.cpu_temperature:
                if metrics.cpu_temperature > 80:
                    alerts.append({
                        "type": "critical",
                        "message": f"High CPU temperature: {metrics.cpu_temperature:.1f}°C",
                        "threshold": 80
                    })
                    status = "critical"
                elif metrics.cpu_temperature > 70:
                    alerts.append({
                        "type": "warning",
                        "message": f"High CPU temperature: {metrics.cpu_temperature:.1f}°C",
                        "threshold": 70
                    })
                    if status == "healthy":
                        status = "warning"
            
            # Log critical alerts
            for alert in alerts:
                if alert["type"] == "critical":
                    await self.log_system_alert(alert["message"])
            
            return {
                "status": status,
                "alerts": alerts,
                "metrics": metrics.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await self.log_error(f"Error checking system health: {str(e)}")
            return {
                "status": "error",
                "alerts": [{"type": "error", "message": "Unable to check system health"}],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def start_monitoring(self, interval: int = 60):
        """Start continuous system monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval))
        
        await self.log_info("System monitoring started")
    
    async def stop_monitoring(self):
        """Stop continuous system monitoring"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        await self.log_info("System monitoring stopped")
    
    async def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Get and store current metrics
                metrics = await self.get_current_metrics()
                await self.store_metrics(metrics)
                
                # Check system health
                health = await self.check_system_health()
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.log_error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(interval)
    
    async def log_info(self, message: str):
        """Log info message"""
        log_entry = LogEntry(
            level=LogLevel.INFO,
            source=LogSource.SYSTEM,
            message=message
        )
        await db.logs.insert_one(log_entry.dict())
    
    async def log_error(self, message: str):
        """Log error message"""
        log_entry = LogEntry(
            level=LogLevel.ERROR,
            source=LogSource.SYSTEM,
            message=message
        )
        await db.logs.insert_one(log_entry.dict())
    
    async def log_system_alert(self, message: str):
        """Log system alert"""
        log_entry = LogEntry(
            level=LogLevel.CRITICAL,
            source=LogSource.SYSTEM,
            message=f"SYSTEM ALERT: {message}"
        )
        await db.logs.insert_one(log_entry.dict())

# Create global instance
system_monitor = SystemMonitorService()