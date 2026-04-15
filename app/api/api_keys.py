# app/api/api_keys.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import SystemApiKey
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
import hashlib, secrets, datetime

router = APIRouter()

class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyOut(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime.datetime
    key: Optional[str] = None # Only returned on creation

@router.get("/keys", response_model=List[ApiKeyOut])
async def list_keys(request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    keys = db.query(SystemApiKey).filter(
        SystemApiKey.tenant_id == tenant_id,
        SystemApiKey.is_active == True
    ).all()
    return [{"id": k.id, "name": k.name, "key_prefix": k.key_prefix, "is_active": k.is_active, "created_at": k.created_at} for k in keys]

@router.post("/keys", response_model=ApiKeyOut)
async def generate_key(request: Request, body: ApiKeyCreate, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    
    # Generate random key
    raw_key = f"uae_{secrets.token_urlsafe(32)}"
    hashed = hashlib.sha256(raw_key.encode()).hexdigest()
    
    new_key = SystemApiKey(
        tenant_id=tenant_id,
        name=body.name,
        key_prefix=raw_key[:8] + "...",
        hashed_key=hashed,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    return {
        "id": new_key.id,
        "name": new_key.name,
        "key_prefix": new_key.key_prefix,
        "is_active": new_key.is_active,
        "created_at": new_key.created_at,
        "key": raw_key # RETURN ONCE
    }

@router.delete("/keys/{key_id}")
async def revoke_key(key_id: str, request: Request, db: Session = Depends(get_db)):
    tenant_id = getattr(request.state, "tenant_id", "demo-key-123")
    key = db.query(SystemApiKey).filter(
        SystemApiKey.id == key_id,
        SystemApiKey.tenant_id == tenant_id
    ).first()
    if not key:
        raise HTTPException(404, "Key not found")
    
    key.is_active = False
    db.commit()
    return {"message": "Key revoked"}
