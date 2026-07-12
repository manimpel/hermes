from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import (
    Payment, Project, ProjectStatus, PaymentType, PaymentStatus,
    FreelancerProfile,
)
from app.services.payments import mark_payment_received, release_payout
from app.services.notifications import notify
from datetime import datetime

router = APIRouter(prefix="/webhooks", tags=["payments"])

ADMIN_TOKEN = "hermes-admin-secret"


def verify_admin(authorization: str = Header(...)):
    if authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(403, "Admin access required")
    return True


@router.post("/confirm-payment/{project_id}")
async def confirm_upi_payment(
    project_id: str,
    payment_type: str = "ADVANCE",
    _: bool = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin confirms UPI payment was received for a project."""
    payment = await mark_payment_received(project_id, payment_type, db)
    if not payment:
        raise HTTPException(404, "Payment record not found")

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    if payment_type == "ADVANCE":
        project.status = ProjectStatus.IN_PROGRESS

        # Lock freelancer
        result = await db.execute(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == project.assigned_freelancer_id
            )
        )
        fp = result.scalar_one_or_none()
        if fp:
            fp.current_project_id = project.id
            fp.availability = False

        await db.commit()

        await notify(str(project.client_id), "Payment confirmed. Project is now in progress.", db)
        await notify(
            str(project.assigned_freelancer_id),
            f"Payment received. Begin '{project.title}'. Deadline: {project.deadline}",
            db,
        )

    elif payment_type == "FINAL":
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

    return {"status": "payment confirmed", "project_status": project.status.value}
