from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Notification
from app.config import settings
import httpx


async def notify(user_id: str, message: str, db: AsyncSession, data: dict = None, title: str = None):
    """Store notification in DB. Push/SMS integrations added later."""
    notification = Notification(
        user_id=user_id,
        title=title or "Hermes",
        body=message,
        data=data or {},
    )
    db.add(notification)
    await db.commit()


async def send_sms(phone: str, message: str):
    """Send SMS via MSG91. Stubbed — configure MSG91_AUTH_KEY to activate."""
    if not settings.MSG91_AUTH_KEY:
        print(f"[SMS stub] To {phone}: {message}")
        return

    async with httpx.AsyncClient() as client:
        await client.post(
            "https://control.msg91.com/api/v5/flow/",
            headers={"authkey": settings.MSG91_AUTH_KEY},
            json={
                "template_id": "hermes_otp",
                "short_url": "0",
                "recipients": [{"mobiles": phone, "otp": message}],
            },
        )
