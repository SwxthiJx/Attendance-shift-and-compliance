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
    Supports flexible field aliases (timestamp/punch_timestamp, type/punch_type, shift_start/start_time, start/end for OT).
    Returns counts of created records.
    """
    worker_code_to_id = {}
    
    # Helper to resolve or auto-create Worker by worker_code or worker_id
    def resolve_worker_id(item: Dict[str, Any]) -> int:
        code = str(item.get("worker_id") or item.get("worker_code") or item.get("worker", "UNKNOWN"))
        if code in worker_code_to_id:
            return worker_code_to_id[code]
        
        db_w = db.query(Worker).filter((Worker.worker_code == code) | (Worker.id == (int(code) if code.isdigit() else -1))).first()
        if not db_w:
            db_w = Worker(
                worker_code=code,
                name=f"Worker {code}",
                department="Operations"
            )
            db.add(db_w)
            db.flush()
        
        worker_code_to_id[code] = db_w.id
        return db_w.id

    # 1. Ingest Workers if explicitly supplied
    workers_input = data.get("workers", [])
    for w in workers_input:
        resolve_worker_id(w)

    # Helper for parsing datetime strings or combining date + HH:MM
    def parse_dt(val: Any, base_date: date = None) -> datetime:
        if isinstance(val, datetime):
            return val
        val_str = str(val).strip()
        if "T" in val_str or " " in val_str and len(val_str) > 10:
            return datetime.fromisoformat(val_str)
        elif base_date and ":" in val_str:
            parts = val_str.split(":")
            return datetime.combine(base_date, datetime.min.time()).replace(hour=int(parts[0]), minute=int(parts[1]))
        return datetime.fromisoformat(val_str)

    # Helper for parsing date strings
    def parse_d(val: Any) -> date:
        if isinstance(val, date):
            return val
        return date.fromisoformat(str(val).strip())

    # 2. Ingest Rosters
    rosters_count = 0
    for r in data.get("rosters", []):
        w_id = resolve_worker_id(r)
        w_date = parse_d(r.get("work_date") or r.get("date"))
        
        raw_start = r.get("start_time") or r.get("shift_start")
        raw_end = r.get("end_time") or r.get("shift_end")
        
        start_t = parse_dt(raw_start, w_date)
        end_t = parse_dt(raw_end, w_date)
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
        raw_ts = p.get("punch_timestamp") or p.get("timestamp")
        p_ts = parse_dt(raw_ts)
        p_type = str(p.get("punch_type") or p.get("type")).upper()
        device_id = p.get("raw_device_id") or p.get("terminal") or "BIOMETRIC_01"

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
        l_date = parse_d(l.get("leave_date") or l.get("date"))
        l_type = l.get("leave_type", "FULL_DAY")

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
        o_date = parse_d(o.get("work_date") or o.get("date"))
        
        # Determine approved hours either directly or from start/end times
        if "approved_hours" in o:
            app_hours = float(o["approved_hours"])
        elif "start" in o and "end" in o:
            ot_start = parse_dt(o["start"], o_date)
            ot_end = parse_dt(o["end"], o_date)
            app_hours = round((ot_end - ot_start).total_seconds() / 3600.0, 4)
        else:
            app_hours = 0.0

        reason = o.get("reason", "Approved Overtime")

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

