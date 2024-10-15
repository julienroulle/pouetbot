from sqlmodel import Field, Session, SQLModel, create_engine
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


class PushUpLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    pushups: int
    timestamp: datetime = Field(default_factory=datetime.now)


class UserTotal(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    total_pushups: int = Field(default=0)


engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
