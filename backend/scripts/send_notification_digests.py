"""Send monthly digest emails and reminder emails for due users."""

import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.repositories.user import UserRepository
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


async def run_digest_job() -> None:
    async with AsyncSessionLocal() as db:
        service = NotificationService(db)
        digest_count = await service.send_due_monthly_digests()

        users = await UserRepository(db).list_active_verified()
        reminder_count = 0
        for user in users:
            reminder_count += await service.send_email_for_active_reminders(user)

        await db.commit()
        logger.info(
            "Notification job complete — %s digests, %s reminder emails",
            digest_count,
            reminder_count,
        )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run_digest_job())


if __name__ == "__main__":
    main()
