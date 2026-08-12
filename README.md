<<<<<<< HEAD
# Attendance & Shift Compliance

A backend service that reconciles biometric punches, shift rosters, approved leave, and overtime approvals to calculate payable hours per worker per day and surface attendance/compliance issues for review.

## 1. Problem Overview

The four sources belong to the same facilities company but may disagree. The system reconciles them instead of relying on a single source.

The project uses **simulated data**. A known-correct set of shifts is generated first, then biometric punch data is generated from it with controlled errors such as missing and duplicate punches. This provides ground truth for validation.

## 2. Inputs

| Source             | Purpose                  |
| ------------------ | ------------------------ |
| Biometric punches  | Actual IN/OUT events     |
| Shift roster       | Scheduled working shifts |
| Approved leave     | Approved absences        |
| Overtime approvals | Pre-approved overtime    |

## 3. Key Assumptions

* A missing punch does **not** mean the worker worked until midnight.
* The rostered shift length is not blindly used when attendance is incomplete.
* An unresolved missing IN/OUT punch becomes an **exception** rather than an estimated payable period.
* Punches occurring seconds apart are treated as duplicates using a configurable threshold.
* Overtime is checked against both actual punches and approval records.
* Overtime worked without approval is surfaced rather than silently paid or dropped.
* Overnight shifts are attributed to their roster/work date.
* Only the two supplied compliance rules are applied:

  * Shift > 10 continuous hours
  * More than 6 consecutive working days
* Compliance thresholds are configuration-driven.

## 4. Output

For each worker and work date, the service produces:

* Payable hours
* Compliance flags
* Exceptions requiring review

A **flag** means the payable hours can still be determined but an issue should be surfaced.

An **exception** means the payable hours cannot be safely determined and should not be automatically paid.

## 5. Ground-Truth Validation

The generated correct shifts act as ground truth.

```text
Correct shifts
     ↓
Generate punches
     ↓
Inject errors
     ↓
Reconciliation
     ↓
Compare with ground truth
```

This allows the correctness of the reconciliation logic to be measured.

## 6. Technology

* Python
* FastAPI
* REST API
* PostgreSQL
* SQLAlchemy
* Alembic
* Pytest

## 7. Setup & Run

### Prerequisites

* Python 3.11+
* PostgreSQL
* pip

### Install

```bash
git clone <repository-url>
cd attendance-shift-compliance

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Configure

Create `.env` from `.env.example` and provide the PostgreSQL connection:

```text
DATABASE_URL=postgresql://user:password@localhost/attendance_db
```

### Initialize database

=======
# Attendance & Shift Compliance Backend

Production-grade backend service built with Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Pydantic v2, and Pytest.

This service ingests biometric punch logs, shift rosters, approved leave records, and overtime approvals to calculate payable hours per worker per day, enforce compliance rules, and detect operational exceptions.

---

## Technical Stack

- **Framework**: FastAPI (Async & Sync OpenAPI REST endpoints)
- **Database**: PostgreSQL (Production DB) / SQLite (Zero-dependency Local Development)
- **ORM & Migrations**: SQLAlchemy v2 & Alembic
- **Validation & Schemas**: Pydantic v2 & Pydantic Settings
- **Testing**: Pytest & FastAPI TestClient

---

## Quick Start & Setup Instructions

### 1. Clone & Workspace Setup
Recommend setting the root project directory as your workspace:
```bash
cd /Users/swathijayadevan06/.gemini/antigravity-ide/scratch/attendance_compliance_service
```

### 2. Environment & Dependency Installation
Create virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

### 3. Database Migration
Run database migrations using Alembic:
>>>>>>> 45985de (docs(architecture): Add technical design docs, API spec, test plan, and execution demo script)
```bash
alembic upgrade head
```

<<<<<<< HEAD
### Generate simulated data

```bash
python scripts/generate_data.py
```

### Start API

```bash
uvicorn app.main:app --reload
```

API documentation is available through FastAPI's generated `/docs` endpoint.

### Run tests

```bash
pytest
```

> Update commands if the final repository structure differs.

## 8. Scope Limits

The following are intentionally excluded:

| Excluded                                | Why                                             |
| --------------------------------------- | ----------------------------------------------- |
| Real biometric/HR integrations          | Sources are simulated by requirement            |
| Frontend / approval UI                  | Explicitly outside project scope                |
| Payroll payment processing              | The service calculates hours only               |
| Labour-law research                     | Only the supplied compliance rules are required |
| Automatic exception approval/resolution | Uncertain data must be surfaced for review      |




=======
### 4. Run Automated Test Suite
Run the full 13-scenario test suite including unit, integration, idempotency, and ground-truth validation:
```bash
python3 -m pytest -v
```

### 5. Run End-to-End Demo Script
Execute the complete end-to-end demo flow (generation -> ingestion -> period processing -> results retrieval -> exceptions review -> ground truth verification):
```bash
python3 scripts/run_demo.py
```

### 6. Launch API Server & Interactive Docs
Start the Uvicorn web server:
```bash
uvicorn app.main:app --reload --port 8000
```
Open your browser to:
- **Swagger Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Key Assumptions & Scope Limits

1. **Missing Punch Policy**:
   Missing IN or OUT punches render interval durations uncertain. The system **never** invents punch timestamps or assumes rostered shift durations. Unverified intervals create a high-severity `Exception` (`MISSING_IN` / `MISSING_OUT`) and set `payable_hours = 0.0` until supervisor review.

2. **Compliance Enforcement Scope**:
   Strictly implements ONLY the two specified compliance rules:
   - **Rule 1**: Flag continuous shifts exceeding `MAX_CONTINUOUS_SHIFT_HOURS` (Default: 10.0 hours).
   - **Rule 2**: Flag workers exceeding `MAX_CONSECUTIVE_WORKING_DAYS` (Default: 6 consecutive days).
   Labour law extensions or complex overtime rate tiers were intentionally excluded per the project specification.

3. **Frontend & Supervisor Approval UI**:
   No UI is included. Demonstration and evaluation are performed entirely via REST endpoints, automated Pytest suite, and Swagger `/docs`.

4. **Re-runnable Processing**:
   Processing a pay period is fully idempotent. Re-executing `POST /api/v1/periods/{period_id}/process` deletes previous period results and recomputes without creating duplicate records.

---

## Project Structure

```text
attendance_compliance_service/
├── alembic/              # Database migration scripts & env setup
├── app/
│   ├── api/              # REST API controllers (ingest, periods, results)
│   ├── core/             # Configuration settings & environment variables
│   ├── db/               # SQLAlchemy engine & session management
│   ├── models/           # SQLAlchemy ORM models (Worker, Roster, Punch, etc.)
│   ├── schemas/          # Pydantic v2 schemas for API contracts
│   ├── services/         # Core business services (Deduplication, Reconciliation, Compliance, Generator)
│   └── main.py           # FastAPI application entry point
├── docs/
│   ├── DESIGN.md         # Architecture, design trade-offs, and Mermaid diagrams
│   ├── API.md            # Comprehensive API specification & examples
│   └── TEST_PLAN.md      # Testing strategy & ground-truth validation plan
├── scripts/
│   └── run_demo.py       # End-to-end executable demo script
├── tests/                # Complete Pytest automated test suite
├── .env.example          # Environment configuration defaults
├── alembic.ini           # Alembic migration configuration
├── pyproject.toml        # Project setup & dependency manifest
└── README.md             # Project overview & quick start guide
```
>>>>>>> 45985de (docs(architecture): Add technical design docs, API spec, test plan, and execution demo script)
