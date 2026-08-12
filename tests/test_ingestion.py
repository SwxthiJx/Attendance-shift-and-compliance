import pytest

def test_ingest_flow(client):
    # 1. Ingest Worker
    w_resp = client.post("/api/v1/ingest/workers", json=[
        {"worker_code": "TEST01", "name": "Test Worker", "department": "Engineering"}
    ])
    assert w_resp.status_code == 201
    w_data = w_resp.json()
    worker_id = w_data[0]["id"]
    
    # 2. Ingest Shift Roster
    s_resp = client.post("/api/v1/ingest/shifts", json=[
        {
            "worker_id": worker_id,
            "work_date": "2026-08-01",
            "start_time": "2026-08-01T09:00:00",
            "end_time": "2026-08-01T17:00:00",
            "break_minutes": 0
        }
    ])
    assert s_resp.status_code == 201
    
    # 3. Ingest Punches
    p_resp = client.post("/api/v1/ingest/punches", json=[
        {"worker_id": worker_id, "punch_timestamp": "2026-08-01T09:00:00", "punch_type": "IN"},
        {"worker_id": worker_id, "punch_timestamp": "2026-08-01T17:00:00", "punch_type": "OUT"}
    ])
    assert p_resp.status_code == 201
    
    # 4. Ingest Invalid Punch Type Validation Error
    bad_p_resp = client.post("/api/v1/ingest/punches", json=[
        {"worker_id": worker_id, "punch_timestamp": "2026-08-01T09:00:00", "punch_type": "INVALID"}
    ])
    assert bad_p_resp.status_code == 422 # Pydantic validation failure
