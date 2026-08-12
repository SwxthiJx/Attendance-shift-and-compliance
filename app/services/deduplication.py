from typing import List, Dict, Any
from datetime import datetime
from app.models.punch import Punch

def deduplicate_punches(punches: List[Punch], window_seconds: int = 60) -> List[Punch]:
    """
    Deduplicates punches for each worker.
    Punches of the same type ('IN' or 'OUT') within window_seconds of a previous punch
    are marked with is_deduplicated = True.
    """
    if not punches:
        return []

    # Sort punches by worker_id, punch_type, and timestamp
    sorted_punches = sorted(punches, key=lambda p: (p.worker_id, p.punch_type, p.punch_timestamp))

    last_punch_time: Dict[tuple, datetime] = {}

    for punch in sorted_punches:
        key = (punch.worker_id, punch.punch_type)
        if key in last_punch_time:
            time_diff = (punch.punch_timestamp - last_punch_time[key]).total_seconds()
            if time_diff <= window_seconds:
                punch.is_deduplicated = True
                continue
        
        punch.is_deduplicated = False
        last_punch_time[key] = punch.punch_timestamp

    return sorted_punches
