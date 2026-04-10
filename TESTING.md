# Testing Guide

This document covers everything needed to run, extend, and manually test the Network Monitoring Utility.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Running the Test Suite](#running-the-test-suite)
3. [Test Architecture](#test-architecture)
4. [Writing New Tests](#writing-new-tests)
5. [Manual API Testing](#manual-api-testing)
6. [Frontend Testing](#frontend-testing)
7. [CI Pipeline](#ci-pipeline)

---

## Prerequisites

Install all dependencies (including test tools) into a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Key test dependencies pulled in by `requirements.txt`:

| Package | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-asyncio` | `async def` test support |
| `httpx` | In-process async HTTP client (no server needed) |
| `aiosqlite` | In-memory SQLite for isolated test DBs |
| `ruff` | Linter / formatter checks |

---

## Running the Test Suite

### Run all tests

```bash
pytest
```

### Verbose output

```bash
pytest -v
```

### Run a single file

```bash
pytest tests/test_health.py -v
```

### Run a single test by name

```bash
pytest -k "test_nodes_list_empty" -v
```

### Run with stdout captured (see print/log output)

```bash
pytest -s
```

### Show slowest tests

```bash
pytest --durations=10
```

Expected output when all tests pass:

```
tests/test_health.py .....                                         [100%]
5 passed in 0.42s
```

---

## Test Architecture

### Configuration (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"     # all async tests run automatically, no @pytest.mark.asyncio needed
testpaths    = ["tests"]
addopts      = "-ra -q"   # show short summary for non-passed; quiet mode
```

### The `client` fixture (`tests/conftest.py`)

Every async test that needs HTTP access uses the shared `client` fixture:

- Creates a **fresh in-memory SQLite database** per test — no leftover state between runs.
- Overrides the `get_session` FastAPI dependency so requests hit the test DB, not the real one.
- Wraps the FastAPI app in `httpx.AsyncClient` via `ASGITransport` — **no server process** is started.
- Cleans up (clears dependency overrides, disposes engine) after the test completes.

```
Test function
    └── client fixture
            ├── in-memory SQLite (fresh per test)
            ├── async_sessionmaker → overrides get_session
            └── AsyncClient(ASGITransport(app)) → HTTP calls go in-process
```

---

## Writing New Tests

Create new files under `tests/`. Prefix the file name with `test_`.

### Example: Node CRUD

```python
# tests/test_nodes.py
import pytest
from httpx import AsyncClient


async def test_create_node(client: AsyncClient):
    response = await client.post("/nodes", json={"address": "192.168.1.1"})
    assert response.status_code == 201
    data = response.json()
    assert data["address"] == "192.168.1.1"
    assert data["last_status"] == "UNKNOWN"
    assert data["id"] is not None


async def test_create_node_with_port(client: AsyncClient):
    response = await client.post("/nodes", json={"address": "10.0.0.1", "port": 443})
    assert response.status_code == 201
    assert response.json()["port"] == 443


async def test_create_node_duplicate(client: AsyncClient):
    await client.post("/nodes", json={"address": "10.0.0.2"})
    response = await client.post("/nodes", json={"address": "10.0.0.2"})
    assert response.status_code == 409


async def test_get_node(client: AsyncClient):
    created = (await client.post("/nodes", json={"address": "10.0.0.3"})).json()
    response = await client.get(f"/nodes/{created['id']}")
    assert response.status_code == 200
    assert response.json()["address"] == "10.0.0.3"


async def test_get_node_not_found(client: AsyncClient):
    response = await client.get("/nodes/99999")
    assert response.status_code == 404


async def test_list_nodes(client: AsyncClient):
    await client.post("/nodes", json={"address": "10.0.0.4"})
    await client.post("/nodes", json={"address": "10.0.0.5"})
    response = await client.get("/nodes")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_update_node(client: AsyncClient):
    created = (await client.post("/nodes", json={"address": "10.0.0.6"})).json()
    response = await client.patch(f"/nodes/{created['id']}", json={"port": 8080})
    assert response.status_code == 200
    assert response.json()["port"] == 8080


async def test_delete_node(client: AsyncClient):
    created = (await client.post("/nodes", json={"address": "10.0.0.7"})).json()
    response = await client.delete(f"/nodes/{created['id']}")
    assert response.status_code == 204
    # confirm it's gone
    assert (await client.get(f"/nodes/{created['id']}")).status_code == 404


async def test_delete_node_not_found(client: AsyncClient):
    response = await client.delete("/nodes/99999")
    assert response.status_code == 404
```

### Example: Logs

```python
# tests/test_logs.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.status_log import StatusLog


async def _create_node(client: AsyncClient, address: str) -> dict:
    return (await client.post("/nodes", json={"address": address})).json()


async def test_logs_empty(client: AsyncClient):
    response = await client.get("/logs")
    assert response.status_code == 200
    assert response.json() == []


async def test_node_logs_not_found(client: AsyncClient):
    response = await client.get("/nodes/99999/logs")
    assert response.status_code == 404


async def test_node_logs_empty(client: AsyncClient):
    node = await _create_node(client, "10.1.0.1")
    response = await client.get(f"/nodes/{node['id']}/logs")
    assert response.status_code == 200
    assert response.json() == []


async def test_logs_limit(client: AsyncClient):
    response = await client.get("/logs?limit=50")
    assert response.status_code == 200


async def test_logs_limit_exceeded(client: AsyncClient):
    # limit > 1000 is rejected
    response = await client.get("/logs?limit=9999")
    assert response.status_code == 422


async def test_logs_limit_zero(client: AsyncClient):
    response = await client.get("/logs?limit=0")
    assert response.status_code == 422
```

### Example: Input Validation

```python
# tests/test_validation.py
import pytest
from httpx import AsyncClient


async def test_create_node_empty_address(client: AsyncClient):
    response = await client.post("/nodes", json={"address": ""})
    assert response.status_code == 422


async def test_create_node_address_too_long(client: AsyncClient):
    response = await client.post("/nodes", json={"address": "a" * 256})
    assert response.status_code == 422


async def test_create_node_port_out_of_range_low(client: AsyncClient):
    response = await client.post("/nodes", json={"address": "10.0.0.1", "port": 0})
    assert response.status_code == 422


async def test_create_node_port_out_of_range_high(client: AsyncClient):
    response = await client.post("/nodes", json={"address": "10.0.0.1", "port": 65536})
    assert response.status_code == 422


async def test_create_node_invalid_json(client: AsyncClient):
    response = await client.post(
        "/nodes",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
```

### Tips for async tests

- The fixture is `async`, so your test must also be `async def`.
- `asyncio_mode = "auto"` in `pyproject.toml` means you do **not** need `@pytest.mark.asyncio` on each test.
- Each test gets its own isolated DB — no `setUp`/`tearDown` needed.
- Use `pytest -k "keyword"` to run only tests matching a name pattern.

---

## Manual API Testing

Start the backend first:

```bash
uvicorn app.main:app --reload
```

The interactive docs are at `http://localhost:8000/docs`.

### Nodes

**List all nodes**
```bash
curl http://localhost:8000/nodes
```

**Add a node (no port)**
```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"address": "8.8.8.8"}'
```

**Add a node with a port**
```bash
curl -X POST http://localhost:8000/nodes \
  -H "Content-Type: application/json" \
  -d '{"address": "example.com", "port": 443}'
```

**Get a single node**
```bash
curl http://localhost:8000/nodes/1
```

**Update a node's port**
```bash
curl -X PATCH http://localhost:8000/nodes/1 \
  -H "Content-Type: application/json" \
  -d '{"port": 8080}'
```

**Delete a node**
```bash
curl -X DELETE http://localhost:8000/nodes/1
```

### Logs

**List all logs (default limit 100)**
```bash
curl http://localhost:8000/logs
```

**List logs with custom limit**
```bash
curl "http://localhost:8000/logs?limit=50"
```

**List logs for a specific node**
```bash
curl http://localhost:8000/nodes/1/logs
```

### Error cases to verify manually

| Request | Expected status |
|---|---|
| `POST /nodes` with duplicate address | `409 Conflict` |
| `GET /nodes/99999` | `404 Not Found` |
| `DELETE /nodes/99999` | `404 Not Found` |
| `POST /nodes` with empty body | `422 Unprocessable Entity` |
| `GET /logs?limit=0` | `422 Unprocessable Entity` |
| `GET /logs?limit=1001` | `422 Unprocessable Entity` |

---

## Frontend Testing

The Streamlit dashboard (`frontend/app.py`) has no automated test suite — it is tested manually.

### Setup

```bash
# Terminal 1 — start the backend
uvicorn app.main:app --reload

# Terminal 2 — start the dashboard
streamlit run frontend/app.py
```

Open `http://localhost:8501` in a browser.

### Checklist

**Connection & refresh**
- [ ] The header shows **API Connected** (green dot) when the backend is running.
- [ ] The header shows **API Unreachable** (red dot) when the backend is stopped.
- [ ] The page auto-refreshes at the configured interval; the refresh counter increments.
- [ ] Changing the API URL in the sidebar updates the connection status immediately on next refresh.

**Adding nodes (sidebar form)**
- [ ] Submitting a valid address adds the node and shows a success toast.
- [ ] Submitting a duplicate address shows an error message.
- [ ] Submitting an empty address shows a warning.
- [ ] A port value of `0` is treated as "no port" (not sent to the API).

**Dashboard tab**
- [ ] Metric cards show correct totals for Total / Online / Offline / Unknown.
- [ ] The progress bar in the header reflects the online ratio.
- [ ] The node table renders with correct address, status badge, and latency color.
- [ ] ONLINE nodes show a green pulsing dot; OFFLINE shows red.
- [ ] Latency colors: green < 80 ms, yellow 80–250 ms, red > 250 ms.
- [ ] The Online / Offline / Latency summary cards update when a node's status changes.

**Event Logs tab**
- [ ] Recovery events (OFFLINE → ONLINE) show an upward green arrow and a green row tint.
- [ ] Outage events (ONLINE → OFFLINE) show a downward red arrow and a red row tint.
- [ ] Recovery and Outage metric counters are accurate.
- [ ] Changing the log limit in the sidebar changes the number of rows shown.

**Manage Nodes tab**
- [ ] Each node row shows address, status badge, and a Delete button.
- [ ] Clicking Delete removes the node and the page reruns.
- [ ] The Danger Zone expander is collapsed by default.
- [ ] "Delete All Nodes" button is disabled until the confirmation checkbox is checked.
- [ ] After deleting all nodes the dashboard shows the empty state message.

---

## CI Pipeline

The GitHub Actions workflow (`.github/workflows/`) runs on every push and pull request. It executes:

```bash
pytest
```

To run the same check locally before pushing:

```bash
# Lint
ruff check .

# Format check
ruff format --check .

# Tests
pytest
```

To auto-fix lint and formatting issues:

```bash
ruff check . --fix
ruff format .
```

---

## UI Input Testing Data

Ready-to-paste values for the **Add Node** and **Update Node** forms in the Streamlit dashboard.

### Add Node — valid entries (ONLINE expected)

| Address           | Port  | Notes                          |
|-------------------|-------|--------------------------------|
| `8.8.8.8`         | `53`  | Google Public DNS              |
| `1.1.1.1`         | `53`  | Cloudflare DNS                 |
| `8.8.4.4`         | `53`  | Google DNS secondary           |
| `9.9.9.9`         | `53`  | Quad9 DNS                      |
| `github.com`      | `443` | HTTPS — hostname resolution    |
| `cloudflare.com`  | `443` | HTTPS                          |
| `google.com`      | `80`  | HTTP                           |
| `httpbin.org`     | `80`  | HTTP test service              |
| `1.1.1.1`         |       | ICMP-only (leave Port blank)   |
| `localhost`       | `8000`| Local FastAPI backend          |
| `127.0.0.1`       | `8000`| Local FastAPI backend (IP)     |

### Add Node — unreachable entries (OFFLINE expected)

| Address           | Port   | Notes                              |
|-------------------|--------|------------------------------------|
| `192.168.99.99`   | `9999` | Private range, nothing listening   |
| `10.0.0.254`      | `8080` | Private range, nothing listening   |
| `203.0.113.1`     | `443`  | RFC 5737 documentation range       |
| `192.0.2.100`     |        | TEST-NET-1, no route (ICMP only)   |
| `dead.invalid`    | `80`   | Invalid hostname — DNS will fail   |

### Add Node — validation edge cases

| Address                  | Port    | Expected behaviour                     |
|--------------------------|---------|----------------------------------------|
| *(empty)*                | `80`    | Warning — address is required          |
| `8.8.8.8` *(duplicate)*  | `53`    | Error — 409 Conflict                   |
| `google.com`             | `0`     | Ignored — port 0 sent as "no port"     |
| `google.com`             | `65535` | Accepted — maximum valid port          |
| `google.com`             | `65536` | Should be rejected by form             |
| `a`                      | `443`   | Accepted — min_length is 1             |

### Update Node — test scenarios

Apply these on an existing node (e.g. the one created with `8.8.8.8`):

| Field    | New value    | Notes                                   |
|----------|--------------|-----------------------------------------|
| Port     | `443`        | Switch from 53 → HTTPS                  |
| Port     | *(blank)*    | Remove port — switches to ICMP-only     |
| Address  | `9.9.9.9`    | Change to Quad9 DNS                     |
| Address  | *(address already used by another node)* | Should show 409 error |

### Sidebar settings — test values

| Setting          | Value                    | Notes                                  |
|------------------|--------------------------|----------------------------------------|
| API URL          | `http://localhost:8000`  | Default — backend running locally      |
| API URL          | `http://127.0.0.1:8000`  | Equivalent alternate form              |
| API URL          | `http://localhost:9999`  | Wrong port — header shows API error    |
| Refresh interval | `5`                      | Fastest practical refresh (seconds)    |
| Refresh interval | `30`                     | Slower polling                         |
| Log limit        | `10`                     | Show only last 10 status-change events |
| Log limit        | `500`                    | High-volume history view               |

### Quick seed script

Populates the database with a mixed set of nodes in one go:

```bash
BASE=http://localhost:8000/nodes
for payload in \
  '{"address":"8.8.8.8","port":53}' \
  '{"address":"1.1.1.1","port":53}' \
  '{"address":"8.8.4.4","port":53}' \
  '{"address":"9.9.9.9","port":53}' \
  '{"address":"github.com","port":443}' \
  '{"address":"cloudflare.com","port":443}' \
  '{"address":"192.168.99.99","port":9999}' \
  '{"address":"10.0.0.254","port":8080}' \
  '{"address":"dead.invalid","port":80}'; do
  curl -s -X POST "$BASE" \
    -H "Content-Type: application/json" \
    -d "$payload" | python3 -m json.tool
done
```
