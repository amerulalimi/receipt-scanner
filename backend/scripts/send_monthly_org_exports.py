"""Send monthly org payroll CSV exports (run via cron on 1st of month)."""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.organisation import Organisation
from app.services.email import send_org_export_email
from app.services.export import ExportService

logger = logging.getLogger(__name__)


async def main() -> None:
    tax_year = datetime.now().year
    async with async_session_factory() as db:
        result = await db.execute(
            select(Organisation).where(Organisation.status == "active"),
        )
        organisations = list(result.scalars().all())
        export = ExportService(db)
        sent = 0

        for org in organisations:
            try:
                content, filename = await export.build_org_payroll_csv(
                    org.id,
                    tax_year=tax_year,
                    template="generic",
                )
            except Exception:
                logger.info("Skip org %s — no approved claims", org.id)
                continue

            await send_org_export_email(
                org_name=org.name,
                filename=filename,
                csv_content=content,
            )
            sent += 1

        await db.commit()
        logger.info("Sent %s org payroll exports for tax year %s", sent, tax_year)


if __name__ == "__main__":
    asyncio.run(main())
