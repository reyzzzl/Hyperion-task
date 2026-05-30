import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..models import APIKey
from .auth import get_current_user, require_role

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

def _get_cipher():
    key = os.environ.get("API_KEY_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("API_KEY_ENCRYPTION_KEY environment variable is required")
    try:
        return Fernet(key.encode())
    except Exception:
        raise RuntimeError("API_KEY_ENCRYPTION_KEY must be a valid Fernet key (32 url-safe base64 bytes)")

class CreateAPIKeyRequest(BaseModel):
    scopes: list[str] = []
    expires_days: int = 90

class APIKeyResponse(BaseModel):
    key_id: str
    scopes: list[str]
    expires_at: str
    created_at: str

@router.post("")
async def create_api_key(
    req: CreateAPIKeyRequest,
    current_user = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db)
):
    raw_key = f"hyp_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    encrypted = _get_cipher().encrypt(raw_key.encode()).decode()
    expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_days)
    api_key = APIKey(
        org_id=current_user.org_id,
        user_id=current_user.user_id,
        key_hash=key_hash,
        encrypted_key=encrypted,
        scopes=req.scopes,
        expires_at=expires_at,
        revoked=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(api_key)
    await db.commit()
    return {"key": raw_key, "key_id": str(api_key.key_id), "expires_at": expires_at.isoformat()}

@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(APIKey).where(APIKey.user_id == current_user.user_id, APIKey.revoked == False)
    result = await db.execute(stmt)
    keys = result.scalars().all()
    return [
        {
            "key_id": str(k.key_id),
            "scopes": k.scopes,
            "expires_at": k.expires_at.isoformat() if k.expires_at else "",
            "created_at": k.created_at.isoformat()
        }
        for k in keys
    ]

@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user = Depends(require_role(["admin", "owner"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(APIKey).where(APIKey.key_id == key_id, APIKey.user_id == current_user.user_id)
    result = await db.execute(stmt)
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.revoked = True
    await db.commit()
    return {"message": "API key revoked"}