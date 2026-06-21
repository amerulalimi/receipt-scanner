import json
import logging
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis
from app.repositories.user import UserRepository
from app.services.session import get_session_data
from app.services.upload_session import UploadSessionService
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


async def _authenticate_websocket(websocket: WebSocket) -> uuid.UUID | None:
    session_id = websocket.cookies.get(settings.session_cookie_name)
    if not session_id:
        return None

    redis = get_redis()
    session_data = await get_session_data(redis, session_id)
    if session_data is None:
        return None

    return uuid.UUID(session_data["user_id"])


async def dashboard_websocket(websocket: WebSocket) -> None:
    user_id = await _authenticate_websocket(websocket)
    if user_id is None:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    await websocket.accept()

    subscribed_token: str | None = None

    try:
        raw = await websocket.receive_text()
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            await websocket.send_json(
                {"type": "error", "data": {"message": "Mesej JSON tidak sah."}},
            )
            await websocket.close(code=4400, reason="Invalid message")
            return

        if message.get("type") != "subscribe":
            await websocket.send_json(
                {
                    "type": "error",
                    "data": {"message": "Mesej pertama mesti subscribe."},
                },
            )
            await websocket.close(code=4400, reason="Expected subscribe")
            return

        upload_session_token = message.get("upload_session_token")
        if not upload_session_token or not isinstance(upload_session_token, str):
            await websocket.send_json(
                {
                    "type": "error",
                    "data": {"message": "upload_session_token diperlukan."},
                },
            )
            await websocket.close(code=4400, reason="Missing token")
            return

        async with AsyncSessionLocal() as db:
            user = await UserRepository(db).get_by_id(user_id)
            if user is None or not user.is_active:
                await websocket.close(code=4401, reason="Unauthorized")
                return

            service = UploadSessionService(db)
            await service.assert_user_owns_session(user, upload_session_token)

        subscribed_token = upload_session_token
        await ws_manager.subscribe(subscribed_token, websocket)
        await websocket.send_json(
            {"type": "subscribed", "data": {"upload_session_token": subscribed_token}},
        )

        while websocket.client_state == WebSocketState.CONNECTED:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WebSocket error for user %s", user_id)
    finally:
        if subscribed_token is not None:
            await ws_manager.unsubscribe(subscribed_token, websocket)
