"""
Database setup and models for MySQL persistence.
"""

from datetime import datetime
import os

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "hold_analyzor")
DB_USER = os.getenv("DB_USER", "hold_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    symbols = Column(String(500), nullable=False)
    monthly_amount = Column(Float, nullable=False)
    months = Column(Integer, nullable=False)
    strategy_profile = Column(String(32), nullable=False)
    allocation_mode = Column(String(32), nullable=False)
    summary = Column(JSON, nullable=True)
    results = Column(JSON, nullable=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
