from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import (
    User, Project, ProjectStatus, FreelancerProfile,
    DailyMatchBatch, Rating, Payment,
)
from app.services.auth import get_current_user
from datetime import date

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/freelancer")
async def freelancer_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Freelancer profile not found")

    # Current project
    current_project = None
    if profile.current_project_id:
        result = await db.execute(
            select(Project).where(Project.id == profile.current_project_id)
        )
        current_project = result.scalar_one_or_none()

    # Past projects
    result = await db.execute(
        select(Project).where(
            Project.assigned_freelancer_id == user.id,
            Project.status == ProjectStatus.CLOSED,
        ).order_by(Project.completed_at.desc())
    )
    past_projects = result.scalars().all()

    # Earnings
    result = await db.execute(
        select(func.sum(Payment.net_amount)).where(
            Payment.project_id.in_(
                select(Project.id).where(Project.assigned_freelancer_id == user.id)
            ),
            Payment.status.in_(["RELEASED"]),
        )
    )
    total_earnings = result.scalar() or 0

    return {
        "availability": profile.availability,
        "avg_rating": float(profile.avg_rating) if profile.avg_rating else None,
        "completed_count": profile.completed_count or 0,
        "current_project": {
            "id": str(current_project.id),
            "title": current_project.title,
            "status": current_project.status.value,
            "deadline": str(current_project.deadline) if current_project.deadline else None,
            "revision_count": current_project.revision_count,
        } if current_project else None,
        "past_projects": [
            {
                "id": str(p.id),
                "title": p.title,
                "completed_at": str(p.completed_at) if p.completed_at else None,
            }
            for p in past_projects
        ],
        "total_earnings": float(total_earnings),
    }


@router.get("/client")
async def client_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Active projects
    result = await db.execute(
        select(Project).where(
            Project.client_id == user.id,
            Project.status.notin_([ProjectStatus.CLOSED, ProjectStatus.DRAFT]),
        ).order_by(Project.created_at.desc())
    )
    active_projects = result.scalars().all()

    # Today's swipe batches
    result = await db.execute(
        select(DailyMatchBatch).where(
            DailyMatchBatch.client_id == user.id,
            DailyMatchBatch.batch_date == date.today(),
        )
    )
    batches = result.scalars().all()

    # Past projects
    result = await db.execute(
        select(Project).where(
            Project.client_id == user.id,
            Project.status == ProjectStatus.CLOSED,
        ).order_by(Project.completed_at.desc())
    )
    past_projects = result.scalars().all()

    return {
        "active_projects": [
            {
                "id": str(p.id),
                "title": p.title,
                "status": p.status.value,
                "assigned_freelancer_id": str(p.assigned_freelancer_id) if p.assigned_freelancer_id else None,
                "deadline": str(p.deadline) if p.deadline else None,
            }
            for p in active_projects
        ],
        "swipe_batches": [
            {
                "project_id": str(b.project_id),
                "remaining": len([
                    fid for fid in (b.freelancer_ids or [])
                    if fid not in (b.swiped_ids or [])
                ]),
            }
            for b in batches
        ],
        "past_projects": [
            {
                "id": str(p.id),
                "title": p.title,
                "completed_at": str(p.completed_at) if p.completed_at else None,
            }
            for p in past_projects
        ],
    }
