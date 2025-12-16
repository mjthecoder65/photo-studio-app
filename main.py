import uvicorn
from fastapi import FastAPI

from configs.settings import settings
from configs.tracing import setup_tracing
from routers.ai_photos import router as ai_photos_router
from routers.albums import router as albums_router
from routers.auth import router as auth_router
from routers.healthy import router as healthy_router
from routers.photos import router as photos_router
from routers.users import router as user_router

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

setup_tracing(
    app=app,
    project_id=settings.GCS_PROJECT_ID,
    enable_tracing=settings.ENABLE_TRACING,
)

app.include_router(healthy_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(photos_router)
app.include_router(albums_router)
app.include_router(ai_photos_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
