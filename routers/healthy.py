from fastapi import APIRouter

from configs.settings import settings

router = APIRouter(prefix=f"/api/{settings.APP_VERSION}/healthy", tags=["Healthy"])


@router.get("")
async def healthy_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
