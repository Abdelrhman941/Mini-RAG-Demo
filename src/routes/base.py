from fastapi import APIRouter, Depends
from core.configs import Settings, get_settings

base_router = APIRouter(prefix="/v1", tags=["base"])

@base_router.get("/")
async def read_root(appsSettings: Settings = Depends(get_settings)):
    return {
        "APP": appsSettings.APP_NAME,
        "VERSION": appsSettings.APP_VERSION,
        "DESCRIPTION": appsSettings.APP_DESCRIPTION,
    }
