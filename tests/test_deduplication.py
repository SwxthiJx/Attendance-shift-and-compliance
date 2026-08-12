import pytest
from datetime import datetime, timedelta
from app.models.punch import Punch
from app.services.deduplication import deduplicate_punches

def test_deduplication_seconds_apart():
    t0 = datetime(2026, 8, 1, 9, 0, 1)
    t1 = datetime(2026, 8, 1, 9, 0, 4) # 3 seconds later
    t2 = datetime(2026, 8, 1, 17, 0, 0)
    
    punches = [
        Punch(id=1, worker_id=101, punch_timestamp=t0, punch_type="IN"),
        Punch(id=2, worker_id=101, punch_timestamp=t1, punch_type="IN"),
        Punch(id=3, worker_id=101, punch_timestamp=t2, punch_type="OUT"),
    ]
    
    res = deduplicate_punches(punches, window_seconds=60)
    
    p1 = next(p for p in res if p.id == 1)
    p2 = next(p for p in res if p.id == 2)
    p3 = next(p for p in res if p.id == 3)
    
    assert p1.is_deduplicated is False
    assert p2.is_deduplicated is True
    assert p3.is_deduplicated is False

def test_deduplication_outside_window():
    t0 = datetime(2026, 8, 1, 9, 0, 0)
    t1 = datetime(2026, 8, 1, 9, 5, 0) # 5 minutes later
    
    punches = [
        Punch(id=1, worker_id=101, punch_timestamp=t0, punch_type="IN"),
        Punch(id=2, worker_id=101, punch_timestamp=t1, punch_type="IN"),
    ]
    
    res = deduplicate_punches(punches, window_seconds=60)
    assert res[0].is_deduplicated is False
    assert res[1].is_deduplicated is False
