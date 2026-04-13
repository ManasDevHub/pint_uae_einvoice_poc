from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from app.core.auth import authenticate_user, create_access_token, decode_token, get_user, pwd_context
from app.db.session import get_db
from app.db.models import User, AuditLog
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import timedelta, datetime

router = APIRouter()
bearer = HTTPBearer(auto_error=False)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    status: str
    avatar: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    password: str
    status: Optional[str] = "Active"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db)
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    username = payload.get("sub")
    user_dict = get_user(db, username)
    if not user_dict:
        raise HTTPException(status_code=401, detail="User not found")
    return user_dict

def _log_audit(db: Session, username: str, action: str, success: bool, request: Request = None, detail: str = None):
    try:
        # Try to get real IP if behind proxy
        ip = "unknown"
        if request:
            ip = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")
            if "," in ip: ip = ip.split(",")[0].strip() # Handle multiple proxies
        
        log_entry = AuditLog(username=username, action=action, success=success, ip_address=ip, detail=detail)
        db.add(log_entry)
        db.commit()
    except Exception:
        pass  # Never let audit logging break the main flow

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.username, req.password)
    if not user:
        _log_audit(db, req.username, "LOGIN", False, request, "Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    # Update last_login
    db_user = db.query(User).filter(User.username == req.username).first()
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.commit()
    _log_audit(db, req.username, "LOGIN", True, request, "Successful login")
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(hours=8)
    )
    user_out = {k: v for k, v in user.items() if k != "hashed_password"}
    return {"access_token": token, "token_type": "bearer", "user": user_out}

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserOut])
async def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(User).order_by(User.created_at).all()
    return users

@router.post("/users", response_model=UserOut)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user. Admin only. New user can immediately sign in."""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=409, detail=f"Username '{user_data.username}' is already taken")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=409, detail=f"Email '{user_data.email}' is already in use")
    parts = user_data.full_name.split()
    avatar = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else parts[0][:2].upper()
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=pwd_context.hash(user_data.password),
        status=user_data.status or "Active",
        avatar=avatar
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    _log_audit(db, current_user["username"], "USER_CREATED", True, request, f"Created user: {user_data.username}")
    return new_user

@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin" and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if update_data.full_name: user.full_name = update_data.full_name
    if update_data.email: user.email = update_data.email
    if update_data.role and current_user["role"] == "Admin": user.role = update_data.role
    if update_data.status and current_user["role"] == "Admin": user.status = update_data.status
    if update_data.password:
        user.hashed_password = pwd_context.hash(update_data.password)
        _log_audit(db, current_user["username"], "PASSWORD_CHANGE", True, request, f"Changed password for: {user.username}")
    
    if update_data.role:
        _log_audit(db, current_user["username"], "ROLE_CHANGED", True, request, f"Changed role for {user.username} to {update_data.role}")
    
    if update_data.status:
        _log_audit(db, current_user["username"], "STATUS_CHANGED", True, request, f"Changed status for {user.username} to {update_data.status}")

    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    username = user.username
    db.delete(user)
    db.commit()
    _log_audit(db, current_user["username"], "USER_DELETED", True, request, f"Deleted user: {username}")
    return {"message": f"User '{username}' deleted successfully"}

@router.get("/audit-log")
async def get_audit_log(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
    return [
        {
            "id": l.id,
            "username": l.username,
            "action": l.action,
            "success": l.success,
            "ip_address": l.ip_address,
            "detail": l.detail,
            "created_at": l.created_at
        }
        for l in logs
    ]

@router.post("/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    _log_audit(db, current_user["username"], "LOGOUT", True, request)
    return {"message": "Logged out successfully"}
