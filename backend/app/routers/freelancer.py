from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import User, FreelancerProfile
from app.schemas.schemas import (
    FreelancerProfileCreate, FreelancerProfileUpdate, FreelancerProfileOut
)
from app.services.auth import get_current_user
from app.agent.linkedin_parser import hermes_parse_linkedin

router = APIRouter(prefix="/freelancer", tags=["freelancer"])


@router.post("/profile", response_model=FreelancerProfileOut)
async def create_or_update_profile(
    data: FreelancerProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
    else:
        profile = FreelancerProfile(user_id=user.id, **data.model_dump(exclude_unset=True))
        db.add(profile)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.put("/profile", response_model=FreelancerProfileOut)
async def update_profile(
    data: FreelancerProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found. Create one first.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/profile/{user_id}", response_model=FreelancerProfileOut)
async def get_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Freelancer profile not found")
    return profile


@router.post("/linkedin-upload")
async def upload_linkedin(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    html_content = await file.read()
    html_text = html_content.decode("utf-8", errors="ignore")

    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = FreelancerProfile(user_id=user.id)
        db.add(profile)

    profile.linkedin_raw_html = html_text
    await db.commit()

    background_tasks.add_task(hermes_parse_linkedin, str(user.id), html_text, db)
    return {"message": "LinkedIn file received, parsing in background"}


@router.post("/portfolio-links")
async def set_portfolio_links(
    links: list[str],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(links) > 3:
        raise HTTPException(400, "Maximum 3 portfolio links allowed")

    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    profile.portfolio_links = links
    await db.commit()
    return {"message": "Portfolio links updated"}


@router.put("/interest-areas")
async def set_interest_areas(
    areas: list[str],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    profile.interest_areas = areas
    await db.commit()
    return {"message": "Interest areas updated"}


@router.put("/availability")
async def set_availability(
    available: bool,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")

    profile.availability = available
    await db.commit()
    return {"message": f"Availability set to {available}"}
