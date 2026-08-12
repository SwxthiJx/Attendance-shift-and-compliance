from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from app.models.punch import Punch
from app.models.roster import ShiftRoster
from app.models.leave import ApprovedLeave
from app.models.overtime import OvertimeApproval

class ReconciledShift:
    def __init__(
        self,
        worker_id: int,
        work_date: date,
        roster: Optional[ShiftRoster] = None,
        in_punch: Optional[Punch] = None,
        out_punch: Optional[Punch] = None,
        leave: Optional[ApprovedLeave] = None,
        overtime: Optional[OvertimeApproval] = None,
    ):
        self.worker_id = worker_id
        self.work_date = work_date
        self.roster = roster
        self.in_punch = in_punch
        self.out_punch = out_punch
        self.leave = leave
        self.overtime = overtime
        self.exceptions = []
        self.flags = []

class ReconciliationService:
    """
    Reconciles Shift Rosters, Biometric Punches, Approved Leaves, and Overtime Approvals
    per worker + work_date.
    Handles overnight shifts crossing midnight safely.
    """

    @staticmethod
    def reconcile(
        worker_id: int,
        work_dates: List[date],
        rosters: List[ShiftRoster],
        punches: List[Punch], # deduplicated punches only
        leaves: List[ApprovedLeave],
        overtimes: List[OvertimeApproval]
    ) -> List[ReconciledShift]:

        roster_map: Dict[date, ShiftRoster] = {r.work_date: r for r in rosters if r.worker_id == worker_id}
        leave_map: Dict[date, ApprovedLeave] = {l.leave_date: l for l in leaves if l.worker_id == worker_id}
        overtime_map: Dict[date, OvertimeApproval] = {o.work_date: o for o in overtimes if o.worker_id == worker_id}

        valid_punches = [p for p in punches if p.worker_id == worker_id and not p.is_deduplicated]
        
        # Sort valid punches by timestamp
        valid_punches = sorted(valid_punches, key=lambda p: p.punch_timestamp)

        # Track assigned punches to prevent double-assignment
        assigned_punch_ids = set()

        reconciled_shifts: List[ReconciledShift] = []

        # Collect all relevant dates (from roster, leave, overtime, or punch timestamps)
        all_dates = set(work_dates)
        for r in rosters:
            if r.worker_id == worker_id:
                all_dates.add(r.work_date)
        for l in leaves:
            if l.worker_id == worker_id:
                all_dates.add(l.leave_date)
        for o in overtimes:
            if o.worker_id == worker_id:
                all_dates.add(o.work_date)
        for p in valid_punches:
            all_dates.add(p.punch_timestamp.date())

        for w_date in sorted(list(all_dates)):
            roster = roster_map.get(w_date)
            leave = leave_map.get(w_date)
            overtime = overtime_map.get(w_date)

            in_punch = None
            out_punch = None

            if roster:
                # Find punches window for roster: [roster.start_time - 4h, roster.end_time + 4h]
                win_start = roster.start_time - timedelta(hours=4)
                win_end = roster.end_time + timedelta(hours=4)

                candidate_punches = [
                    p for p in valid_punches 
                    if p.id not in assigned_punch_ids and win_start <= p.punch_timestamp <= win_end
                ]

                # Identify IN punch (first IN in window)
                for p in candidate_punches:
                    if p.punch_type == "IN" and not in_punch:
                        in_punch = p
                        assigned_punch_ids.add(p.id)

                # Identify OUT punch (last OUT in window after IN punch timestamp, or nearest OUT)
                for p in reversed(candidate_punches):
                    if p.punch_type == "OUT" and not out_punch:
                        if not in_punch or p.punch_timestamp >= in_punch.punch_timestamp:
                            out_punch = p
                            assigned_punch_ids.add(p.id)

            else:
                # No rostered shift for this work date: check unassigned punches on this date
                candidate_punches = [
                    p for p in valid_punches 
                    if p.id not in assigned_punch_ids and p.punch_timestamp.date() == w_date
                ]

                for p in candidate_punches:
                    if p.punch_type == "IN" and not in_punch:
                        in_punch = p
                        assigned_punch_ids.add(p.id)
                    elif p.punch_type == "OUT" and not out_punch:
                        out_punch = p
                        assigned_punch_ids.add(p.id)

            rec_shift = ReconciledShift(
                worker_id=worker_id,
                work_date=w_date,
                roster=roster,
                in_punch=in_punch,
                out_punch=out_punch,
                leave=leave,
                overtime=overtime
            )

            # Detect Exceptions
            # 1. Punch on Approved Leave
            if leave and (in_punch or out_punch):
                rec_shift.exceptions.append({
                    "code": "PUNCH_ON_LEAVE",
                    "message": f"Biometric punch recorded on approved leave day ({w_date})",
                    "severity": "HIGH"
                })

            # 2. Missing Punches
            elif (in_punch and not out_punch):
                rec_shift.exceptions.append({
                    "code": "MISSING_OUT",
                    "message": f"Missing OUT punch for work date {w_date}",
                    "severity": "HIGH"
                })
            elif (out_punch and not in_punch):
                rec_shift.exceptions.append({
                    "code": "MISSING_IN",
                    "message": f"Missing IN punch for work date {w_date}",
                    "severity": "HIGH"
                })

            reconciled_shifts.append(rec_shift)

        return reconciled_shifts
