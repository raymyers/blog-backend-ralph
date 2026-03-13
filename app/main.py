"""FastAPI application main module."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.routes.auth import router as auth_router
from app.routes.articles import router as articles_router, tags_router
from app.routes.profiles import router as profiles_router
from app.routes.comments import router as comments_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    create_db_and_tables()
    yield
    # Shutdown


app = FastAPI(
    title="blog-backend-ralph",
    description="A FastAPI backend for the RealWorld Conduit API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(tags_router)
app.include_router(profiles_router)
app.include_router(comments_router)


@app.get("/")
async def root():
    return {"message": "Welcome to blog-backend-ralph API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
