import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import User, UserLogin, TOTPSetup, TokenResponse
from database import db
import os

# Security configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.pwd_context = pwd_context
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token"
            )
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username from database"""
        user_data = await db.users.find_one({"username": username})
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from database"""
        user_data = await db.users.find_one({"id": user_id})
        if user_data:
            return User(**user_data)
        return None
    
    async def create_user(self, username: str, email: str, password: str, role: str = "user") -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_username(username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=role
        )
        
        # Save to database
        await db.users.insert_one(user.dict())
        return user
    
    async def authenticate_user(self, login_data: UserLogin, ip_address: str) -> TokenResponse:
        """Authenticate user and return token"""
        user = await self.get_user_by_username(login_data.username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked"
            )
        
        # Verify password
        if not self.verify_password(login_data.password, user.password_hash):
            # Increment failed attempts
            await db.users.update_one(
                {"id": user.id},
                {
                    "$inc": {"failed_login_attempts": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= 4:  # 5 total attempts
                lock_until = datetime.utcnow() + timedelta(minutes=30)
                await db.users.update_one(
                    {"id": user.id},
                    {"$set": {"locked_until": lock_until}}
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check 2FA if enabled
        if user.totp_enabled:
            if not login_data.totp_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TOTP code required",
                    headers={"X-Require-TOTP": "true"}
                )
            
            if not self.verify_totp(user.totp_secret, login_data.totp_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid TOTP code"
                )
        
        # Check IP restrictions
        if user.allowed_ips and ip_address not in user.allowed_ips:
            # Log suspicious login attempt
            await self.log_security_event(
                user.id, ip_address, "UNAUTHORIZED_IP", 
                f"Login attempt from unauthorized IP: {ip_address}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP address not allowed"
            )
        
        # Reset failed attempts and update last login
        await db.users.update_one(
            {"id": user.id},
            {
                "$set": {
                    "failed_login_attempts": 0,
                    "last_login": datetime.utcnow(),
                    "locked_until": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Create access token
        token_data = {
            "sub": user.id,
            "username": user.username,
            "role": user.role
        }
        access_token = self.create_access_token(token_data)
        
        # Log successful login
        await self.log_security_event(
            user.id, ip_address, "LOGIN_SUCCESS", 
            f"Successful login for user: {user.username}"
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, secret: str, username: str, issuer: str = "RDP Stealth") -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        if not secret or not token:
            return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    async def setup_totp(self, user_id: str) -> TOTPSetup:
        """Setup TOTP for user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        secret = self.generate_totp_secret()
        qr_code = self.generate_qr_code(secret, user.username)
        
        # Save secret to database (not enabled yet)
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"totp_secret": secret, "updated_at": datetime.utcnow()}}
        )
        
        return TOTPSetup(secret=secret, qr_code=qr_code)
    
    async def enable_totp(self, user_id: str, totp_code: str) -> bool:
        """Enable TOTP after verification"""
        user = await self.get_user_by_id(user_id)
        if not user or not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP not setup"
            )
        
        if not self.verify_totp(user.totp_secret, totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code"
            )
        
        # Enable TOTP
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"totp_enabled": True, "updated_at": datetime.utcnow()}}
        )
        
        await self.log_security_event(
            user_id, None, "TOTP_ENABLED", 
            f"TOTP enabled for user: {user.username}"
        )
        
        return True
    
    async def log_security_event(self, user_id: str, ip_address: str, event_type: str, message: str):
        """Log security events"""
        from models import LogEntry, LogLevel, LogSource
        
        log_entry = LogEntry(
            level=LogLevel.WARNING if "UNAUTHORIZED" in event_type else LogLevel.INFO,
            source=LogSource.AUTH_SERVICE,
            message=message,
            details={"event_type": event_type, "user_id": user_id},
            user_id=user_id,
            ip_address=ip_address
        )
        
        await db.logs.insert_one(log_entry.dict())

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    auth_service = AuthService()
    
    try:
        payload = auth_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token"
            )
        
        user = await auth_service.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token"
        )

# Create default admin user if not exists
async def create_default_admin():
    """Create default admin user if it doesn't exist"""
    auth_service = AuthService()
    
    admin_user = await auth_service.get_user_by_username("admin")
    if not admin_user:
        await auth_service.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="admin"
        )
        print("Default admin user created: admin/admin123")