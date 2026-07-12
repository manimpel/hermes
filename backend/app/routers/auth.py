from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import OTPSendRequest, AuthResponse, UserUpdate
from app.services.auth import create_jwt, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
async def login(req: OTPSendRequest, db: AsyncSession = Depends(get_db)):
    """Simple phone login — no OTP for MVP."""
    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()
    is_new = user is None

    if is_new:
        user = User(phone=req.phone)
        db.add(user)

    user.last_login = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    token = create_jwt({"user_id": str(user.id)})
    return AuthResponse(token=token, user_id=str(user.id), is_new=is_new)


@router.put("/user")
async def update_user(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.role is not None:
        user.role = data.role
    await db.commit()
    await db.refresh(user)
    return {"message": "Updated", "user_id": str(user.id)}


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "phone": user.phone,
        "name": user.name,
        "email": user.email,
        "role": user.role.value if user.role else None,
    }
