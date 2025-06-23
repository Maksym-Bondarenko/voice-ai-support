def test_reschedule_updates_db_and_fires_email(client, mute_webhooks):
    # 1) reschedule
    resp = client.post(
        "/reschedule",
        json={"tracking_id": "ABC123456", "new_slot": "2025-06-18T07:00:00Z"},
    )
    assert resp.json()["ok"] is True

    # 2) DB row changed
    check = client.post(
        "/validate",
        json={"tracking_id": "ABC123456", "postal_code": "80331"},
    ).json()
    assert check["status"] == "Scheduled"

    # 3) email webhook called exactly once
    assert len(mute_webhooks) == 1
    url, payload = mute_webhooks[0]
    assert "email-confirm" in url
    assert payload["tracking_id"] == "ABC123456"