"""FastAPI application main module."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import ValidationError as PydanticValidationError
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import create_db_and_tables
from app.routes.auth import router as auth_router
from app.routes.articles import router as articles_router, tags_router
from app.routes.profiles import router as profiles_router
from app.routes.comments import router as comments_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="blog-backend-ralph",
    description="A FastAPI backend for the RealWorld Conduit API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Map Pydantic validation errors to RealWorld API error format."""
    errors = {}
    for error in exc.errors():
        loc = error.get("loc", [])
        # Field name is the last non-"body" element
        field = str(loc[-1]) if loc else "body"
        msg_raw = error.get("msg", "is invalid")
        # Pydantic v2 prefixes custom messages with "Value error, "
        if msg_raw.startswith("Value error, "):
            msg = msg_raw[len("Value error, "):]
        elif error.get("type") in ("string_too_short", "missing"):
            msg = "can't be blank"
        else:
            msg = msg_raw
        if field not in errors:
            errors[field] = []
        errors[field].append(msg)
    return JSONResponse(status_code=422, content={"errors": errors})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return HTTPException detail directly when it contains an errors dict."""
    if isinstance(exc.detail, dict) and "errors" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"errors": {"body": [str(exc.detail)]}})


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_handler(request: Request, exc: PydanticValidationError):
    """Handle Pydantic ValidationError raised manually inside endpoints."""
    errors = {}
    for error in exc.errors():
        loc = error.get("loc", [])
        field = str(loc[-1]) if loc else "body"
        msg_raw = error.get("msg", "is invalid")
        if msg_raw.startswith("Value error, "):
            msg = msg_raw[len("Value error, "):]
        elif error.get("type") in ("string_too_short", "missing"):
            msg = "can't be blank"
        else:
            msg = msg_raw
        if field not in errors:
            errors[field] = []
        errors[field].append(msg)
    return JSONResponse(status_code=422, content={"errors": errors})


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
