import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid
from ..core.database import get_db
from ..models import User, Organization
from ..core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from .auth import get_current_user
from .rate_limit import limiter
from jwt import ExpiredSignatureError, InvalidTokenError

router = APIRouter(prefix="/auth", tags=["authentication"])

def _is_valid_email(email: str) -> bool:
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email) is not None

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class UserCreate(BaseModel):
    email: str
    password: str
    name: str = ""
    role: str = "viewer"
    org_name: str = "Default Organization"

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    org_id: str

@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == data.email, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.user_id), "role": user.role, "org_id": str(user.org_id)})
    refresh_token = create_refresh_token({"sub": str(user.user_id)})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.user_id),
            "email": user.email,
            "name": user.name or "",
            "role": user.role,
            "org_id": str(user.org_id)
        }
    }

@router.post("/refresh")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    stmt = select(User).where(User.user_id == user_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    new_access_token = create_access_token({"sub": str(user.user_id), "role": user.role, "org_id": str(user.org_id)})
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.user_id),
        "email": current_user.email,
        "name": current_user.name or "",
        "role": current_user.role,
        "org_id": str(current_user.org_id)
    }

@router.post("/register")
@limiter.limit("5/hour")
async def register(request: Request, data: UserCreate, db: AsyncSession = Depends(get_db)):
    if not _is_valid_email(data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        org = Organization(name=data.org_name)
        db.add(org)
        await db.flush()
        hashed = hash_password(data.password)
        user = User(
            user_id=uuid.uuid4(),
            org_id=org.org_id,
            email=data.email,
            hashed_password=hashed,
            name=data.name,
            role=data.role,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")
    access_token = create_access_token({"sub": str(user.user_id), "role": user.role, "org_id": str(user.org_id)})
    refresh_token = create_refresh_token({"sub": str(user.user_id)})
    return {
        "message": "User created successfully",
        "user_id": str(user.user_id),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }