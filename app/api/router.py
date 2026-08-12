from fastapi import APIRouter
from app.api import ingest, periods, results

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ingest.router)
api_router.include_router(periods.router)
api_router.include_router(results.router)
