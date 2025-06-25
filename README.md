# Delivery Rescheduler Voice‑AI Support

A full‑stack reference app that turns a **Retell** Voice‑AI agent into a self‑service delivery‑rescheduling hotline.
Built with **FastAPI + SQLAlchemy + n8n + SQLite** and deploys anywhere.

---

## ✨Key features

| Flow             | What happens                                      |
|------------------|---------------------------------------------------|
| **Caller dials** | Retell greets, asks tracking ID & postal code     |
| **Validation**   | FastAPI looks up the package in SQLite            |
| **Offer slots**  | Caller picks 1 / 2 / 3 → DB is updated            |
| **Confirm**      | FastAPI triggers n8n → e‑mail confirmation        |
| **Escalation**   | Invalid ID / ineligible status → n8n support hook |
| **Logs & QA**    | Transcript + completed / escalated flags stored   |

---

## 🏗Project structure

```text
.
├── app/                # FastAPI service
│   ├── core/           # settings loader
│   ├── db/             # models, session, seed script
│   ├── routers/        # REST + /retell webhook (and old custom-LLM code)
│   ├── services/       # e‑mail, support hooks, after‑call QA
│   └── voice_/         # in‑memory Retell session manager (and old attempt-files of custom LLM)
├── tests/              # unit / integration suite (pytest)
├── alembic/            # auto‑generated migrations
├── requirements.txt
└── README.md           # ← you are here
```

---

## 🚀Quick‑start (local dev)

> **Prereqs** Python3.11+, [ngrok](https://ngrok.com) (or Cloudflare Tunnel), Docker (used only for n8n), and a free [Retell](https://retellai.com) account.

```bash
# 1 – clone & install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2 – environment
cp .env.example .env               # edit if needed

# 3 – DB schema & seed demo rows
alembic upgrade head
python -m app.db.seed              # inserts ABC123456 / 80331 (eligible)

# 4 – run FastAPI (auto‑reload *and* verbose debug logging)
uvicorn app.main:app \
        --reload \
        --port 8000 \
        --log-level debug \
        --env-file .env

#   for remote debug launch with debugpy instead:
# python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload --port 8000

# 5 – spin‑up n8n (e‑mail + support hooks)
docker run -d --name n8n -p 5678:5678 \
  -e N8N_HOST="localhost" -e N8N_PROTOCOL="http" \
  n8nio/n8n
#    ↳ create two workflows:
#        /email-confirm      (Ethereal SMTP or your provider)
#        /support-escalation (Slack, Gmail, etc.)
#      then copy their URLs into .env

# 6 – expose FastAPI to the public for Retell webhook
ngrok http 8000
#    ↳ copy https://<hash>.ngrok.io → Retell “Webhook URL” field.
```

### ▶️Run the sample test‑suite

```bash
pytest -q    # 3 tests, <1s
```

---

## 🖥Live‑demo checklist

1. Dial the Retell agent number.
2. Provide tracking `ABCD` + postal `80331`.
3. Choose slot **1** (Tomorrow AM).
4. Watch:

   * FastAPI logs the `/retell` webhook calls.
   * `packages` row now has `status="Scheduled"`.
   * n8n workflow fires → Ethereal preview link arrives.
   * `call_logs` shows `completed=true`.

---

## ⚙️Environment (.env keys)

| Key                    | Example                                                 | Purpose                      |
| ---------------------- |---------------------------------------------------------|------------------------------|
| `DATABASE_URL`         | `sqlite:///./db.sqlite3`                                | Local DB                     |
| `EMAIL_WEBHOOK_URL`    | `http://localhost:5678/webhook-test/email-confirm`      | n8n confirmation             |
| `SUPPORT_WEBHOOK_URL`  | `http://localhost:5678/webhook-test/support-escalation` | n8n escalation               |
| `N8N_API_KEY`          | `<n8n-secret>`                                          | Header sent to both webhooks |
| `VOICE_WEBHOOK_SECRET` | `<retell-secret>`                                       | Optional HMAC guard          |

---

## 🧪With more time

* Swap in **Redis** for the in‑memory call session store.
* Add SMS confirmations.
* CI pipeline (GitHub-Actions) → test ➜ build ➜ deploy.
* Grafana dashboard for call latency & slot‑uptake stats.
* Use OpenAI/Anthropic to post‑score call QA.
* Experiment with other Voice‑AI engines (LeapingAI, ElevenLabs, ...).
* Work with LLM: RAG, RAFT, CAG, evals, A-B testing of different designs, ...

---

## 📸Screenshots
* **n8n Webhooks**: ![image](https://github.com/user-attachments/assets/0597d511-4045-48a1-8dab-ecb6ab752cef)
* **Retell Flow**: ![image](https://github.com/user-attachments/assets/28c3d611-6d42-44bf-9fbb-509951a0bbf9)

---

Maksym Bondarenko | 2025
[LinkedIn](https://www.linkedin.com/in/maksym-bondarenko-ua/) | [GitHub](https://github.com/Maksym-Bondarenko)
