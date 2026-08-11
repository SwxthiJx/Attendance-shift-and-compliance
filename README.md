# Attendance-shift-and-compliance
### README.md

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

```bash
alembic upgrade head
```

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

## 9. Documentation

See [`docs/DESIGN.md`](docs/DESIGN.md) for the architecture, design choices, and trade-offs.



