# ChartDB Backend

Django REST backend for the ChartDB frontend. It stores normalized diagrams in MySQL,
introspects one configured read-only MySQL source, and proxies streamed AI SQL export.

This V1 deliberately has no authentication and binds to localhost in Docker. Do not expose
it publicly.

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

- API: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI: `http://localhost:8000/api/schema/`

Set `VITE_API_BASE_URL=http://localhost:8000/api/v1` in the frontend.

## Local development on Windows, macOS, or Linux

```bash
python -m pip install -r requirements.txt
python manage.py runserver
```

Run this from the `chartdb-backend` directory with Python 3.13 or later. The local
server stores diagrams in MySQL database `chartdb`, applies migrations automatically,
and serves the API at `http://127.0.0.1:8000/api/v1`. The frontend origins
`http://localhost:5173` and `http://127.0.0.1:5173` are allowed by default.

The Windows defaults use MySQL at `127.0.0.1:3306`, database `chartdb`, user `root`,
and password `sql123456` for both application storage and schema introspection.
Copy `.env.local.example` to `.env.local` only when these values need to change.
If MySQL is unavailable, migrations fail and the backend does not start.

## API

- `GET /api/v1/health/live` and `GET /api/v1/health/ready`
- `GET|POST /api/v1/diagrams`
- `GET|PUT|DELETE /api/v1/diagrams/{id}`
- `POST /api/v1/source-database/introspect`
- `POST /api/v1/ai/sql-export/stream`

`PUT` and `DELETE` require the current revision. A stale write returns HTTP 409.
AI output is streamed as `delta`, `done`, and `error` SSE events.

## Run tests

```bash
python3.13 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

The test settings use MySQL database `chartdb_test`.

Generate and validate the OpenAPI document with:

```bash
.venv/bin/python manage.py spectacular --validate --file openapi.json
```

## Source database safety

`SOURCE_DB_*` is independent from `APP_DB_*`. Give the source user only `SELECT` access.
The API accepts no connection credentials and never returns or logs the configured password.
