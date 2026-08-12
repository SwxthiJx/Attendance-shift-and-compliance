from typing import Dict, Any
from app.services.reconciliation import ReconciledShift

class PayableCalculator:
    """
    Calculates rostered hours, actual worked hours, approved overtime, unapproved overtime,
    and final payable hours for a reconciled shift.
    """

    @staticmethod
    def calculate(rec_shift: ReconciledShift) -> Dict[str, Any]:
        rostered_hours = 0.0
        actual_worked_hours = 0.0
        payable_hours = 0.0
        approved_ot_hours = 0.0
        unapproved_ot_hours = 0.0

        if rec_shift.roster:
            dur_seconds = (rec_shift.roster.end_time - rec_shift.roster.start_time).total_seconds()
            break_mins = rec_shift.roster.break_minutes if rec_shift.roster.break_minutes is not None else 0.0
            rostered_hours = round(max(0.0, (dur_seconds / 3600.0) - (break_mins / 60.0)), 4)

        if rec_shift.overtime:
            approved_ot_hours = round(rec_shift.overtime.approved_hours, 4)

        # Check if shift has blocking exceptions (Missing punches or punch on leave)
        blocking_exceptions = [e for e in rec_shift.exceptions if e["code"] in ("MISSING_IN", "MISSING_OUT", "PUNCH_ON_LEAVE")]
        if blocking_exceptions:
            # Cannot safely calculate payable hours! Set payable hours to 0.0 per missing punch policy
            return {
                "rostered_hours": rostered_hours,
                "actual_worked_hours": 0.0,
                "payable_hours": 0.0,
                "approved_overtime_hours": approved_ot_hours,
                "unapproved_overtime_hours": 0.0,
                "exceptions": rec_shift.exceptions,
                "flags": rec_shift.flags
            }

        if rec_shift.in_punch and rec_shift.out_punch:
            worked_seconds = (rec_shift.out_punch.punch_timestamp - rec_shift.in_punch.punch_timestamp).total_seconds()
            actual_worked_hours = round(max(0.0, worked_seconds / 3600.0), 4)

            if rostered_hours > 0:
                extra_worked = max(0.0, actual_worked_hours - rostered_hours)
                payable_ot = min(extra_worked, approved_ot_hours)
                unapproved_ot_hours = round(max(0.0, extra_worked - approved_ot_hours), 4)
                
                # Base pay = min(actual_worked_hours, rostered_hours) + payable overtime
                payable_hours = round(min(actual_worked_hours, rostered_hours) + payable_ot, 4)
            else:
                payable_hours = round(min(actual_worked_hours, approved_ot_hours), 4)
                unapproved_ot_hours = round(max(0.0, actual_worked_hours - approved_ot_hours), 4)

            # If unapproved overtime exists, surface exception
            if unapproved_ot_hours > 0.0:
                rec_shift.exceptions.append({
                    "code": "UNAPPROVED_OVERTIME",
                    "message": f"Unapproved overtime of {unapproved_ot_hours:.2f} hours worked",
                    "severity": "MEDIUM"
                })

        return {
            "rostered_hours": rostered_hours,
            "actual_worked_hours": actual_worked_hours,
            "payable_hours": payable_hours,
            "approved_overtime_hours": approved_ot_hours,
            "unapproved_overtime_hours": unapproved_ot_hours,
            "exceptions": rec_shift.exceptions,
            "flags": rec_shift.flags
        }
