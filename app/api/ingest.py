from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.worker import Worker
from app.models.roster import ShiftRoster
from app.models.punch import Punch
from app.models.leave import ApprovedLeave
from app.models.overtime import OvertimeApproval
from app.schemas import (
    WorkerCreate, WorkerResponse,
    ShiftRosterCreate, ShiftRosterResponse,
    PunchCreate, PunchResponse,
    ApprovedLeaveCreate, ApprovedLeaveResponse,
    OvertimeApprovalCreate, OvertimeApprovalResponse
)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post("/workers", response_model=List[WorkerResponse], status_code=status.HTTP_201_CREATED)
def ingest_workers(workers: List[WorkerCreate], db: Session = Depends(get_db)):
    """Ingest worker profiles."""
    created_workers = []
    for w in workers:
        db_worker = db.query(Worker).filter(Worker.worker_code == w.worker_code).first()
        if not db_worker:
            db_worker = Worker(worker_code=w.worker_code, name=w.name, department=w.department)
            db.add(db_worker)
            db.flush()
        created_workers.append(db_worker)
    db.commit()
    for w in created_workers:
        db.refresh(w)
    return created_workers

@router.post("/shifts", response_model=List[ShiftRosterResponse], status_code=status.HTTP_201_CREATED)
def ingest_shifts(shifts: List[ShiftRosterCreate], db: Session = Depends(get_db)):
    """Ingest shift roster records."""
    created_shifts = []
    for s in shifts:
        worker = db.query(Worker).filter(Worker.id == s.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail=f"Worker ID {s.worker_id} not found")
        db_shift = ShiftRoster(
            worker_id=s.worker_id,
            work_date=s.work_date,
            start_time=s.start_time,
            end_time=s.end_time,
            break_minutes=s.break_minutes
        )
        db.add(db_shift)
        created_shifts.append(db_shift)
    db.commit()
    for s in created_shifts:
        db.refresh(s)
    return created_shifts

@router.post("/punches", response_model=List[PunchResponse], status_code=status.HTTP_201_CREATED)
def ingest_punches(punches: List[PunchCreate], db: Session = Depends(get_db)):
    """Ingest biometric punch logs."""
    created_punches = []
    for p in punches:
        worker = db.query(Worker).filter(Worker.id == p.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail=f"Worker ID {p.worker_id} not found")
        db_punch = Punch(
            worker_id=p.worker_id,
            punch_timestamp=p.punch_timestamp,
            punch_type=p.punch_type,
            raw_device_id=p.raw_device_id
        )
        db.add(db_punch)
        created_punches.append(db_punch)
    db.commit()
    for p in created_punches:
        db.refresh(p)
    return created_punches

@router.post("/leave", response_model=List[ApprovedLeaveResponse], status_code=status.HTTP_201_CREATED)
def ingest_leave(leaves: List[ApprovedLeaveCreate], db: Session = Depends(get_db)):
    """Ingest approved leave records."""
    created_leaves = []
    for l in leaves:
        worker = db.query(Worker).filter(Worker.id == l.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail=f"Worker ID {l.worker_id} not found")
        existing = db.query(ApprovedLeave).filter(
            ApprovedLeave.worker_id == l.worker_id,
            ApprovedLeave.leave_date == l.leave_date
        ).first()
        if not existing:
            db_leave = ApprovedLeave(
                worker_id=l.worker_id,
                leave_date=l.leave_date,
                leave_type=l.leave_type
            )
            db.add(db_leave)
            created_leaves.append(db_leave)
        else:
            created_leaves.append(existing)
    db.commit()
    for l in created_leaves:
        db.refresh(l)
    return created_leaves

@router.post("/overtime", response_model=List[OvertimeApprovalResponse], status_code=status.HTTP_201_CREATED)
def ingest_overtime(overtimes: List[OvertimeApprovalCreate], db: Session = Depends(get_db)):
    """Ingest overtime approval records."""
    created_overtimes = []
    for o in overtimes:
        worker = db.query(Worker).filter(Worker.id == o.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail=f"Worker ID {o.worker_id} not found")
        existing = db.query(OvertimeApproval).filter(
            OvertimeApproval.worker_id == o.worker_id,
            OvertimeApproval.work_date == o.work_date
        ).first()
        if not existing:
            db_ot = OvertimeApproval(
                worker_id=o.worker_id,
                work_date=o.work_date,
                approved_hours=o.approved_hours,
                reason=o.reason
            )
            db.add(db_ot)
            created_overtimes.append(db_ot)
        else:
            existing.approved_hours = o.approved_hours
            existing.reason = o.reason
            created_overtimes.append(existing)
    db.commit()
    for o in created_overtimes:
        db.refresh(o)
    return created_overtimes
