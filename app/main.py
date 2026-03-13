from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.database import create_db_and_tables
from app.routes.articles import router as articles_router, tags_router
from app.routes.auth import router as auth_router
from app.routes.comments import router as comments_router
from app.routes.profiles import router as profiles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="blog-backend-ralph", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _pydantic_errors_to_dict(errors: list) -> dict:
    result: dict = {}
    for error in errors:
        loc = error.get("loc", [])
        field = str(loc[-1]) if loc else "body"
        msg = error.get("msg", "is invalid")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        elif error.get("type") in ("string_too_short", "missing"):
            msg = "can't be blank"
        result.setdefault(field, []).append(msg)
    return result


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"errors": _pydantic_errors_to_dict(exc.errors())})


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_handler(request: Request, exc: PydanticValidationError):
    return JSONResponse(status_code=422, content={"errors": _pydantic_errors_to_dict(exc.errors())})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "errors" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"errors": {"body": [str(exc.detail)]}})


app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(tags_router)
app.include_router(profiles_router)
app.include_router(comments_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
