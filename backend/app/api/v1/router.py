from fastapi import APIRouter

from app.api.v1.routes import admin_auth, admin_directory, auth, claims, config_admin, config_secrets, config_settings, household, invites, notifications, org, receipts, upload_sessions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(admin_auth.router)
api_router.include_router(admin_directory.router)
api_router.include_router(claims.router)
api_router.include_router(household.router)
api_router.include_router(notifications.router)
api_router.include_router(receipts.router)
api_router.include_router(upload_sessions.router)
api_router.include_router(config_secrets.router)
api_router.include_router(config_settings.router)
api_router.include_router(config_admin.router)
api_router.include_router(org.router)
api_router.include_router(invites.router)
