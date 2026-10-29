from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth

app = FastAPI(
    title=settings.APP_NAME + " API",
    description="Test Case Management System Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Authentication Router
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth-v1"])


@app.get("/", tags=["system"])
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "message": f"Welcome to {settings.APP_NAME} Test Case Management API",
    }


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy"}
