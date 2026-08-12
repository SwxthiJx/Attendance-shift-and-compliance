# API Reference Specification

Base URL: `http://localhost:8000/api/v1`

---

## 1. Ingestion Endpoints

### 1.1 Ingest Workers
- **Method**: `POST`
- **Path**: `/ingest/workers`
- **Request Body**: Array of `WorkerCreate`
```json
[
  {
    "worker_code": "EMP001",
    "name": "Alice Smith",
    "department": "Operations"
  }
]
```
- **Response**: `201 Created`
```json
[
  {
    "id": 1,
    "worker_code": "EMP001",
    "name": "Alice Smith",
    "department": "Operations",
    "created_at": "2026-08-12T08:00:00Z"
  }
]
```

### 1.2 Ingest Shift Rosters
- **Method**: `POST`
- **Path**: `/ingest/shifts`
- **Request Body**: Array of `ShiftRosterCreate`
```json
[
  {
    "worker_id": 1,
    "work_date": "2026-08-01",
    "start_time": "2026-08-01T09:00:00Z",
    "end_time": "2026-08-01T17:00:00Z",
    "break_minutes": 0.0
  }
]
```

### 1.3 Ingest Biometric Punches
- **Method**: `POST`
- **Path**: `/ingest/punches`
- **Request Body**: Array of `PunchCreate`
```json
[
  {
    "worker_id": 1,
    "punch_timestamp": "2026-08-01T09:00:00Z",
    "punch_type": "IN",
    "raw_device_id": "DEV-01"
  },
  {
    "worker_id": 1,
    "punch_timestamp": "2026-08-01T17:00:00Z",
    "punch_type": "OUT",
    "raw_device_id": "DEV-01"
  }
]
```

### 1.4 Ingest Approved Leave
- **Method**: `POST`
- **Path**: `/ingest/leave`
- **Request Body**: Array of `ApprovedLeaveCreate`
```json
[
  {
    "worker_id": 5,
    "leave_date": "2026-08-05",
    "leave_type": "ANNUAL"
  }
]
```

### 1.5 Ingest Overtime Approvals
- **Method**: `POST`
- **Path**: `/ingest/overtime`
- **Request Body**: Array of `OvertimeApprovalCreate`
```json
[
  {
    "worker_id": 7,
    "work_date": "2026-08-07",
    "approved_hours": 2.0,
    "reason": "Inventory Audit"
  }
]
```

---

## 2. Pay Period Processing Endpoints

### 2.1 Process Pay Period
- **Method**: `POST`
- **Path**: `/periods/{period_id}/process`
- **Response**: `200 OK`
```json
{
  "pay_period_id": "PERIOD_2026_08_A",
  "total_records_processed": 22,
  "total_payable_hours": 148.9997,
  "total_flags": 3,
  "total_exceptions": 4,
  "message": "Successfully processed pay period PERIOD_2026_08_A"
}
```

### 2.2 Generate & Ingest Synthetic Dataset (Demo Helper)
- **Method**: `POST`
- **Path**: `/periods/generate-and-ingest?seed=42&num_workers=10`
- **Response**: `201 Created`

---

## 3. Results & Compliance Queries

### 3.1 Get Payable Results
- **Method**: `GET`
- **Path**: `/results?pay_period_id=PERIOD_2026_08_A`
- **Response**: `200 OK`
```json
[
  {
    "id": 1,
    "worker_id": 1,
    "work_date": "2026-08-01",
    "pay_period_id": "PERIOD_2026_08_A",
    "rostered_hours": 8.0,
    "actual_worked_hours": 8.0,
    "payable_hours": 8.0,
    "approved_overtime_hours": 0.0,
    "unapproved_overtime_hours": 0.0,
    "status": "PROCESSED",
    "processed_at": "2026-08-12T08:30:00Z",
    "flags": [],
    "exceptions": []
  }
]
```

### 3.2 Get Exceptions Queue
- **Method**: `GET`
- **Path**: `/exceptions?pay_period_id=PERIOD_2026_08_A`
- **Response**: `200 OK`
```json
[
  {
    "id": 1,
    "worker_id": 2,
    "work_date": "2026-08-02",
    "pay_period_id": "PERIOD_2026_08_A",
    "code": "MISSING_IN",
    "message": "Missing IN punch for work date 2026-08-02",
    "severity": "HIGH",
    "created_at": "2026-08-12T08:30:00Z"
  }
]
```

### 3.3 Get Compliance Flags
- **Method**: `GET`
- **Path**: `/flags?pay_period_id=PERIOD_2026_08_A`
- **Response**: `200 OK`
```json
[
  {
    "id": 1,
    "worker_id": 9,
    "work_date": "2026-08-09",
    "pay_period_id": "PERIOD_2026_08_A",
    "rule_code": "MAX_CONTINUOUS_SHIFT_HOURS",
    "message": "Shift duration of 11.00 hours exceeds continuous limit of 10.0 hours",
    "created_at": "2026-08-12T08:30:00Z"
  }
]
```

### 3.4 Ground-Truth Comparison Verification
- **Method**: `GET`
- **Path**: `/ground-truth/compare?pay_period_id=PERIOD_2026_08_A&seed=42`
- **Response**: `200 OK`
```json
{
  "pay_period_id": "PERIOD_2026_08_A",
  "seed": 42,
  "total_scenarios": 21,
  "matched_scenarios": 21,
  "accuracy_percentage": 100.0,
  "is_perfect_match": true,
  "discrepancies": []
}
```
