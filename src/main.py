import uvicorn
import logging
from fastapi import FastAPI
from .routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from .models import ResponseSignal as RS
from .core import get_settings

logger = logging.getLogger("uvicorn.error")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
        app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]
        await app.mongo_conn.admin.command('ping')
        logger.info(f"✅ {RS.DB_CONNECTION_SUCCESS.value}")
    except Exception as e:
        logger.error(f"❌ {RS.DB_CONNECTION_FAILED.value}: {e}")
        raise
    yield
    app.mongo_conn.close()


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
)
app.include_router(base.base_router)
app.include_router(data.data_router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
