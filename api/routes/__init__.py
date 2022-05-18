from fastapi import APIRouter

from api.routes.views import router as ws_router

router = APIRouter()


router.include_router(ws_router, prefix="/api", tags=["views"])
