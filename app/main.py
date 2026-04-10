from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.router import api_router
from app.config import settings
from app.core.database import init_db
from app.core.logger import setup_logging
from app.services.scheduler import start_scheduler, stop_scheduler

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database...")
    await init_db()
    logger.success("Database ready.")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(api_router)
