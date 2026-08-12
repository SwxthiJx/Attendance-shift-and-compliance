# Test Strategy & Verification Plan

## 1. Overview & Testing Strategy

The test suite ensures total correctness across all 14 core functional requirements through isolated unit tests, end-to-end API integration tests, idempotency checks, and automated ground-truth verification.

Testing layers:
1. **Unit Tests**: Test isolated modules (deduplication sliding window, payable calculator logic, compliance engine rules).
2. **API Integration Tests**: Test REST API endpoint ingestion, request validation error handling, and results reporting.
3. **Period Processing & Idempotency Tests**: Verify that processing pay periods produces exact results and re-execution creates no duplicate DB records.
4. **Ground-Truth Validation**: Automated 1:1 verification comparing computed database output against synthetic ground-truth expectation metadata.

---

## 2. Test Coverage Matrix (14 Requirements)

| # | Test Case / Scenario | Test File | Assertion Verified |
| :--- | :--- | :--- | :--- |
| **1** | Normal 8h shift | `tests/test_reconciliation.py` | `payable_hours == 8.0`, `exceptions == []` |
| **2** | Missing IN punch | `tests/test_reconciliation.py` | Exception `MISSING_IN`, `payable_hours == 0.0` |
| **3** | Missing OUT punch | `tests/test_reconciliation.py` | Exception `MISSING_OUT`, `payable_hours == 0.0` |
| **4** | Duplicate punches (seconds apart) | `tests/test_deduplication.py` | Second punch tagged `is_deduplicated = True` |
| **5** | Overnight shift crossing midnight | `tests/test_reconciliation.py` | Shift attributed to original rostered `work_date` |
| **6** | Punch on approved leave day | `tests/test_reconciliation.py` | Exception `PUNCH_ON_LEAVE`, `payable_hours == 0.0` |
| **7** | Approved overtime | `tests/test_compliance.py` | `payable_hours == rostered + approved_ot` |
| **8** | Unapproved overtime | `tests/test_compliance.py` | `payable_hours == rostered`, Exception `UNAPPROVED_OVERTIME` |
| **9** | Partially approved overtime | `tests/test_compliance.py` | `payable_hours == rostered + partial_ot`, Exception `UNAPPROVED_OVERTIME` |
| **10** | Shift > 10 continuous hours | `tests/test_compliance.py` | Flag `MAX_CONTINUOUS_SHIFT_HOURS` generated |
| **11** | Worker > 6 consecutive work days | `tests/test_compliance.py` | Flag `MAX_CONSECUTIVE_WORKING_DAYS` on 7th+ day |
| **12** | Flag vs Exception behavior | `tests/test_reconciliation.py` | Exception holds pay; Flag permits payment |
| **13** | Pay period re-running (Idempotency)| `tests/test_period_processing.py` | Re-execution count matches original; 0 duplicate DB rows |
| **14** | Ground-truth comparison | `tests/test_ground_truth.py` | `accuracy_percentage == 100.0%`, `is_perfect_match == True` |

---

## 3. How to Run Automated Tests

### Run Full Test Suite
```bash
python3 -m pytest -v
```

### Run Specific Test Module
```bash
python3 -m pytest tests/test_compliance.py -v
```

### Run Ground Truth Validation
```bash
python3 -m pytest tests/test_ground_truth.py -v
```

---

## 4. Ground-Truth Validation Methodology

The synthetic data generator (`app/services/generator.py`) generates a deterministic dataset using a seed (default `42`).
For every generated worker shift, the generator constructs a ground-truth tuple:
```json
{
  "payable_hours": 8.0,
  "exceptions": ["MISSING_OUT"],
  "flags": ["MAX_CONTINUOUS_SHIFT_HOURS"]
}
```
The ground truth verification engine executes `GET /api/v1/ground-truth/compare`, comparing computed DB rows against expectations and reporting 100% match accuracy.
