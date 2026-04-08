from fastapi import APIRouter

from app.api.routes import logs, nodes

api_router = APIRouter()
api_router.include_router(nodes.router)
api_router.include_router(logs.router)
