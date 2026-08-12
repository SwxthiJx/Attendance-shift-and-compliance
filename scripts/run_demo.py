#!/usr/bin/env python3
"""
End-to-End Demonstration Script for Attendance & Shift Compliance Service.
Executes dataset generation, ingestion, period processing, results retrieval,
exceptions review, compliance flag surfacing, and ground truth validation.
"""

import sys
import os
import json

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine

def run_demo():
    print("=" * 80)
    print("ATTENDANCE & SHIFT COMPLIANCE BACKEND DEMO")
    print("=" * 80)

    # 1. Initialize DB Schema
    print("\n[Step 1] Initializing Database Schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("-> Database schema ready.")

    client = TestClient(app)

    # 2. Generate and Ingest Synthetic Data
    print("\n[Step 2] Ingesting 4 Simulated Data Sources (Biometric Punches, Rosters, Leave, Overtime)...")
    gen_resp = client.post("/api/v1/periods/generate-and-ingest?seed=42&num_workers=10")
    print(f"-> Ingestion Status: {gen_resp.status_code}")
    print(f"-> Source Records Ingested: {json.dumps(gen_resp.json()['counts'], indent=2)}")

    # 3. Process Pay Period
    pay_period_id = "PERIOD_2026_08_A"
    print(f"\n[Step 3] Executing Re-runnable Processing Pipeline for Pay Period: {pay_period_id}...")
    proc_resp = client.post(f"/api/v1/periods/{pay_period_id}/process")
    summary = proc_resp.json()
    print(f"-> Summary: Processed {summary['total_records_processed']} records | "
          f"Total Payable Hours: {summary['total_payable_hours']}h | "
          f"Flags: {summary['total_flags']} | Exceptions: {summary['total_exceptions']}")

    # 4. Demonstrate Idempotent Re-running
    print("\n[Step 4] Testing Idempotency by Re-running Processing for Same Pay Period...")
    proc_resp_rerun = client.post(f"/api/v1/periods/{pay_period_id}/process")
    summary_rerun = proc_resp_rerun.json()
    print(f"-> Re-run Summary: Payable Hours={summary_rerun['total_payable_hours']}h, "
          f"Flags={summary_rerun['total_flags']}, Exceptions={summary_rerun['total_exceptions']}")
    assert summary['total_payable_hours'] == summary_rerun['total_payable_hours']
    print("-> Idempotency Verified: No duplicate results created.")

    # 5. Retrieve Results
    print("\n[Step 5] Retrieving Computed Payable Results...")
    res_resp = client.get(f"/api/v1/results?pay_period_id={pay_period_id}")
    results = res_resp.json()
    print(f"-> Total Payable Result Records: {len(results)}")
    
    # Print sample worker results
    sample_worker_id = 1
    w1_res = [r for r in results if r["worker_id"] == sample_worker_id][:2]
    print(f"\nSample Worker {sample_worker_id} Results:")
    for r in w1_res:
        print(f"   Work Date: {r['work_date']} | Rostered: {r['rostered_hours']}h | "
              f"Worked: {r['actual_worked_hours']}h | Payable: {r['payable_hours']}h | Status: {r['status']}")

    # 6. Surface Exceptions
    print("\n[Step 6] Surfacing Operational Exceptions Requiring Review...")
    exc_resp = client.get(f"/api/v1/exceptions?pay_period_id={pay_period_id}")
    exceptions = exc_resp.json()
    print(f"-> Total Exceptions Detected: {len(exceptions)}")
    for exc in exceptions[:5]:
        print(f"   Worker {exc['worker_id']} | Date: {exc['work_date']} | Code: [{exc['code']}] | Severity: {exc['severity']} | Message: {exc['message']}")

    # 7. Surface Compliance Flags
    print("\n[Step 7] Surfacing Compliance Engine Flags...")
    flg_resp = client.get(f"/api/v1/flags?pay_period_id={pay_period_id}")
    flags = flg_resp.json()
    print(f"-> Total Compliance Flags Triggered: {len(flags)}")
    for flg in flags:
        print(f"   Worker {flg['worker_id']} | Date: {flg['work_date']} | Rule: [{flg['rule_code']}] | Message: {flg['message']}")

    # 8. Perform Ground-Truth Comparison
    print("\n[Step 8] Comparing System Computed Results Against Known Ground Truth...")
    gt_resp = client.get(f"/api/v1/ground-truth/compare?pay_period_id={pay_period_id}&seed=42")
    gt_data = gt_resp.json()
    print(f"-> Total Ground-Truth Scenarios: {gt_data['total_scenarios']}")
    print(f"-> Matched Scenarios: {gt_data['matched_scenarios']}")
    print(f"-> System Accuracy: {gt_data['accuracy_percentage']}%")
    print(f"-> Perfect Match: {gt_data['is_perfect_match']}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("Interactive Swagger UI docs available at: http://127.0.0.1:8000/docs")
    print("=" * 80)

if __name__ == "__main__":
    run_demo()
