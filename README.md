<div align="center">

# 🌐 Network Monitoring Utility

**Real-time async network node monitoring — ICMP ping & TCP port checks with a live dashboard**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.56-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/SQLite-aiosqlite-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/HoshiBatista/Network-Monitoring-Utility/python-app.yml?style=flat&logo=github-actions&logoColor=white&label=CI)](../../actions)

</div>

---

## Overview

Network Monitoring Utility is a high-performance web application that tracks whether your network nodes are reachable. It fires parallel ICMP and TCP checks using Python's native `asyncio`, persists results to SQLite, and surfaces everything through a sleek Streamlit dashboard that auto-refreshes in real time.

<div align="center">

| Feature | Detail |
|---|---|
| Parallel checks | `asyncio.gather` — all nodes checked simultaneously |
| Check methods | ICMP echo (no-port nodes) · TCP connect (port nodes) |
| State detection | Log entry written **only** on status change |
| Scheduler | APScheduler — configurable interval (default 30 s) |
| Dashboard | Live table · status badges · latency breakdown |
| History | Full event log with recovery / outage counters |

</div>

---

## Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi&logoColor=white" /> | Async REST API, dependency injection, OpenAPI docs |
| <img src="https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white" /> | Auto-refreshing dashboard, forms, metrics |
| <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=flat&logo=sqlite&logoColor=white" /> | Async I/O via `aiosqlite` + SQLAlchemy 2.0 ORM |
| <img src="https://img.shields.io/badge/Runtime-Python_3.13-3776AB?style=flat&logo=python&logoColor=white" /> | `asyncio` concurrency, `asyncio.open_connection` |
| <img src="https://img.shields.io/badge/Logging-Loguru-brightgreen?style=flat&logo=python&logoColor=white" /> | Colorized console output with per-level colours |
| <img src="https://img.shields.io/badge/Scheduler-APScheduler-blue?style=flat&logo=python&logoColor=white" /> | `AsyncIOScheduler` background job |
| <img src="https://img.shields.io/badge/ICMP-icmplib-orange?style=flat&logo=python&logoColor=white" /> | Unprivileged ping (no root required) |
| <img src="https://img.shields.io/badge/Validation-Pydantic_v2-E92063?style=flat&logo=pydantic&logoColor=white" /> | Request / response schemas |
| <img src="https://img.shields.io/badge/Tests-pytest_asyncio-0A9EDC?style=flat&logo=pytest&logoColor=white" /> | Async test suite, in-memory SQLite per test |
| <img src="https://img.shields.io/badge/Linter-Ruff-D7FF64?style=flat&logo=ruff&logoColor=black" /> | Fast Python linter & formatter |

</div>

---

## Project Structure

```
network-monitoring-utility/
├── app/
│   ├── api/
│   │   ├── router.py            # API router aggregator
│   │   └── routes/
│   │       ├── nodes.py         # CRUD endpoints for nodes
│   │       └── logs.py          # Status log endpoints
│   ├── config/
│   │   └── config.py            # Pydantic settings (env / .env file)
│   ├── core/
│   │   ├── database.py          # Async SQLAlchemy engine & session
│   │   └── logger.py            # Loguru setup + stdlib bridge
│   ├── models/
│   │   ├── node.py              # Node ORM model
│   │   └── status_log.py        # StatusLog ORM model
│   ├── schemas/
│   │   ├── node.py              # NodeCreate / NodeUpdate / NodeResponse
│   │   └── status_log.py        # StatusLogResponse
│   ├── services/
│   │   ├── checker.py           # Async checker (Phase 2)
│   │   └── scheduler.py         # APScheduler background job (Phase 3)
│   └── main.py                  # FastAPI app + lifespan
├── frontend/
│   └── app.py                   # Streamlit dashboard
├── tests/
│   └── conftest.py              # Shared fixtures (async client, test DB)
├── .github/workflows/           # CI pipeline
├── requirements.txt
├── pyproject.toml
├── TESTING.md
├── CONTRIBUTING.md
├── SECURITY.md
└── CODE_OF_CONDUCT.md
```

---

## Quick Start

### Prerequisites

- Python **3.13+**
- pip

### 1. Clone & install

```bash
git clone https://github.com/crissyro/network-monitoring-utility.git
cd network-monitoring-utility

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure (optional)

Create a `.env` file in the project root to override defaults:

```env
MONITORING_INTERVAL_SECONDS=30
MONITORING_TIMEOUT_SECONDS=5.0
LOG_LEVEL=INFO
LOG_FILE=logs/monitor.log          # optional — omit to log to stdout only
DATABASE_URL=sqlite+aiosqlite:///./network_monitor.db
```

### 3. Start the backend

```bash
uvicorn app.main:app --reload
```

Backend is now live at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

### 4. Start the dashboard

```bash
streamlit run frontend/app.py
```

Dashboard opens at `http://localhost:8501`.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/nodes` | List all monitored nodes |
| `POST` | `/nodes` | Add a new node |
| `GET` | `/nodes/{id}` | Get a single node |
| `PATCH` | `/nodes/{id}` | Update address or port |
| `DELETE` | `/nodes/{id}` | Remove a node |
| `GET` | `/logs` | List all status-change events |
| `GET` | `/nodes/{id}/logs` | List events for a specific node |

### Add a node — example

```bash
# TCP check (with port)
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"address": "8.8.8.8", "port": 53}'

# ICMP-only (no port)
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"address": "1.1.1.1"}'
```

---

## How It Works

```
startup
  └─ init_db()          create tables if they don't exist
  └─ start_scheduler()  APScheduler fires run_checks() every N seconds

run_checks()
  ├─ SELECT all nodes from SQLite
  ├─ asyncio.gather(*[_check_node(n) for n in nodes])
  │     ├─ port set   → asyncio.open_connection  (TCP)
  │     └─ no port    → icmplib.async_ping        (ICMP, unprivileged)
  └─ for each result:
        ├─ update last_status / last_latency / last_check_at
        ├─ if status changed → INSERT StatusLog row
        │     ONLINE  → logger.success(...)
        │     OFFLINE → logger.warning(...)
        └─ else → logger.info(...)
```

---

## Running Tests

```bash
pytest              # run all tests
pytest -v           # verbose
pytest -k "nodes"   # filter by name
```

Tests use an **in-memory SQLite database** per test — no server needed, no state leakage between runs.

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `MONITORING_INTERVAL_SECONDS` | `30` | Seconds between check cycles |
| `MONITORING_TIMEOUT_SECONDS` | `5.0` | Per-node check timeout |
| `LOG_LEVEL` | `INFO` | Minimum log level |
| `LOG_FILE` | `""` | Path to rotating log file (empty = disabled) |
| `LOG_ROTATION` | `10 MB` | Rotate when file reaches this size |
| `LOG_RETENTION` | `1 week` | Delete rotated files older than this |
| `DATABASE_URL` | `sqlite+aiosqlite:///./network_monitor.db` | SQLAlchemy async DB URL |
| `DEBUG` | `false` | Enable SQLAlchemy query echo & traceback vars |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for the vulnerability reporting process.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).

## License

Distributed under the **MIT License**.
