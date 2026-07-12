from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import (
    Project, ProjectStatus, Payment, PaymentStatus, User, FreelancerProfile,
)
from app.services.payments import release_payout
from app.config import settings
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_TOKEN = "hermes-admin-secret"  # Replace with proper auth


def verify_admin(authorization: str = Header(...)):
    if authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(403, "Admin access required")
    return True


@router.get("/projects")
async def list_projects(
    status: str = None,
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Project)
    if status:
        query = query.where(Project.status == ProjectStatus(status))
    query = query.order_by(Project.created_at.desc()).limit(50)
    result = await db.execute(query)
    projects = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "status": p.status.value,
            "client_id": str(p.client_id),
            "assigned_freelancer_id": str(p.assigned_freelancer_id) if p.assigned_freelancer_id else None,
            "budget": float(p.budget) if p.budget else None,
            "created_at": str(p.created_at),
        }
        for p in projects
    ]


@router.post("/projects/{project_id}/force-release")
async def force_release(
    project_id: str,
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404)

    # Release any held payments
    result = await db.execute(
        select(Payment).where(
            Payment.project_id == project_id,
            Payment.status == PaymentStatus.HELD,
        )
    )
    payments = result.scalars().all()
    for payment in payments:
        await release_payout(
            str(project.assigned_freelancer_id),
            float(payment.net_amount),
            project_id,
            payment.type.value,
            db,
        )

    project.status = ProjectStatus.CLOSED
    project.completed_at = datetime.utcnow()

    # Free freelancer
    result = await db.execute(
        select(FreelancerProfile).where(
            FreelancerProfile.user_id == project.assigned_freelancer_id
        )
    )
    fp = result.scalar_one_or_none()
    if fp:
        fp.current_project_id = None
        fp.availability = True

    await db.commit()
    return {"status": "force released"}


@router.post("/projects/{project_id}/force-refund")
async def force_refund(
    project_id: str,
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404)

    # Mark payments as refunded
    result = await db.execute(
        select(Payment).where(
            Payment.project_id == project_id,
            Payment.status.in_([PaymentStatus.HELD, PaymentStatus.PENDING]),
        )
    )
    payments = result.scalars().all()
    for payment in payments:
        payment.status = PaymentStatus.REFUNDED

    project.status = ProjectStatus.CLOSED
    project.completed_at = datetime.utcnow()

    # Free freelancer
    if project.assigned_freelancer_id:
        result = await db.execute(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == project.assigned_freelancer_id
            )
        )
        fp = result.scalar_one_or_none()
        if fp:
            fp.current_project_id = None
            fp.availability = True

    await db.commit()
    return {"status": "refunded"}


@router.get("/users")
async def list_users(
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(100))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "phone": u.phone,
            "name": u.name,
            "role": u.role.value if u.role else None,
            "last_login": str(u.last_login) if u.last_login else None,
        }
        for u in users
    ]


@router.get("/payments")
async def list_payments(
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment).order_by(Payment.created_at.desc()).limit(100)
    )
    payments = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "project_id": str(p.project_id),
            "type": p.type.value,
            "gross_amount": float(p.gross_amount),
            "net_amount": float(p.net_amount),
            "status": p.status.value,
            "created_at": str(p.created_at),
        }
        for p in payments
    ]
