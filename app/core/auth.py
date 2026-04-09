from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "uae-pint-ae-secret-key-2024-adamas-tech"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Seed data for init_db
DEFAULT_USERS = {
    "admin": {
        "username": "admin",
        "email": "admin@adamas.tech",
        "full_name": "Admin User",
        "role": "Admin",
        "hashed_password": pwd_context.hash("Admin@123"),
        "status": "Active",
        "avatar": "AU",
    },
    "analyst": {
        "username": "analyst",
        "email": "sarah.m@adamas.tech",
        "full_name": "Sarah Miller",
        "role": "Analyst",
        "hashed_password": pwd_context.hash("Analyst@123"),
        "status": "Active",
        "avatar": "SM",
    },
    "viewer": {
        "username": "viewer",
        "email": "john.d@adamas.tech",
        "full_name": "John Doe",
        "role": "Viewer",
        "hashed_password": pwd_context.hash("Viewer@123"),
        "status": "Active",
        "avatar": "JD",
    }
}

def get_all_default_users():
    """Return all default user dicts for DB seeding."""
    return list(DEFAULT_USERS.values())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str) -> Optional[dict]:
    from app.db.models import User
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    # Convert SQLAlchemy object to dict for backward compatibility in the router
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "hashed_password": user.hashed_password,
        "status": user.status,
        "avatar": user.avatar
    }

def authenticate_user(db, username: str, password: str) -> Optional[dict]:
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
