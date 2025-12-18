# Cloud Run Observability Sandbox

A small Flask-based demo app to explore Cloud Run observability features (logging, tracing, metrics) and simple Firestore integration.

## What this project is
- A minimal Flask application demonstrating:
  - JSON structured logging (using `python-json-logger`)
  - Trace linkage via `X-Cloud-Trace-Context` header
  - Simulated latency and CPU load endpoints for tracing/metrics
  - Basic Firestore usage for sample user writes
- Intended for running on Google Cloud Run (Dockerfile uses a builder + distroless runtime), but also runnable locally.

## Key files
- `main.py` — Flask app and all endpoints
- `requirements.txt` — Python dependencies
- `Dockerfile` — multi-stage build, runtime uses distroless and runs `gunicorn` as a module
- `.gitignore` — ignores common Python artifacts

## Environment
- `PROJECT_ID` (optional) — Google Cloud project id used to initialize Firestore client
- `DATABASE_ID` (optional) — Firestore database id (defaults to `(default)`)

If `PROJECT_ID` is not provided, Firestore initialization will fail and the app continues with `db = None` (you can still use non-Firestore endpoints).

## Quick start — local (dev)
1. Create and activate a virtual environment:
   - python -m venv .venv
   - source .venv/bin/activate  (or `.venv\Scripts\activate` on Windows)
2. Install dependencies:
   - pip install -r requirements.txt
3. Run:
   - For simple dev run: `python main.py` (starts Flask builtin server on port 8080)
   - To run with Gunicorn (recommended, matches production):
     - `python -m gunicorn --bind :8080 --workers 1 --threads 8 main:app`

## Quick start — Docker (matches deployment)
1. Build:
   - docker build -t cloud-run-observability-sandbox .
2. Run (example):
   - docker run -p 8080:8080 -e PROJECT_ID=your-gcp-project cloud-run-observability-sandbox

The `Dockerfile` uses a builder stage to install packages into `/app/site-packages` and a distroless runtime image for a smaller surface area.

## Endpoints
- `GET /` — Health / welcome message
- `POST /users` — Add a user to Firestore
  - Expects JSON with `id` and `name`
- `GET /slow-trace` — Simulates a slow dependency (sleeps, touches Firestore) — useful to create longer traces
- `GET /cpu-heavy` — Computes some arbitrary CPU task — useful to observe CPU metrics
- `GET /flaky` — Randomly returns 500 to simulate intermittent errors
- `GET /crash` — Demonstrate a runtime error and how Error reporting records and keeps track of errors
- `GET /cached-config` — Demonstrates cold vs warm start behaviour using a global cache

## Observability notes
- Logging:
  - Uses `python-json-logger` to emit JSON logs to stdout.
  - Logs include a `trace_id` field extracted from the `X-Cloud-Trace-Context` header so logs can be correlated with Cloud Trace.
  - Logs also include a `component` field to filter by logical area (e.g., `trace-demo`, `cpu-demo`, `cache`, `user-module`).
- Traces:
  - The app reads `X-Cloud-Trace-Context` header and includes the trace id in log payloads to link logs and traces.
- Metrics & Alerts:
  - Use `cpu-heavy` and `slow-trace` to generate observable signals for metrics dashboards and alerting rules.

## Firestore
- The app initializes a Firestore client at startup using `google-cloud-firestore`.
- If initialization fails, `db` falls back to `None` and DB-related endpoints will skip database operations (but still run).
- `POST /users` writes to the `sampleUsers` collection.

## Notes for contributors
- Keep changes small and focused: this repo is a demo to exercise observability features.
- When adding endpoints, include structured logging with `component` and `trace_id` in `extra` for consistency.
- Avoid adding secrets or service account keys to the repo. Use environment variables or Cloud Run/IAM service accounts for production credentials.

## Troubleshooting
- If Firestore calls fail locally, ensure application has GCP credentials (e.g., `gcloud auth application-default login`) or unset `PROJECT_ID` to run without DB.
- For local tracing/log correlation, include a header like:
  - `X-Cloud-Trace-Context: TRACE_ID/123;o=1` where `TRACE_ID` is a hex trace id.

## License
- MIT
