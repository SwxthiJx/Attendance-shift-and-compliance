import pytest

def test_ground_truth_comparison(client):
    # 1. Ingest synthetic data with seed 42
    gen_resp = client.post("/api/v1/periods/generate-and-ingest?seed=42&num_workers=10")
    assert gen_resp.status_code == 201
    
    period_id = "PERIOD_2026_08_A"
    
    # 2. Process pay period
    proc_resp = client.post(f"/api/v1/periods/{period_id}/process")
    assert proc_resp.status_code == 200
    
    # 3. Call Ground Truth Comparison endpoint
    gt_resp = client.get(f"/api/v1/ground-truth/compare?pay_period_id={period_id}&seed=42")
    assert gt_resp.status_code == 200
    
    gt_data = gt_resp.json()
    assert gt_data["is_perfect_match"] is True
    assert gt_data["accuracy_percentage"] == 100.0
    assert len(gt_data["discrepancies"]) == 0
