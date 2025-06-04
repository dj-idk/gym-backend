from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette_csrf import CSRFMiddleware

from src.middleware import RequestLoggingMiddleware
from src.utils import setup_limiter, setup_exception_handlers
from src.data import (
    init_db,
    close_db_connection,
    Base,
    init_roles_and_permissions,
    get_db_context,
)
from src.config import settings

from .auth import router as auth_router
from .profile import router as profile_router
from .user import router as user_router

# CORS Variable configuration
cors_origins = (
    settings.CORS_ALLOW_ORIGINS.split(",") if settings.CORS_ALLOW_ORIGINS else ["*"]
)
cors_methods = (
    settings.CORS_ALLOW_METHODS.split(",") if settings.CORS_ALLOW_METHODS else ["*"]
)
cors_headers = (
    settings.CORS_ALLOW_HEADERS.split(",") if settings.CORS_ALLOW_HEADERS else ["*"]
)
cors_credentials = settings.CORS_ALLOW_CREDENTIALS.lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    async with get_db_context() as session:
        await init_roles_and_permissions(session)

    yield

    await close_db_connection()


app = FastAPI(
    title=settings.SERVER_NAME,
    version="1.0.0",
    lifespan=lifespan,
    root_path=settings.API_V1_STR,
)

setup_exception_handlers(app)
setup_limiter(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)
app.add_middleware(
    CSRFMiddleware,
    secret=settings.CSRF_TOKEN_SECRET,
    sensitive_cookies="Authorization",
    cookie_domain=settings.CSRF_COOKIE_DOMAIN,
)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/")
async def root():
    return {"message": "Welcome to Gym Backend API", "docs": "/docs"}


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(user_router)
