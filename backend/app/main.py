"""FastAPI entry point. Run locally with: uvicorn app.main:app --reload"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session

from app.core.config import Settings
from app.core.db import create_db_engine, init_db
from app.routers import health, testcases
from app.services.seed import seed_dataset

logging.basicConfig(level=logging.INFO)

'''
FastAPI entry point. Run locally with: uvicorn app.main:app --reload
Creates lifespan context to initialize the database and seed the dataset before the first request.
Lifespan also disposes the database engine after the last request.

Creation either with or without a Settings object. If no Settings object is provided, it is created from environment variables.

Creates data path and upload path if they do not exist yet. The upload path is used to store uploaded files, the data path is used to store the database and the dataset.

'''
def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    '''
    Start- and Shutdown-logic 
    '''
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings)
        init_db(engine)
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        with Session(engine) as session: # opens db session and closes it at the end of this block
            seed_dataset(session, settings.dataset_dir) # loads startup data from dataset to the db
        app.state.engine = engine
        yield # before yield is run at startup after yield is run at shutdown
        engine.dispose()

    '''
    Creates a FastAPI Instance 
    '''
    app = FastAPI(
        title="VLM Animation Check API",
        version="0.1.0",
        lifespan=lifespan,
        # Everything lives under /api so the frontend proxy only needs one rule.
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.settings = settings
    app.include_router(health.router)
    app.include_router(testcases.router)
    return app


app = create_app() # starts the concrete instance at uvicorn
