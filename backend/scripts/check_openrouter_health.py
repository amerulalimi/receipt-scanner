"""Check OpenRouter credentials and API health (no secrets printed)."""
import asyncio

import httpx
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.receipt import Receipt
from app.services.job_queue import get_openrouter_credentials


async def main() -> None:
    async with AsyncSessionLocal() as db:
        creds = await get_openrouter_credentials(db)
        if not creds:
            print("OPENROUTER: NOT_CONFIGURED")
            return

        api_key, model = creds
        print(f"OPENROUTER: key_len={len(api_key)} model={model}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            auth_resp = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            print(f"AUTH_KEY status={auth_resp.status_code}")
            if auth_resp.status_code == 200:
                data = auth_resp.json().get("data", {})
                print(f"AUTH_KEY label={data.get('label')} limit={data.get('limit')}")

            chat_resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Reply with OK only."}],
                    "max_tokens": 5,
                },
            )
            print(f"CHAT status={chat_resp.status_code}")
            if chat_resp.status_code != 200:
                print(f"CHAT error={chat_resp.text[:200]}")

        rows = await db.execute(
            select(
                Receipt.merchant_name,
                Receipt.category,
                Receipt.status,
                Receipt.claimed_amount,
            )
            .where(Receipt.deleted_at.is_(None))
            .order_by(Receipt.created_at.desc())
            .limit(5),
        )
        print("RECENT_RECEIPTS:")
        for row in rows:
            print(" ", row)


if __name__ == "__main__":
    asyncio.run(main())
