import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Tuple

class SyntheticDataGenerator:
    """
    Reproducible Synthetic Data Generator for Attendance & Compliance Testing.
    Creates workers, shift rosters, biometric punches (with controlled anomalies),
    approved leaves, overtime approvals, and ground-truth expectation metadata.
    """

    def __init__(self, seed: int = 42, num_workers: int = 10, start_date: date = date(2026, 8, 1)):
        self.seed = seed
        self.num_workers = num_workers
        self.start_date = start_date
        random.seed(self.seed)

    def generate(self) -> Dict[str, Any]:
        random.seed(self.seed)

        workers = []
        rosters = []
        punches = []
        leaves = []
        overtimes = []
        ground_truth = {}

        # 1. Generate Workers
        for i in range(1, self.num_workers + 1):
            w_code = f"EMP{i:03d}"
            workers.append({
                "id": i,
                "worker_code": w_code,
                "name": f"Worker {i}",
                "department": "Operations" if i % 2 == 0 else "Logistics"
            })

        # Scenario Mapping across Workers over a 14-day pay period (Aug 1 to Aug 14, 2026)
        # Worker 1: Normal 8h shifts every day (Aug 1 - Aug 5)
        # Worker 2: Missing IN Punch (Aug 2)
        # Worker 3: Missing OUT Punch (Aug 3)
        # Worker 4: Duplicate Punches (Aug 4)
        # Worker 5: Punch on Approved Leave (Aug 5)
        # Worker 6: Overnight Shift (Aug 5: 22:00 to Aug 6 06:00)
        # Worker 7: Approved Overtime (Aug 7: Rostered 8h, Worked 10h, 2h Approved)
        # Worker 8: Unapproved Overtime (Aug 8: Rostered 8h, Worked 10h, 0h Approved)
        # Worker 9: Shift > 10 Continuous Hours (Aug 9: 11h worked)
        # Worker 10: > 6 Consecutive Working Days (Aug 1 to Aug 8: 8 consecutive days)

        # Worker 1: Normal shifts Aug 1 - Aug 5
        for day_offset in range(5):
            w_date = self.start_date + timedelta(days=day_offset)
            start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=9, minute=0)
            end_dt = start_dt + timedelta(hours=8)
            rosters.append({"worker_id": 1, "work_date": w_date, "start_time": start_dt, "end_time": end_dt, "break_minutes": 0.0})
            punches.append({"worker_id": 1, "punch_timestamp": start_dt, "punch_type": "IN", "raw_device_id": "DEV-01"})
            punches.append({"worker_id": 1, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-01"})
            ground_truth[(1, w_date)] = {
                "payable_hours": 8.0,
                "exceptions": [],
                "flags": []
            }

        # Worker 2: Missing IN Punch on Aug 2
        w_date = self.start_date + timedelta(days=1)
        start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=9, minute=0)
        end_dt = start_dt + timedelta(hours=8)
        rosters.append({"worker_id": 2, "work_date": w_date, "start_time": start_dt, "end_time": end_dt, "break_minutes": 0.0})
        # ONLY OUT punch
        punches.append({"worker_id": 2, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-02"})
        ground_truth[(2, w_date)] = {
            "payable_hours": 0.0,
            "exceptions": ["MISSING_IN"],
            "flags": []
        }

        # Worker 3: Missing OUT Punch on Aug 3
        w_date = self.start_date + timedelta(days=2)
        start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=9, minute=0)
        end_dt = start_dt + timedelta(hours=8)
        rosters.append({"worker_id": 3, "work_date": w_date, "start_time": start_dt, "end_time": end_dt, "break_minutes": 0.0})
        # ONLY IN punch
        punches.append({"worker_id": 3, "punch_timestamp": start_dt, "punch_type": "IN", "raw_device_id": "DEV-03"})
        ground_truth[(3, w_date)] = {
            "payable_hours": 0.0,
            "exceptions": ["MISSING_OUT"],
            "flags": []
        }

        # Worker 4: Duplicate Punches on Aug 4 (IN at 09:00:01 and 09:00:04, OUT at 17:00:00 and 17:00:03)
        w_date = self.start_date + timedelta(days=3)
        start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=9, minute=0)
        end_dt = start_dt + timedelta(hours=8)
        rosters.append({"worker_id": 4, "work_date": w_date, "start_time": start_dt, "end_time": end_dt, "break_minutes": 0.0})
        punches.append({"worker_id": 4, "punch_timestamp": start_dt + timedelta(seconds=1), "punch_type": "IN", "raw_device_id": "DEV-04"})
        punches.append({"worker_id": 4, "punch_timestamp": start_dt + timedelta(seconds=4), "punch_type": "IN", "raw_device_id": "DEV-04"}) # Dup
        punches.append({"worker_id": 4, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-04"})
        punches.append({"worker_id": 4, "punch_timestamp": end_dt + timedelta(seconds=3), "punch_type": "OUT", "raw_device_id": "DEV-04"}) # Dup
        ground_truth[(4, w_date)] = {
            "payable_hours": 8.0,
            "exceptions": [],
            "flags": []
        }

        # Worker 5: Punch on Approved Leave Day (Aug 5)
        w_date = self.start_date + timedelta(days=4)
        start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=9, minute=0)
        end_dt = start_dt + timedelta(hours=8)
        leaves.append({"worker_id": 5, "leave_date": w_date, "leave_type": "ANNUAL"})
        punches.append({"worker_id": 5, "punch_timestamp": start_dt, "punch_type": "IN", "raw_device_id": "DEV-05"})
        punches.append({"worker_id": 5, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-05"})
        ground_truth[(5, w_date)] = {
            "payable_hours": 0.0, # Cannot pay automatically when punch on leave conflict
            "exceptions": ["PUNCH_ON_LEAVE"],
            "flags": []
        }

        # Worker 6: Overnight Shift (Aug 5 22:00 to Aug 6 06:00)
        w_date = self.start_date + timedelta(days=4) # Aug 5
        start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=22, minute=0)
        end_dt = start_dt + timedelta(hours=8) # Aug 6 06:00
        rosters.append({"worker_id": 6, "work_date": w_date, "start_time": start_dt, "end_time": end_dt, "break_minutes": 0.0})
        punches.append({"worker_id": 6, "punch_timestamp": start_dt, "punch_type": "IN", "raw_device_id": "DEV-06"})
        punches.append({"worker_id": 6, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-06"})
        ground_truth[(6, w_date)] = {
            "payable_hours": 8.0,
            "exceptions": [],
            "flags": []
        }


        # Worker 7: Approved Overtime (Aug 7: Rostered 8h, Worked 10h, 2h Approved)
        w_date = self.start_date + timedelta(days=6)
        start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=8, minute=0)
        end_dt = start_dt + timedelta(hours=10) # 18:00
        rostered_end = start_dt + timedelta(hours=8)
        rosters.append({"worker_id": 7, "work_date": w_date, "start_time": start_dt, "end_time": rostered_end, "break_minutes": 0.0})
        overtimes.append({"worker_id": 7, "work_date": w_date, "approved_hours": 2.0, "reason": "Inventory Audit"})
        punches.append({"worker_id": 7, "punch_timestamp": start_dt, "punch_type": "IN", "raw_device_id": "DEV-07"})
        punches.append({"worker_id": 7, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-07"})
        ground_truth[(7, w_date)] = {
            "payable_hours": 10.0,
            "exceptions": [],
            "flags": []
        }

        # Worker 8: Unapproved Overtime (Aug 8: Rostered 8h, Worked 10h, 0h Approved)
        w_date = self.start_date + timedelta(days=7)
        start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=8, minute=0)
        end_dt = start_dt + timedelta(hours=10) # 18:00
        rostered_end = start_dt + timedelta(hours=8)
        rosters.append({"worker_id": 8, "work_date": w_date, "start_time": start_dt, "end_time": rostered_end, "break_minutes": 0.0})
        # NO overtime approval
        punches.append({"worker_id": 8, "punch_timestamp": start_dt, "punch_type": "IN", "raw_device_id": "DEV-08"})
        punches.append({"worker_id": 8, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-08"})
        ground_truth[(8, w_date)] = {
            "payable_hours": 8.0, # Unapproved 2h OT not paid automatically
            "exceptions": ["UNAPPROVED_OVERTIME"],
            "flags": []
        }

        # Worker 9: Shift > 10 Continuous Hours (Aug 9: 11 hours continuous shift)
        w_date = self.start_date + timedelta(days=8)
        start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=7, minute=0)
        end_dt = start_dt + timedelta(hours=11) # 18:00
        rosters.append({"worker_id": 9, "work_date": w_date, "start_time": start_dt, "end_time": end_dt, "break_minutes": 0.0})
        overtimes.append({"worker_id": 9, "work_date": w_date, "approved_hours": 3.0, "reason": "Emergency Shift"})
        punches.append({"worker_id": 9, "punch_timestamp": start_dt, "punch_type": "IN", "raw_device_id": "DEV-09"})
        punches.append({"worker_id": 9, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-09"})
        ground_truth[(9, w_date)] = {
            "payable_hours": 11.0,
            "exceptions": [],
            "flags": ["MAX_CONTINUOUS_SHIFT_HOURS"]
        }

        # Worker 10: Exceeding 6 Consecutive Working Days (Worked 8 consecutive days: Aug 1 to Aug 8)
        for day_offset in range(8):
            w_date = self.start_date + timedelta(days=day_offset)
            start_dt = datetime.combine(w_date, datetime.min.time()).replace(hour=9, minute=0)
            end_dt = start_dt + timedelta(hours=8)
            rosters.append({"worker_id": 10, "work_date": w_date, "start_time": start_dt, "end_time": end_dt, "break_minutes": 0.0})
            punches.append({"worker_id": 10, "punch_timestamp": start_dt, "punch_type": "IN", "raw_device_id": "DEV-10"})
            punches.append({"worker_id": 10, "punch_timestamp": end_dt, "punch_type": "OUT", "raw_device_id": "DEV-10"})
            
            expected_flags = []
            if day_offset >= 6: # 7th and 8th consecutive days trigger Rule 2 flag
                expected_flags.append("MAX_CONSECUTIVE_WORKING_DAYS")
            
            ground_truth[(10, w_date)] = {
                "payable_hours": 8.0,
                "exceptions": [],
                "flags": expected_flags
            }

        return {
            "workers": workers,
            "rosters": rosters,
            "punches": punches,
            "leaves": leaves,
            "overtimes": overtimes,
            "ground_truth": ground_truth
        }
