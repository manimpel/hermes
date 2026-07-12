from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import User, ClientProfile
from app.schemas.schemas import ClientProfileCreate, ClientProfileUpdate, ClientProfileOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/client", tags=["client"])


@router.post("/profile", response_model=ClientProfileOut)
async def create_or_update_profile(
    data: ClientProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
    else:
        profile = ClientProfile(user_id=user.id, **data.model_dump(exclude_unset=True))
        db.add(profile)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.put("/profile", response_model=ClientProfileOut)
async def update_profile(
    data: ClientProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/profile/{user_id}", response_model=ClientProfileOut)
async def get_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Client profile not found")
    return profile
