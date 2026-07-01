"""Create a platform admin account."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis
from app.services.admin_auth import AdminAuthService


async def create_admin(email: str, full_name: str | None, password: str) -> None:
    async with AsyncSessionLocal() as session:
        service = AdminAuthService(session, get_redis())
        admin = await service.create_admin(
            email=email,
            password=password,
            full_name=full_name,
        )
        await session.commit()
        print(f"Platform admin created: {admin.email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a platform admin account")
    parser.add_argument("email", help="Admin email address")
    parser.add_argument("full_name", nargs="?", default=None, help="Display name")
    parser.add_argument(
        "--password",
        help="Admin password (prompted securely if omitted)",
    )
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    asyncio.run(create_admin(args.email, args.full_name, password))


if __name__ == "__main__":
    main()
