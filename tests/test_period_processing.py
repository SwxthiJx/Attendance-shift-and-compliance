import pytest

def test_pay_period_processing_and_rerunnability(client):
    # 1. Generate & Ingest synthetic data
    gen_resp = client.post("/api/v1/periods/generate-and-ingest?seed=42&num_workers=10")
    assert gen_resp.status_code == 201
    
    period_id = "PERIOD_2026_08_A"
    
    # 2. First Run of Pay Period Processing
    proc_resp1 = client.post(f"/api/v1/periods/{period_id}/process")
    assert proc_resp1.status_code == 200
    p1_summary = proc_resp1.json()
    assert p1_summary["total_records_processed"] > 0
    
    # 3. Retrieve Payable Results & Exceptions
    res_resp1 = client.get(f"/api/v1/results?pay_period_id={period_id}")
    assert res_resp1.status_code == 200
    results_count_1 = len(res_resp1.json())
    
    exc_resp1 = client.get(f"/api/v1/exceptions?pay_period_id={period_id}")
    assert exc_resp1.status_code == 200
    exceptions_count_1 = len(exc_resp1.json())
    
    # 4. SECOND Run (Re-run) of the exact same Pay Period ID
    proc_resp2 = client.post(f"/api/v1/periods/{period_id}/process")
    assert proc_resp2.status_code == 200
    p2_summary = proc_resp2.json()
    
    res_resp2 = client.get(f"/api/v1/results?pay_period_id={period_id}")
    results_count_2 = len(res_resp2.json())
    
    exc_resp2 = client.get(f"/api/v1/exceptions?pay_period_id={period_id}")
    exceptions_count_2 = len(exc_resp2.json())
    
    # Verify IDEMPOTENCY: Re-running processing produced identical record counts, NO duplicates created
    assert results_count_1 == results_count_2
    assert exceptions_count_1 == exceptions_count_2
    assert p1_summary["total_payable_hours"] == p2_summary["total_payable_hours"]
