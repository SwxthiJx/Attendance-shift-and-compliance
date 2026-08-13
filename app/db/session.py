from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Connect args for SQLite compatibility
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

import os
os.makedirs("/tmp", exist_ok=True)

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False
    )
except Exception as err:
    print(f"Database Engine Fallback Warning: {err}")
    engine = create_engine(
        "sqlite:////tmp/attendance.db",
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

