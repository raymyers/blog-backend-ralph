from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from app.deps import get_engine
from app.routes import articles, auth, comments, profiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(title="RealWorld Conduit", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return detail directly so routes can shape the error body themselves."""
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"errors": {"body": ["Invalid request"]}})


app.include_router(auth.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(comments.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
