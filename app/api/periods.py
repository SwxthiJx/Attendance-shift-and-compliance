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
    try:
        from app.db.session import engine, Base
        Base.metadata.create_all(bind=engine)


    # Clean DB tables for pure benchmark comparison
    try:
        db.query(ExceptionRecord).delete(synchronize_session=False)
        db.query(ComplianceFlag).delete(synchronize_session=False)
        db.query(PayableResult).delete(synchronize_session=False)
        db.query(Punch).delete(synchronize_session=False)
        db.query(ShiftRoster).delete(synchronize_session=False)
        db.query(ApprovedLeave).delete(synchronize_session=False)
        db.query(OvertimeApproval).delete(synchronize_session=False)
        db.query(Worker).delete(synchronize_session=False)
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Cleanup note: {exc}")



    generator = SyntheticDataGenerator(seed=seed, num_workers=num_workers)
    data = generator.generate()

    # Ingest Workers
    worker_map = {}
    for w in data["workers"]:
        db_w = db.query(Worker).filter(Worker.worker_code == w["worker_code"]).first()
        if not db_w:
            db_w = Worker(worker_code=w["worker_code"], name=w["name"], department=w["department"])
            db.add(db_w)
            db.flush()
        worker_map[w["id"]] = db_w.id

    # Ingest Rosters
    for r in data["rosters"]:
        w_id = worker_map.get(r["worker_id"], r["worker_id"])
        db.add(ShiftRoster(
            worker_id=w_id,
            work_date=r["work_date"],
            start_time=r["start_time"],
            end_time=r["end_time"],
            break_minutes=r.get("break_minutes", 0)
        ))

    # Ingest Punches
    for p in data["punches"]:
        w_id = worker_map.get(p["worker_id"], p["worker_id"])
        db.add(Punch(
            worker_id=w_id,
            punch_timestamp=p["punch_timestamp"],
            punch_type=p["punch_type"],
            raw_device_id=p.get("raw_device_id", "BIOMETRIC_01")
        ))

    # Ingest Leaves
    for l in data["leaves"]:
        w_id = worker_map.get(l["worker_id"], l["worker_id"])
        db.add(ApprovedLeave(
            worker_id=w_id,
            leave_date=l["leave_date"],
            leave_type=l.get("leave_type", "PAID_LEAVE")
        ))

    # Ingest Overtimes
    for o in data["overtimes"]:
        w_id = worker_map.get(o["worker_id"], o["worker_id"])
        db.add(OvertimeApproval(
            worker_id=w_id,
            work_date=o["work_date"],
            approved_hours=o["approved_hours"],
            reason=o.get("reason", "Approved Overtime")
        ))

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
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Data generation/ingestion error: {err}")

