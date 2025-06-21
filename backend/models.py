from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# User and Authentication Models
class UserRole(str, Enum):
    admin = "admin"
    user = "user"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.user
    totp_secret: Optional[str] = None
    totp_enabled: bool = False
    allowed_ips: List[str] = []
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.user

class UserLogin(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None

class TOTPSetup(BaseModel):
    secret: str
    qr_code: str

# Session Models
class SessionType(str, Enum):
    rdp = "RDP"
    web = "Web Panel"
    file = "File Transfer"

class SessionStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    terminated = "terminated"

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_type: SessionType
    ip_address: str
    country: Optional[str] = None
    city: Optional[str] = None
    user_agent: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: SessionStatus = SessionStatus.active
    bandwidth_used: float = 0.0  # MB
    duration: Optional[int] = None  # seconds

class SessionCreate(BaseModel):
    session_type: SessionType
    ip_address: str
    user_agent: Optional[str] = None

# System Monitoring Models
class SystemMetrics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cpu_usage: float  # percentage
    cpu_temperature: Optional[float] = None  # celsius
    memory_total: int  # MB
    memory_used: int  # MB
    disk_total: int  # GB
    disk_used: int  # GB
    network_upload_speed: float  # KB/s
    network_download_speed: float  # KB/s
    network_total_sent: float  # GB
    network_total_received: float  # GB
    active_connections: int = 0

# File Management Models
class FileType(str, Enum):
    file = "file"
    folder = "folder"

class FileItem(BaseModel):
    name: str
    path: str
    type: FileType
    size: Optional[int] = None  # bytes
    modified: datetime
    permissions: str
    owner: Optional[str] = None
    is_encrypted: bool = False
    checksum: Optional[str] = None

class FileOperation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    operation_type: str  # upload, download, delete, move, copy
    file_path: str
    destination_path: Optional[str] = None
    file_size: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None

# Logging Models
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogSource(str, Enum):
    AUTH_SERVICE = "AUTH_SERVICE"
    RDP_SERVER = "RDP_SERVER"
    FILE_MANAGER = "FILE_MANAGER"
    SYSTEM = "SYSTEM"
    WEB_PANEL = "WEB_PANEL"

class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel
    source: LogSource
    message: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None

class LogQuery(BaseModel):
    level: Optional[LogLevel] = None
    source: Optional[LogSource] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_term: Optional[str] = None
    limit: int = 100

# RDP Connection Models
class RDPConnection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    host: str
    port: int = 3389
    username: str
    password: str  # encrypted
    quality: str = "high"  # low, medium, high, ultra
    status: str = "disconnected"  # connecting, connected, disconnected, error
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

class RDPConnectionCreate(BaseModel):
    host: str
    port: int = 3389
    username: str
    password: str
    quality: str = "high"

# Settings Models
class SecuritySettings(BaseModel):
    auto_lock_timeout: int = 30  # minutes
    require_two_factor: bool = True
    allowed_ips: List[str] = []
    vpn_required: bool = True
    encryption_level: str = "AES-256"
    max_failed_logins: int = 5
    lockout_duration: int = 30  # minutes

class RDPSettings(BaseModel):
    default_port: int = 3389
    default_quality: str = "high"
    audio_redirection: bool = True
    clipboard_sync: bool = True
    stealth_mode: bool = True
    connection_timeout: int = 30  # seconds

class FileSettings(BaseModel):
    max_file_size: int = 100  # MB
    allowed_extensions: List[str] = ["pdf", "doc", "docx", "txt", "jpg", "png", "zip"]
    quarantine_files: bool = True
    encrypt_uploads: bool = True
    scan_for_malware: bool = True

class NotificationSettings(BaseModel):
    email_notifications: bool = True
    login_alerts: bool = True
    file_transfer_alerts: bool = False
    system_alerts: bool = True
    notification_email: EmailStr

class SystemSettings(BaseModel):
    log_level: LogLevel = LogLevel.INFO
    log_retention_days: int = 30
    auto_backup: bool = True
    backup_interval_hours: int = 24
    maintenance_mode: bool = False

class AppSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rdp: RDPSettings = Field(default_factory=RDPSettings)
    files: FileSettings = Field(default_factory=FileSettings)
    notifications: NotificationSettings
    system: SystemSettings = Field(default_factory=SystemSettings)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str

# Response Models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

# Dashboard Models
class DashboardStats(BaseModel):
    active_sessions: int
    total_connections_today: int
    system_uptime: str
    disk_usage_percent: float
    memory_usage_percent: float
    cpu_usage_percent: float
    network_status: str
    security_alerts: int