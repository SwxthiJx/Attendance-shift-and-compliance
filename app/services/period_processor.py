from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.worker import Worker
from app.models.roster import ShiftRoster
from app.models.punch import Punch
from app.models.leave import ApprovedLeave
from app.models.overtime import OvertimeApproval
from app.models.result import PayableResult
from app.models.exception import ExceptionRecord
from app.models.flag import ComplianceFlag
from app.services.deduplication import deduplicate_punches
from app.services.reconciliation import ReconciliationService
from app.services.payable import PayableCalculator
from app.services.compliance import ComplianceEngine
from app.core.config import settings

class PayPeriodProcessor:
    """
    Orchestrates pay period processing:
    1. Load source data (Workers, Rosters, Punches, Leaves, Overtimes)
    2. Deduplicate punches
    3. Reconcile attendance
    4. Calculate payable hours & overtime
    5. Run compliance rules
    6. Idempotently store results in database
    """

    def __init__(self, db: Session):
        self.db = db
        self.compliance_engine = ComplianceEngine()

    def process_period(
        self,
        pay_period_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:

        # 1. Clean previous results for this pay_period_id (Idempotent re-run execution)
        self.db.query(ComplianceFlag).filter(ComplianceFlag.pay_period_id == pay_period_id).delete(synchronize_session=False)
        self.db.query(ExceptionRecord).filter(ExceptionRecord.pay_period_id == pay_period_id).delete(synchronize_session=False)
        self.db.query(PayableResult).filter(PayableResult.pay_period_id == pay_period_id).delete(synchronize_session=False)
        self.db.flush()

        # 2. Fetch Source Data
        workers = self.db.query(Worker).all()
        all_punches = self.db.query(Punch).all()
        all_rosters = self.db.query(ShiftRoster).all()
        all_leaves = self.db.query(ApprovedLeave).all()
        all_overtimes = self.db.query(OvertimeApproval).all()

        if start_date and end_date:
            all_rosters = [r for r in all_rosters if start_date <= r.work_date <= end_date]
            all_leaves = [l for l in all_leaves if start_date <= l.leave_date <= end_date]
            all_overtimes = [o for o in all_overtimes if start_date <= o.work_date <= end_date]

        # 3. Deduplicate Punches
        deduplicate_punches(all_punches, window_seconds=settings.DEDUPLICATION_WINDOW_SECONDS)
        self.db.flush()

        total_processed = 0
        total_payable_hours = 0.0
        total_flags_count = 0
        total_exceptions_count = 0

        # 4. Process Worker by Worker
        for worker in workers:
            w_rosters = [r for r in all_rosters if r.worker_id == worker.id]
            w_leaves = [l for l in all_leaves if l.worker_id == worker.id]
            w_overtimes = [o for o in all_overtimes if o.worker_id == worker.id]
            w_punches = [p for p in all_punches if p.worker_id == worker.id]

            work_dates = set([r.work_date for r in w_rosters] + [l.leave_date for l in w_leaves] + [o.work_date for o in w_overtimes])
            for p in w_punches:
                if not p.is_deduplicated:
                    work_dates.add(p.punch_timestamp.date())

            rec_shifts = ReconciliationService.reconcile(
                worker_id=worker.id,
                work_dates=sorted(list(work_dates)),
                rosters=w_rosters,
                punches=w_punches,
                leaves=w_leaves,
                overtimes=w_overtimes
            )

            # Calculate payable hours per shift
            reconciled_results = []
            for rec_shift in rec_shifts:
                payable_data = PayableCalculator.calculate(rec_shift)
                reconciled_results.append({
                    "rec_shift": rec_shift,
                    "payable_data": payable_data
                })

            # Run Compliance Rules
            evaluated_results = self.compliance_engine.evaluate_shifts(worker.id, reconciled_results)

            # Save Results, Exceptions, and Flags to DB
            for res in evaluated_results:
                rec_shift = res["rec_shift"]
                pdata = res["payable_data"]

                has_exceptions = len(pdata["exceptions"]) > 0
                has_flags = len(pdata["flags"]) > 0

                status = "PROCESSED"
                if has_exceptions:
                    status = "HAS_EXCEPTIONS"
                elif has_flags:
                    status = "HAS_FLAGS"

                in_time_str = rec_shift.in_punch.punch_timestamp.strftime("%Y-%m-%d %H:%M:%S") if rec_shift.in_punch else "MISSING"
                out_time_str = rec_shift.out_punch.punch_timestamp.strftime("%Y-%m-%d %H:%M:%S") if rec_shift.out_punch else "MISSING"

                db_result = PayableResult(
                    worker_id=worker.id,
                    work_date=rec_shift.work_date,
                    pay_period_id=pay_period_id,
                    in_punch_time=in_time_str,
                    out_punch_time=out_time_str,
                    rostered_hours=pdata["rostered_hours"],
                    actual_worked_hours=pdata["actual_worked_hours"],
                    payable_hours=pdata["payable_hours"],
                    approved_overtime_hours=pdata["approved_overtime_hours"],
                    unapproved_overtime_hours=pdata["unapproved_overtime_hours"],
                    status=status
                )

                self.db.add(db_result)
                self.db.flush()

                # Add Exceptions
                for exc in pdata["exceptions"]:
                    db_exc = ExceptionRecord(
                        payable_result_id=db_result.id,
                        worker_id=worker.id,
                        work_date=rec_shift.work_date,
                        pay_period_id=pay_period_id,
                        code=exc["code"],
                        message=exc["message"],
                        severity=exc.get("severity", "HIGH")
                    )
                    self.db.add(db_exc)
                    total_exceptions_count += 1

                # Add Flags
                for flg in pdata["flags"]:
                    db_flg = ComplianceFlag(
                        payable_result_id=db_result.id,
                        worker_id=worker.id,
                        work_date=rec_shift.work_date,
                        pay_period_id=pay_period_id,
                        rule_code=flg["rule_code"],
                        message=flg["message"]
                    )
                    self.db.add(db_flg)
                    total_flags_count += 1

                total_processed += 1
                total_payable_hours += pdata["payable_hours"]

        self.db.commit()

        return {
            "pay_period_id": pay_period_id,
            "total_records_processed": total_processed,
            "total_payable_hours": round(total_payable_hours, 4),
            "total_flags": total_flags_count,
            "total_exceptions": total_exceptions_count,
            "message": f"Successfully processed pay period {pay_period_id}"
        }
