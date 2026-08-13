from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.db.session import get_db
from app.schemas.period import ProcessPeriodRequest, PeriodProcessSummary
from app.services.period_processor import PayPeriodProcessor
from app.services.generator import SyntheticDataGenerator
from app.models.worker import Worker
from app.models.roster import ShiftRoster
from app.models.punch import Punch
from app.models.leave import ApprovedLeave
from app.models.overtime import OvertimeApproval
from app.models.result import PayableResult
from app.models.exception import ExceptionRecord
from app.models.flag import ComplianceFlag


from app.services.custom_ingestor import ingest_custom_dataset

router = APIRouter(prefix="/periods", tags=["Pay Period Processing"])

@router.post("/ingest-custom-and-process", status_code=status.HTTP_201_CREATED)
def ingest_custom_and_process_pay_period(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Ingest any custom employee punch dataset JSON and process pay period immediately.
    """
    pay_period_id = payload.get("pay_period_id", "CUSTOM_PERIOD")
    counts = ingest_custom_dataset(db, payload)
    
    processor = PayPeriodProcessor(db)
    summary = processor.process_period(pay_period_id=pay_period_id)
    summary["ingested_counts"] = counts
    return summary


@router.post("/{period_id}/process", response_model=PeriodProcessSummary)
def process_pay_period(
    period_id: str,
    payload: Optional[ProcessPeriodRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Process a complete pay period idempotently.
    Executes deduplication, attendance reconciliation, payable hours calculation,
    overtime reconciliation, compliance engine evaluation, and stores results.
    """
    start_date = payload.start_date if payload else None
    end_date = payload.end_date if payload else None

    processor = PayPeriodProcessor(db)
    summary = processor.process_period(pay_period_id=period_id, start_date=start_date, end_date=end_date)
    return summary

@router.post("/generate-and-ingest", status_code=status.HTTP_201_CREATED)
def generate_and_ingest_synthetic_data(
    seed: int = Query(42, description="Random seed for reproducible dataset"),
    num_workers: int = Query(10, description="Number of workers to simulate"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Helper endpoint: Generates synthetic dataset (with ground truth anomalies)
    and ingests all four sources into PostgreSQL/SQLite database.
    """
    # Clean DB tables for pure benchmark comparison
    db.query(ExceptionRecord).delete()
    db.query(ComplianceFlag).delete()
    db.query(PayableResult).delete()
    db.query(Punch).delete()
    db.query(ShiftRoster).delete()
    db.query(ApprovedLeave).delete()
    db.query(OvertimeApproval).delete()
    db.query(Worker).delete()
    db.commit()

    generator = SyntheticDataGenerator(seed=seed, num_workers=num_workers)
    data = generator.generate()

    # Ingest Workers
    for w in data["workers"]:
        db.add(Worker(id=w["id"], worker_code=w["worker_code"], name=w["name"], department=w["department"]))
    db.flush()

    # Ingest Rosters
    for r in data["rosters"]:
        db.add(ShiftRoster(**r))

    # Ingest Punches
    for p in data["punches"]:
        db.add(Punch(**p))

    # Ingest Leaves
    for l in data["leaves"]:
        db.add(ApprovedLeave(**l))

    # Ingest Overtimes
    for o in data["overtimes"]:
        db.add(OvertimeApproval(**o))

    db.commit()


    return {
        "message": "Synthetic dataset generated and ingested successfully",
        "seed": seed,
        "counts": {
            "workers": len(data["workers"]),
            "rosters": len(data["rosters"]),
            "punches": len(data["punches"]),
            "leaves": len(data["leaves"]),
            "overtimes": len(data["overtimes"])
        }
    }


