import os
from sqlmodel import SQLModel, create_engine, Session

DB_PATH = os.environ.get("VISIONQC_DB", os.path.join(os.path.dirname(__file__), "..", "..", "data", "visionqc.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
