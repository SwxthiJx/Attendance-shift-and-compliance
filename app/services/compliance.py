from typing import List, Dict, Any
from datetime import date
from app.core.config import settings

class ComplianceEngine:
    """
    Separate configurable compliance engine enforcing ONLY the two specified rules:
    Rule 1: Shift exceeding MAX_CONTINUOUS_SHIFT_HOURS (default 10.0 hours)
    Rule 2: Worker exceeding MAX_CONSECUTIVE_WORKING_DAYS (default 6 days)
    """

    def __init__(
        self,
        max_continuous_shift_hours: float = None,
        max_consecutive_working_days: int = None
    ):
        self.max_continuous_shift_hours = (
            max_continuous_shift_hours 
            if max_continuous_shift_hours is not None 
            else settings.MAX_CONTINUOUS_SHIFT_HOURS
        )
        self.max_consecutive_working_days = (
            max_consecutive_working_days 
            if max_consecutive_working_days is not None 
            else settings.MAX_CONSECUTIVE_WORKING_DAYS
        )

    def evaluate_shifts(self, worker_id: int, reconciled_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluates compliance rules for a worker's shifts across a pay period.
        Adds compliance flags to the shift results.
        """
        # Sort results chronologically by work_date
        sorted_results = sorted(reconciled_results, key=lambda r: r["rec_shift"].work_date)

        consecutive_days_count = 0
        last_work_date: date = None

        for result in sorted_results:
            w_date = result["rec_shift"].work_date
            actual_worked = result["payable_data"]["actual_worked_hours"]

            # --- Rule 1: Continuous Shift Hours ---
            if actual_worked > self.max_continuous_shift_hours:
                result["payable_data"]["flags"].append({
                    "rule_code": "MAX_CONTINUOUS_SHIFT_HOURS",
                    "message": f"Shift duration of {actual_worked:.2f} hours exceeds continuous limit of {self.max_continuous_shift_hours:.1f} hours"
                })

            # --- Rule 2: Consecutive Working Days ---
            # A day counts as worked if actual_worked_hours > 0
            if actual_worked > 0:
                if last_work_date is None or (w_date - last_work_date).days == 1:
                    consecutive_days_count += 1
                else:
                    consecutive_days_count = 1
                
                last_work_date = w_date

                if consecutive_days_count > self.max_consecutive_working_days:
                    result["payable_data"]["flags"].append({
                        "rule_code": "MAX_CONSECUTIVE_WORKING_DAYS",
                        "message": f"Worker has worked {consecutive_days_count} consecutive days, exceeding threshold of {self.max_consecutive_working_days} days"
                    })
            else:
                consecutive_days_count = 0
                last_work_date = None

        return sorted_results
