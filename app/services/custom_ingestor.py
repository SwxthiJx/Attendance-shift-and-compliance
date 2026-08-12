from typing import Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.worker import Worker
from app.models.roster import ShiftRoster
from app.models.punch import Punch
from app.models.leave import ApprovedLeave
from app.models.overtime import OvertimeApproval

def ingest_custom_dataset(db: Session, data: Dict[str, Any]) -> Dict[str, int]:
    """
    Ingests a custom dataset payload containing workers, rosters, punches, leaves, and overtimes.
    Returns counts of created records.
    """
    worker_code_to_id = {}
    
    # 1. Ingest Workers
    workers_input = data.get("workers", [])
    for w in workers_input:
        code = w["worker_code"]
        db_worker = db.query(Worker).filter(Worker.worker_code == code).first()
        if not db_worker:
            db_worker = Worker(
                worker_code=code,
                name=w.get("name", f"Worker {code}"),
                department=w.get("department", "General")
            )
            db.add(db_worker)
            db.flush()
        worker_code_to_id[code] = db_worker.id

    # Helper function to get worker_id from either integer id or worker_code string
    def resolve_worker_id(item: Dict[str, Any]) -> int:
        if "worker_id" in item:
            return item["worker_id"]
        elif "worker_code" in item:
            code = item["worker_code"]
            if code in worker_code_to_id:
                return worker_code_to_id[code]
            db_w = db.query(Worker).filter(Worker.worker_code == code).first()
            if db_w:
                worker_code_to_id[code] = db_w.id
                return db_w.id
        raise ValueError(f"Could not resolve worker for item: {item}")

    # Helper for parsing datetime strings
    def parse_dt(val: str) -> datetime:
        return datetime.fromisoformat(val)

    # Helper for parsing date strings
    def parse_d(val: str) -> date:
        return date.fromisoformat(val)

    # 2. Ingest Rosters
    rosters_count = 0
    for r in data.get("rosters", []):
        w_id = resolve_worker_id(r)
        w_date = parse_d(r["work_date"]) if isinstance(r["work_date"], str) else r["work_date"]
        start_t = parse_dt(r["start_time"]) if isinstance(r["start_time"], str) else r["start_time"]
        end_t = parse_dt(r["end_time"]) if isinstance(r["end_time"], str) else r["end_time"]
        break_m = r.get("break_minutes", 0)

        db.add(ShiftRoster(
            worker_id=w_id,
            work_date=w_date,
            start_time=start_t,
            end_time=end_t,
            break_minutes=break_m
        ))
        rosters_count += 1

    # 3. Ingest Punches
    punches_count = 0
    for p in data.get("punches", []):
        w_id = resolve_worker_id(p)
        p_ts = parse_dt(p["punch_timestamp"]) if isinstance(p["punch_timestamp"], str) else p["punch_timestamp"]
        p_type = p["punch_type"]
        device_id = p.get("raw_device_id", "BIOMETRIC_01")

        db.add(Punch(
            worker_id=w_id,
            punch_timestamp=p_ts,
            punch_type=p_type,
            raw_device_id=device_id
        ))
        punches_count += 1

    # 4. Ingest Leaves
    leaves_count = 0
    for l in data.get("leaves", []):
        w_id = resolve_worker_id(l)
        l_date = parse_d(l["leave_date"]) if isinstance(l["leave_date"], str) else l["leave_date"]
        l_type = l.get("leave_type", "PAID_LEAVE")

        db.add(ApprovedLeave(
            worker_id=w_id,
            leave_date=l_date,
            leave_type=l_type
        ))
        leaves_count += 1

    # 5. Ingest Overtimes
    overtimes_count = 0
    for o in data.get("overtimes", []):
        w_id = resolve_worker_id(o)
        o_date = parse_d(o["work_date"]) if isinstance(o["work_date"], str) else o["work_date"]
        app_hours = float(o.get("approved_hours", 0.0))
        reason = o.get("reason", "Operational Overtime")

        db.add(OvertimeApproval(
            worker_id=w_id,
            work_date=o_date,
            approved_hours=app_hours,
            reason=reason
        ))
        overtimes_count += 1

    db.commit()

    return {
        "workers": len(worker_code_to_id),
        "rosters": rosters_count,
        "punches": punches_count,
        "leaves": leaves_count,
        "overtimes": overtimes_count
    }
