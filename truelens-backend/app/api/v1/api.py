from fastapi import APIRouter
from app.api.v1.endpoints import scans, documents

api_router = APIRouter()
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
