import pytest
from datetime import date, datetime, timedelta
from app.models.roster import ShiftRoster
from app.models.punch import Punch
from app.models.leave import ApprovedLeave
from app.models.overtime import OvertimeApproval
from app.services.reconciliation import ReconciliationService
from app.services.payable import PayableCalculator

def test_normal_shift():
    w_date = date(2026, 8, 1)
    start_dt = datetime(2026, 8, 1, 9, 0, 0)
    end_dt = datetime(2026, 8, 1, 17, 0, 0)
    
    roster = ShiftRoster(worker_id=1, work_date=w_date, start_time=start_dt, end_time=end_dt, break_minutes=0.0)
    in_p = Punch(id=1, worker_id=1, punch_timestamp=start_dt, punch_type="IN", is_deduplicated=False)
    out_p = Punch(id=2, worker_id=1, punch_timestamp=end_dt, punch_type="OUT", is_deduplicated=False)
    
    reconciled = ReconciliationService.reconcile(
        worker_id=1,
        work_dates=[w_date],
        rosters=[roster],
        punches=[in_p, out_p],
        leaves=[],
        overtimes=[]
    )
    
    assert len(reconciled) == 1
    shift = reconciled[0]
    assert shift.in_punch == in_p
    assert shift.out_punch == out_p
    assert len(shift.exceptions) == 0
    
    payable = PayableCalculator.calculate(shift)
    assert payable["payable_hours"] == 8.0
    assert payable["actual_worked_hours"] == 8.0

def test_missing_in_punch():
    w_date = date(2026, 8, 2)
    end_dt = datetime(2026, 8, 2, 17, 0, 0)
    
    out_p = Punch(id=1, worker_id=2, punch_timestamp=end_dt, punch_type="OUT", is_deduplicated=False)
    
    reconciled = ReconciliationService.reconcile(
        worker_id=2,
        work_dates=[w_date],
        rosters=[],
        punches=[out_p],
        leaves=[],
        overtimes=[]
    )
    
    shift = reconciled[0]
    payable = PayableCalculator.calculate(shift)
    
    assert any(e["code"] == "MISSING_IN" for e in payable["exceptions"])
    assert payable["payable_hours"] == 0.0 # Missing punch policy: hold pay

def test_missing_out_punch():
    w_date = date(2026, 8, 3)
    start_dt = datetime(2026, 8, 3, 9, 0, 0)
    
    in_p = Punch(id=1, worker_id=3, punch_timestamp=start_dt, punch_type="IN", is_deduplicated=False)
    
    reconciled = ReconciliationService.reconcile(
        worker_id=3,
        work_dates=[w_date],
        rosters=[],
        punches=[in_p],
        leaves=[],
        overtimes=[]
    )
    
    shift = reconciled[0]
    payable = PayableCalculator.calculate(shift)
    
    assert any(e["code"] == "MISSING_OUT" for e in payable["exceptions"])
    assert payable["payable_hours"] == 0.0 # Missing punch policy: hold pay

def test_overnight_shift():
    w_date = date(2026, 8, 5) # Aug 5 work date
    start_dt = datetime(2026, 8, 5, 22, 0, 0)
    end_dt = datetime(2026, 8, 6, 6, 0, 0) # Crosses midnight to Aug 6
    
    roster = ShiftRoster(worker_id=6, work_date=w_date, start_time=start_dt, end_time=end_dt, break_minutes=0.0)
    in_p = Punch(id=1, worker_id=6, punch_timestamp=start_dt, punch_type="IN", is_deduplicated=False)
    out_p = Punch(id=2, worker_id=6, punch_timestamp=end_dt, punch_type="OUT", is_deduplicated=False)
    
    reconciled = ReconciliationService.reconcile(
        worker_id=6,
        work_dates=[w_date],
        rosters=[roster],
        punches=[in_p, out_p],
        leaves=[],
        overtimes=[]
    )
    
    shift = reconciled[0]
    assert shift.work_date == date(2026, 8, 5)
    assert shift.in_punch == in_p
    assert shift.out_punch == out_p
    
    payable = PayableCalculator.calculate(shift)
    assert payable["payable_hours"] == 8.0

def test_punch_during_approved_leave():
    w_date = date(2026, 8, 5)
    start_dt = datetime(2026, 8, 5, 9, 0, 0)
    end_dt = datetime(2026, 8, 5, 17, 0, 0)
    
    leave = ApprovedLeave(worker_id=5, leave_date=w_date, leave_type="ANNUAL")
    in_p = Punch(id=1, worker_id=5, punch_timestamp=start_dt, punch_type="IN", is_deduplicated=False)
    out_p = Punch(id=2, worker_id=5, punch_timestamp=end_dt, punch_type="OUT", is_deduplicated=False)
    
    reconciled = ReconciliationService.reconcile(
        worker_id=5,
        work_dates=[w_date],
        rosters=[],
        punches=[in_p, out_p],
        leaves=[leave],
        overtimes=[]
    )
    
    shift = reconciled[0]
    payable = PayableCalculator.calculate(shift)
    
    assert any(e["code"] == "PUNCH_ON_LEAVE" for e in payable["exceptions"])
    assert payable["payable_hours"] == 0.0
