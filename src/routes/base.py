from datetime import UTC, datetime
from fastapi import APIRouter, Depends
from ..core import Settings, get_settings
from ..models import ResponseSignal as RS

base_router = APIRouter(prefix="/v1", tags=["base"])


@base_router.get("/")
async def read_root(appsSettings: Settings = Depends(get_settings)):
    return {
        "APP": appsSettings.APP_NAME,
        "VERSION": appsSettings.APP_VERSION,
        "DESCRIPTION": appsSettings.APP_DESCRIPTION,
    }


@base_router.get("/health")
async def health_check(appsSettings: Settings = Depends(get_settings)):
    response = {
        "status": RS.STATUS_HEALTHY.value,
        "environment": appsSettings.ENVIRONMENT,
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    return response
