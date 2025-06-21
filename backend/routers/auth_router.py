from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from datetime import datetime
from models import UserLogin, TokenResponse, User, TOTPSetup, SuccessResponse
from auth import AuthService, get_current_user
from database import db

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, request: Request):
    """Login with username/password and optional 2FA"""
    auth_service = AuthService()
    
    # Get client IP
    client_ip = request.client.host
    if hasattr(request, 'headers') and 'x-forwarded-for' in request.headers:
        client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()
    
    return await auth_service.authenticate_user(login_data, client_ip)

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    # Don't return password hash
    user_dict = current_user.dict()
    user_dict.pop('password_hash', None)
    return User(**user_dict)

@router.post("/setup-2fa", response_model=TOTPSetup)
async def setup_two_factor(current_user: User = Depends(get_current_user)):
    """Setup two-factor authentication"""
    auth_service = AuthService()
    return await auth_service.setup_totp(current_user.id)

@router.post("/enable-2fa", response_model=SuccessResponse)
async def enable_two_factor(
    totp_code: str,
    current_user: User = Depends(get_current_user)
):
    """Enable two-factor authentication after verification"""
    auth_service = AuthService()
    await auth_service.enable_totp(current_user.id, totp_code)
    
    return SuccessResponse(
        message="Two-factor authentication enabled successfully"
    )

@router.post("/disable-2fa", response_model=SuccessResponse)
async def disable_two_factor(
    password: str,
    current_user: User = Depends(get_current_user)
):
    """Disable two-factor authentication"""
    auth_service = AuthService()
    
    # Verify password
    if not auth_service.verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Disable 2FA
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "totp_enabled": False,
                "totp_secret": None,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return SuccessResponse(
        message="Two-factor authentication disabled successfully"
    )

@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    auth_service = AuthService()
    
    # Verify current password
    if not auth_service.verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid current password"
        )
    
    # Hash new password
    new_password_hash = auth_service.hash_password(new_password)
    
    # Update password
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return SuccessResponse(
        message="Password changed successfully"
    )