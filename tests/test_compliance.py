import pytest
from datetime import date
from app.services.compliance import ComplianceEngine
from app.services.reconciliation import ReconciledShift

def test_rule_1_shift_exceeding_10_hours():
    engine = ComplianceEngine(max_continuous_shift_hours=10.0)
    
    rec_shift = ReconciledShift(worker_id=9, work_date=date(2026, 8, 9))
    shifts_data = [{
        "rec_shift": rec_shift,
        "payable_data": {
            "rostered_hours": 11.0,
            "actual_worked_hours": 11.0, # Exceeds 10.0h
            "payable_hours": 11.0,
            "approved_overtime_hours": 3.0,
            "unapproved_overtime_hours": 0.0,
            "exceptions": [],
            "flags": []
        }
    }]
    
    res = engine.evaluate_shifts(worker_id=9, reconciled_results=shifts_data)
    flags = res[0]["payable_data"]["flags"]
    
    assert len(flags) == 1
    assert flags[0]["rule_code"] == "MAX_CONTINUOUS_SHIFT_HOURS"

def test_rule_2_consecutive_working_days():
    engine = ComplianceEngine(max_consecutive_working_days=6)
    
    shifts_data = []
    for day in range(1, 9): # 8 consecutive days worked (Aug 1 to Aug 8)
        w_date = date(2026, 8, day)
        rec_shift = ReconciledShift(worker_id=10, work_date=w_date)
        shifts_data.append({
            "rec_shift": rec_shift,
            "payable_data": {
                "rostered_hours": 8.0,
                "actual_worked_hours": 8.0,
                "payable_hours": 8.0,
                "approved_overtime_hours": 0.0,
                "unapproved_overtime_hours": 0.0,
                "exceptions": [],
                "flags": []
            }
        })
        
    res = engine.evaluate_shifts(worker_id=10, reconciled_results=shifts_data)
    
    # Days 1 to 6 should have NO Rule 2 flag
    for day_idx in range(6):
        day_flags = [f for f in res[day_idx]["payable_data"]["flags"] if f["rule_code"] == "MAX_CONSECUTIVE_WORKING_DAYS"]
        assert len(day_flags) == 0
        
    # Day 7 and Day 8 (indices 6 and 7) SHOULD have Rule 2 flag
    for day_idx in range(6, 8):
        day_flags = [f for f in res[day_idx]["payable_data"]["flags"] if f["rule_code"] == "MAX_CONSECUTIVE_WORKING_DAYS"]
        assert len(day_flags) == 1

def test_approved_and_unapproved_overtime():
    from app.services.payable import PayableCalculator
    from app.models.roster import ShiftRoster
    from app.models.punch import Punch
    from app.models.overtime import OvertimeApproval
    from datetime import datetime

    w_date = date(2026, 8, 7)
    start_dt = datetime(2026, 8, 7, 8, 0, 0)
    end_dt = datetime(2026, 8, 7, 18, 0, 0) # 10 hours worked
    rostered_end = datetime(2026, 8, 7, 16, 0, 0) # 8 hours rostered

    roster = ShiftRoster(worker_id=7, work_date=w_date, start_time=start_dt, end_time=rostered_end)
    in_p = Punch(id=1, worker_id=7, punch_timestamp=start_dt, punch_type="IN", is_deduplicated=False)
    out_p = Punch(id=2, worker_id=7, punch_timestamp=end_dt, punch_type="OUT", is_deduplicated=False)

    # 1. Approved Overtime (2h)
    ot_approved = OvertimeApproval(worker_id=7, work_date=w_date, approved_hours=2.0)
    shift1 = ReconciledShift(worker_id=7, work_date=w_date, roster=roster, in_punch=in_p, out_punch=out_p, overtime=ot_approved)
    res1 = PayableCalculator.calculate(shift1)
    
    assert res1["payable_hours"] == 10.0
    assert res1["unapproved_overtime_hours"] == 0.0

    # 2. Unapproved Overtime (0h approved, 2h worked extra)
    shift2 = ReconciledShift(worker_id=8, work_date=w_date, roster=roster, in_punch=in_p, out_punch=out_p, overtime=None)
    res2 = PayableCalculator.calculate(shift2)
    
    assert res2["payable_hours"] == 8.0 # Only rostered paid automatically
    assert res2["unapproved_overtime_hours"] == 2.0
    assert any(e["code"] == "UNAPPROVED_OVERTIME" for e in res2["exceptions"])

    # 3. Partially Approved Overtime (1h approved out of 2h extra worked)
    ot_partial = OvertimeApproval(worker_id=7, work_date=w_date, approved_hours=1.0)
    shift3 = ReconciledShift(worker_id=7, work_date=w_date, roster=roster, in_punch=in_p, out_punch=out_p, overtime=ot_partial)
    res3 = PayableCalculator.calculate(shift3)

    assert res3["payable_hours"] == 9.0
    assert res3["unapproved_overtime_hours"] == 1.0
    assert any(e["code"] == "UNAPPROVED_OVERTIME" for e in res3["exceptions"])
