from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Payment, Project, PaymentType, PaymentStatus

UPI_ID = "8655229505@upi"


def create_upi_order(project: Project, payment_type: str) -> tuple[dict, float]:
    """Create a UPI payment order (manual verification)."""
    if not project.budget:
        raise ValueError("Project budget not set")

    amount = float(project.budget) * 0.5
    order_id = f"hermes_{project.id}_{payment_type}".replace("-", "")[:30]

    order = {
        "id": order_id,
        "amount": amount,
        "currency": "INR",
        "upi_id": UPI_ID,
        "upi_link": f"upi://pay?pa={UPI_ID}&pn=Hermes&am={amount}&cu=INR&tn={order_id}",
        "payment_type": payment_type,
    }
    return order, amount


async def create_payment_record(
    project_id, payment_type: str, amount: float, order_id: str, db: AsyncSession
) -> Payment:
    payment = Payment(
        project_id=project_id,
        type=PaymentType(payment_type),
        gross_amount=Decimal(str(amount)),
        net_amount=Decimal(str(amount)),
        status=PaymentStatus.PENDING,
        razorpay_order_id=order_id,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def mark_payment_received(project_id: str, payment_type: str, db: AsyncSession):
    """Admin manually confirms UPI payment was received."""
    result = await db.execute(
        select(Payment).where(
            Payment.project_id == project_id,
            Payment.type == PaymentType(payment_type),
        )
    )
    payment = result.scalar_one_or_none()
    if payment:
        payment.status = PaymentStatus.HELD
        payment.released_at = datetime.utcnow()
        await db.commit()
    return payment


async def release_payout(user_id: str, amount: float, project_id: str, payment_type: str, db: AsyncSession):
    """Mark payout as released (manual UPI transfer by admin)."""
    result = await db.execute(
        select(Payment).where(
            Payment.project_id == project_id,
            Payment.type == PaymentType(payment_type),
        )
    )
    payment = result.scalar_one_or_none()
    if payment:
        payment.status = PaymentStatus.RELEASED
        payment.released_at = datetime.utcnow()
        await db.commit()
    print(f"[Payout] {payment_type} ₹{amount} to user {user_id} — transfer manually via UPI")
