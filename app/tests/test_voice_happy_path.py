import uuid
import json

def test_voice_happy_path(client, mute_webhooks):
    cid = str(uuid.uuid4())

    def post(body):
        return client.post("/voice-webhook", json=body).json()

    # greeting
    assert "Hello" in post({"event": "call_started", "call_id": cid})["response"]["text"]

    # tracking
    post({"event": "transcript", "call_id": cid, "transcript": "ABC123456"})
    # postal
    post({"event": "transcript", "call_id": cid, "transcript": "80331"})
    # choose slot 1
    final = post({"event": "transcript", "call_id": cid, "transcript": "1"})
    assert "Goodbye" in final["response"]["text"]

    # call ended → QA log write
    post({"event": "call_ended", "call_id": cid, "full_transcript": "dummy"})

    # one confirm-email webhook fired
    assert any("email-confirm" in url for url, _ in mute_webhooks)