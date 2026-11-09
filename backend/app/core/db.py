from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from app.core.config import Settings

'''
Create a database engine from the given settings.
'''
def create_db_engine(settings: Settings) -> Engine:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: FastAPI may use the connection from different threads.
    return create_engine(settings.db_url, connect_args={"check_same_thread": False})

'''
Initialize the database with the given engine.
'''
def init_db(engine: Engine) -> None:
    # Importing the models registers their tables in SQLModel.metadata. (import app.models)
    # No migrations yet: create_all only adds missing tables. Introduce Alembic once
    # the schema needs to change on a deployed database.
    import app.models  # noqa: F401 

    SQLModel.metadata.create_all(engine)
