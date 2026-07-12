from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import User, Rating, Project, ProjectStatus, FreelancerProfile
from app.schemas.schemas import RatingCreate, RatingOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("/", response_model=RatingOut)
async def create_rating(
    data: RatingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == data.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status != ProjectStatus.CLOSED:
        raise HTTPException(400, "Can only rate after project closes")
    if str(user.id) not in [str(project.client_id), str(project.assigned_freelancer_id)]:
        raise HTTPException(403, "Not part of this project")

    # Check if already rated
    result = await db.execute(
        select(Rating).where(
            Rating.project_id == data.project_id,
            Rating.rater_id == user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(400, "Already rated for this project")

    rating = Rating(
        project_id=data.project_id,
        rater_id=user.id,
        ratee_id=data.ratee_id,
        score=data.score,
        review=data.review,
    )
    db.add(rating)

    # Update avg rating if ratee is a freelancer
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == data.ratee_id)
    )
    fp = result.scalar_one_or_none()
    if fp:
        result = await db.execute(
            select(func.avg(Rating.score)).where(Rating.ratee_id == data.ratee_id)
        )
        avg = result.scalar()
        fp.avg_rating = avg
        fp.completed_count = (fp.completed_count or 0) + 1

    await db.commit()
    await db.refresh(rating)
    return rating


@router.get("/user/{user_id}", response_model=list[RatingOut])
async def get_user_ratings(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Rating).where(Rating.ratee_id == user_id).order_by(Rating.created_at.desc())
    )
    return result.scalars().all()
