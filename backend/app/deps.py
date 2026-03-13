"""Dependency injection wiring for FastAPI routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, SQLModel, create_engine

from app.adapters.database import (
    SQLArticleRepository,
    SQLCommentRepository,
    SQLFollowRepository,
    SQLUserRepository,
)
from app.adapters.password import BcryptPasswordHasher
from app.adapters.token import JWTTokenService
from app.config import get_settings
from app.domain.models import User
from app.use_cases.article_service import ArticleService
from app.use_cases.comment_service import CommentService
from app.use_cases.errors import InvalidCredentialsError
from app.use_cases.profile_service import ProfileService
from app.use_cases.user_service import UserService

_engine = None
_test_engine = None  # set by tests to bypass the real database


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(_engine)
    return _engine


def get_session() -> Session:  # type: ignore[return]
    engine = _test_engine if _test_engine is not None else get_engine()
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_user_service(session: SessionDep) -> UserService:
    settings = get_settings()
    return UserService(
        SQLUserRepository(session),
        BcryptPasswordHasher(),
        JWTTokenService(settings),
    )


def get_article_service(session: SessionDep) -> ArticleService:
    return ArticleService(
        SQLArticleRepository(session),
        SQLUserRepository(session),
        SQLFollowRepository(session),
    )


def get_profile_service(session: SessionDep) -> ProfileService:
    return ProfileService(SQLUserRepository(session), SQLFollowRepository(session))


def get_comment_service(session: SessionDep) -> CommentService:
    return CommentService(SQLCommentRepository(session), SQLArticleRepository(session))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ArticleServiceDep = Annotated[ArticleService, Depends(get_article_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]


def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Token "):
        return auth[6:]
    return None


def get_optional_user_id(request: Request) -> int | None:
    token = _extract_token(request)
    if token is None:
        return None
    settings = get_settings()
    return JWTTokenService(settings).decode(token)


def require_user_id(request: Request) -> int:
    token = _extract_token(request)
    if token is None:
        raise HTTPException(
            status_code=401,
            detail={"errors": {"token": ["is missing"]}},
        )
    settings = get_settings()
    user_id = JWTTokenService(settings).decode(token)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail={"errors": {"token": ["is invalid"]}},
        )
    return user_id


OptionalUserIdDep = Annotated[int | None, Depends(get_optional_user_id)]
RequiredUserIdDep = Annotated[int, Depends(require_user_id)]
