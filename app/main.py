from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title="Attendance & Shift Compliance Service",
    description="""
A production-grade backend service for ingesting biometric punch logs, shift rosters, approved leave,
and overtime approvals to reconcile payable hours, enforce compliance rules, and detect operational exceptions.

### Key Features:
* **Deduplication**: Sliding window deduplication of duplicate punches.
* **Overnight Shift Handling**: Correctly attributes shifts crossing midnight to rostered work dates.
* **Missing Punch Policy**: Never invents punches. Missing punches create exceptions and hold payable hours.
* **Compliance Engine**: Configurable enforcement of continuous shift limits (Rule 1) and consecutive work days (Rule 2).
* **Idempotent Processing**: Re-runnable pay period processing.
* **Ground-Truth Validation**: Automated comparison against simulated ground-truth expectations.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.db.session import engine, Base
from app.models import worker, roster, punch, leave, overtime, result, exception, flag

# Ensure DB tables are created immediately when app starts
try:
    Base.metadata.create_all(bind=engine)
except Exception as err:
    print(f"DB Table Creation Warning: {err}")

app.include_router(api_router)



@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "service": "Attendance & Shift Compliance Backend",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "environment": settings.ENVIRONMENT
    }

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

