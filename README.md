> **Note:** This repository is a test fixture used only to demo GitHub search for the [Open Ledger](https://github.com/ranjitaw/open-ledger) Slack hackathon project (Slack "Agent for Good" track). It is not an active or production service — the code, PRs, and commit history here exist purely to give Open Ledger's GitHub integration real data to search against.

# PulseMetrics API

Backend service for the PulseMetrics analytics platform: event ingestion,
webhook processing, and weekly reporting.

## Stack

- Python 3.12, FastAPI
- SQLAlchemy 2.0 (PostgreSQL)
- Redis (report cache)
- Alembic (migrations)
- pytest

## Local setup

\`\`\`bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in DATABASE_URL, REDIS_URL
alembic upgrade head
uvicorn app.main:app --reload
\`\`\`

## Tests

\`\`\`bash
pytest -v
\`\`\`

## Docs

- [Architecture](docs/Architecture.md) - system design and key tradeoffs
- [API Reference](docs/API.md) - endpoint documentation
- [Rollback Runbook](docs/Rollback.md) - deployment rollback procedure

## Project status

Actively developed. See open PRs for in-flight work. Ping #pulsemetrics-eng
in Slack with questions.
