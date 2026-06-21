"""Promote a user to superadmin by email."""

from __future__ import annotations

import asyncio
import sys

from app.core.database import AsyncSessionLocal
from app.repositories.user import UserRepository


async def promote(email: str) -> None:
    normalized = email.strip().lower()
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_email(normalized)
        if user is None:
            print(f"User not found: {normalized}")
            sys.exit(1)

        if user.role == "superadmin":
            print(f"User already superadmin: {normalized}")
            return

        await repo.update_role(user.id, "superadmin")
        await session.commit()
        print(f"Promoted to superadmin: {normalized}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.promote_superadmin user@example.com")
        sys.exit(1)

    asyncio.run(promote(sys.argv[1]))


if __name__ == "__main__":
    main()
