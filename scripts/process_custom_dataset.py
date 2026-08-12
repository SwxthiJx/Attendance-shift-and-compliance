#!/usr/bin/env python3
"""
Custom Dataset Processing CLI Script for Attendance & Shift Compliance Service.
Ingests any custom JSON dataset file containing workers, rosters, punches, leaves, and overtimes,
processes attendance reconciliation, checks compliance rules & exceptions, and calculates payable hours.
"""

import sys
import os
import json
from pathlib import Path

# Ensure app package is in Python path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal, engine, Base
from app.services.custom_ingestor import ingest_custom_dataset
from app.services.period_processor import PayPeriodProcessor
from app.models.worker import Worker
from app.models.result import PayableResult
from app.models.exception import ExceptionRecord
from app.models.flag import ComplianceFlag

def main():
    # Determine input dataset file
    default_dataset_path = Path(__file__).parent.parent / "data" / "sample_custom_dataset.json"
    if len(sys.argv) > 1:
        dataset_path = Path(sys.argv[1])
    else:
        dataset_path = default_dataset_path

    if not dataset_path.exists():
        print(f"Error: Dataset file '{dataset_path}' not found.")
        sys.exit(1)

    print("=" * 85)
    print("ATTENDANCE & COMPLIANCE SERVICE — CUSTOM DATASET PROCESSOR")
    print("=" * 85)
    print(f"Loading custom dataset from: {dataset_path}")

    with open(dataset_path, "r") as f:
        data = json.load(f)

    pay_period_id = data.get("pay_period_id", "CUSTOM_PAY_PERIOD")

    # 1. Prepare DB Schema
    print("\n[1/4] Preparing Database Schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


    db = SessionLocal()
    try:
        # 2. Ingest Custom Dataset
        print("[2/4] Ingesting Custom Dataset Records...")
        counts = ingest_custom_dataset(db, data)
        print(f"  -> Workers Ingested:   {counts['workers']}")
        print(f"  -> Rosters Ingested:   {counts['rosters']}")
        print(f"  -> Punches Ingested:   {counts['punches']}")
        print(f"  -> Leaves Ingested:    {counts['leaves']}")
        print(f"  -> Overtimes Ingested: {counts['overtimes']}")

        # 3. Process Pay Period
        print(f"\n[3/4] Running Period Processing Engine for: '{pay_period_id}'...")
        processor = PayPeriodProcessor(db)
        summary = processor.process_period(pay_period_id=pay_period_id)
        print(f"  -> Total Processed Records: {summary['total_records_processed']}")
        print(f"  -> Total Exceptions Found:  {summary['total_exceptions']}")
        print(f"  -> Total Compliance Flags:  {summary['total_flags']}")
        print(f"  -> Total Payable Hours:     {summary['total_payable_hours']} hours")

        # 4. Display Formatted Breakdown Report
        print("\n" + "=" * 85)
        print("DAILY PAYABLE HOURS BREAKDOWN")
        print("=" * 85)
        print(f"{'Worker Code':<12} | {'Worker Name':<28} | {'Date':<10} | {'Rostered':<8} | {'Worked':<8} | {'Payable':<8} | {'Status':<12}")
        print("-" * 85)

        results = db.query(PayableResult).filter(PayableResult.pay_period_id == pay_period_id).all()
        workers = {w.id: w for w in db.query(Worker).all()}

        for r in results:
            w = workers.get(r.worker_id)
            w_code = w.worker_code if w else str(r.worker_id)
            w_name = w.name[:27] if w else "Unknown"
            print(f"{w_code:<12} | {w_name:<28} | {str(r.work_date):<10} | {r.rostered_hours:<8.1f} | {r.actual_worked_hours:<8.1f} | {r.payable_hours:<8.1f} | {r.status:<12}")

        # Display Exceptions if any
        exceptions = db.query(ExceptionRecord).filter(ExceptionRecord.pay_period_id == pay_period_id).all()
        if exceptions:
            print("\n" + "=" * 85)
            print("OPERATIONAL EXCEPTIONS REQUIRING REVIEW")
            print("=" * 85)
            for exc in exceptions:
                w = workers.get(exc.worker_id)
                w_code = w.worker_code if w else str(exc.worker_id)
                print(f"[{exc.severity}] Worker {w_code} ({exc.work_date}) | Code: {exc.code} | Message: {exc.message}")

        # Display Compliance Flags if any
        flags = db.query(ComplianceFlag).filter(ComplianceFlag.pay_period_id == pay_period_id).all()
        if flags:
            print("\n" + "=" * 85)
            print("COMPLIANCE ENGINE FLAGS")
            print("=" * 85)
            for flg in flags:
                w = workers.get(flg.worker_id)
                w_code = w.worker_code if w else str(flg.worker_id)
                print(f"Worker {w_code} ({flg.work_date}) | Rule: {flg.rule_code} | Message: {flg.message}")

        print("\n" + "=" * 85)
        print(f"GRAND TOTAL PAYABLE HOURS: {summary['total_payable_hours']} hrs")
        print("=" * 85)

    finally:
        db.close()

if __name__ == "__main__":
    main()
