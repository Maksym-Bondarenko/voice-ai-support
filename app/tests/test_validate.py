def test_validate_ok(client):
    resp = client.post(
        "/validate",
        json={"tracking_id": "ABC123456", "postal_code": "80331"},
    )
    data = resp.json()
    assert resp.status_code == 200
    assert data["eligible"] is True
    assert data["status"] in {"Out for Delivery", "Scheduled"}