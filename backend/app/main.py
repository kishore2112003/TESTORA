from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import attachments, auth, cases, sessions

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

# Include Routers (versioned under /api/v1)
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}/sessions", tags=["sessions"])
app.include_router(cases.router, prefix=f"{settings.API_V1_STR}/cases", tags=["cases"])
app.include_router(attachments.router, prefix=f"{settings.API_V1_STR}/attachments", tags=["attachments"])


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
