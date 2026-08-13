from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

from sqlalchemy.pool import StaticPool

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
pool_kwargs = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if ":memory:" in db_url or db_url == "sqlite://":
        pool_kwargs["poolclass"] = StaticPool

from sqlalchemy import text

try:
    engine = create_engine(db_url, connect_args=connect_args, echo=False)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS _health_check_write (id INT)"))
        conn.execute(text("DROP TABLE _health_check_write"))
except Exception as err:
    print(f"Cloud DB Connection/Write Warning ({err}). Falling back to SQLite /tmp/attendance.db")
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

