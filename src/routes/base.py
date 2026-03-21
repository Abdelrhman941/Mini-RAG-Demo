from datetime import UTC, datetime
from fastapi import APIRouter, Depends, Request
from ..core import Settings, get_settings
from ..models import ResponseSignal as RS

base_router = APIRouter(prefix="/v1", tags=["base"])


@base_router.get("/")
async def read_root(appSettings: Settings = Depends(get_settings)):
    return {
        "APP": appSettings.APP_NAME,
        "VERSION": appSettings.APP_VERSION,
        "DESCRIPTION": appSettings.APP_DESCRIPTION,
    }


@base_router.get("/health")
async def health_check(request: Request, appSettings: Settings = Depends(get_settings)):
    try:
        await request.app.mongo_conn.admin.command('ping')
        db_status = RS.STATUS_HEALTHY.value
    except Exception:
        db_status = RS.STATUS_UNHEALTHY.value

    return {
        "status": db_status,
        "environment": appSettings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    }
