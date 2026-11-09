"""FastAPI dependencies shared by all routers."""

from collections.abc import Iterator

from fastapi import Request
from sqlmodel import Session

from app.core.config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
