from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import (
    User, DailyMatchBatch, Swipe, SwipeDirection,
    FreelancerProfile, Project, ProjectStatus,
)
from app.schemas.schemas import SwipeRequest, FreelancerProfileOut
from app.services.auth import get_current_user
from app.services.notifications import notify
from app.services.payments import create_upi_order, create_payment_record
from datetime import datetime, timedelta

router = APIRouter(prefix="/swipe", tags=["swipe"])


@router.get("/batch/{project_id}")
async def get_swipe_batch(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DailyMatchBatch).where(
            DailyMatchBatch.project_id == project_id,
            DailyMatchBatch.client_id == user.id,
            DailyMatchBatch.batch_date == date.today(),
        )
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(404, "No batch generated yet for today")

    remaining_ids = [
        fid for fid in (batch.freelancer_ids or [])
        if fid not in (batch.swiped_ids or [])
    ]

    result = await db.execute(
        select(FreelancerProfile).where(FreelancerProfile.user_id.in_(remaining_ids))
    )
    profiles = result.scalars().all()

    return {
        "profiles": [FreelancerProfileOut.model_validate(p) for p in profiles],
        "remaining": len(remaining_ids),
    }


@router.post("/")
async def record_swipe(
    data: SwipeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    swipe = Swipe(
        client_id=user.id,
        project_id=data.project_id,
        freelancer_id=data.freelancer_id,
        direction=SwipeDirection(data.direction),
    )
    db.add(swipe)

    result = await db.execute(
        select(DailyMatchBatch).where(
            DailyMatchBatch.project_id == data.project_id,
            DailyMatchBatch.client_id == user.id,
            DailyMatchBatch.batch_date == date.today(),
        )
    )
    batch = result.scalar_one_or_none()
    if batch:
        batch.swiped_ids = (batch.swiped_ids or []) + [data.freelancer_id]

    await db.commit()
    return {"status": "recorded"}


@router.post("/select/{freelancer_id}")
async def select_freelancer(
    freelancer_id: str,
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate right swipe exists
    result = await db.execute(
        select(Swipe).where(
            Swipe.client_id == user.id,
            Swipe.project_id == project_id,
            Swipe.freelancer_id == freelancer_id,
            Swipe.direction == SwipeDirection.RIGHT,
        )
    )
    swipe = result.scalar_one_or_none()
    if not swipe:
        raise HTTPException(400, "You must swipe right before selecting")

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404)

    project.assigned_freelancer_id = freelancer_id
    project.status = ProjectStatus.ADVANCE_PENDING
    project.assigned_at = datetime.utcnow()

    # Compute deadline
    if project.timeline_unit:
        unit = project.timeline_unit.value
        val = project.timeline_value or 0
        if unit == "days":
            project.deadline = date.today() + timedelta(days=val)
        elif unit == "weeks":
            project.deadline = date.today() + timedelta(weeks=val)
        elif unit == "months":
            project.deadline = date.today() + timedelta(days=val * 30)

    # Update batch
    result = await db.execute(
        select(DailyMatchBatch).where(DailyMatchBatch.project_id == project_id)
    )
    batch = result.scalar_one_or_none()
    if batch:
        batch.selected_freelancer_id = freelancer_id

    await db.commit()

    await notify(
        freelancer_id,
        f"You've been selected for '{project.title}'. Waiting for client payment.",
        db,
    )

    # Create UPI order for advance
    order, amount = create_upi_order(project, "ADVANCE")
    await create_payment_record(project_id, "ADVANCE", amount, order["id"], db)

    return {"order": order}
