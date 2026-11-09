# Architecture & Decisions

Status: Milestone 1, CF-01 (Test Case & Dataset Management) implemented as foundation.

## Overview

```
Browser ──> frontend (nginx, React/TS) ──/api──> backend (FastAPI, Python)
                                                  ├── SQLite      (DATA_DIR/app.db)
                                                  ├── uploads     (DATA_DIR/uploads/)
                                                  └── seed data   (DATASET_DIR = dataset/)
```

| Path | Content |
|---|---|
| `backend/app/core/` | Settings (env vars), DB engine, FastAPI dependencies |
| `backend/app/models/` | SQLModel tables + API schemas, error type catalogue |
| `backend/app/services/` | Logic without HTTP: seed import, file storage |
| `backend/app/routers/` | REST endpoints (thin, delegate to models/services) |
| `backend/tests/` | API tests (pytest + FastAPI TestClient) |
| `frontend/src/api/` | Typed API client, types mirror the backend schemas |
| `frontend/src/components/` | UI components |

New core features follow the same pattern: model in `models/`, logic in `services/`,
endpoints in `routers/`, registered in `app/main.py` (e.g. CF-02 `models/vlm.py`,
`routers/vlms.py`; CF-03 `services/preprocessing.py`).

## Decisions

| # | Decision | Reason |
|---|---|---|
| 1 | FastAPI + SQLModel (Python), React + Vite (TypeScript) | Team request; FastAPI generates the OpenAPI documentation (NFR-03) at `/api/docs` |
| 2 | SQLite in a Docker volume | No extra service to run on Dokploy; enough for one user and a few hundred rows. SQLModel/SQLAlchemy allows switching to Postgres later |
| 3 | No migrations yet (`create_all`) | Schema is still changing. Introduce Alembic once a deployed database must keep its data across schema changes |
| 4 | Test cases are grouped by their **reference** (no separate dataset entity) | Simplest model that satisfies DS-05. Choosing a set of test cases for a run is done in CF-05 via filters/IDs |
| 5 | `dataset/` is the single source of truth for generated test cases; imported on every start (upsert by ID) and **read-only** via the API | Reproducibility (DS-06): changes go through `testcases.json` + `generate.py`, not through the UI |
| 6 | Uploaded clips (DS-07) are stored in `DATA_DIR/uploads/` with `source = upload` and can be deleted | Keeps user data separate from the versioned dataset |
| 7 | The dataset is baked into the backend image (build context = repo root) | Dokploy builds from the repository; no manual file copy on the server |
| 8 | All API routes under `/api` | One proxy rule in nginx (prod) and Vite (dev); no CORS needed |
| 9 | Error types are a fixed catalogue in `backend/app/models/error_types.py` (mirrors `dataset/generate.py`) | Validated input and a consistent timing/display category (DS-03, DS-04). Extend by adding one entry |

## Validation rules for uploads (DS-07)

- Reference: expected `OK`, error type `none`, no reference link.
- Test case: must link to an existing reference.
- `NOK` requires an error type other than `none`; `OK` may carry an error type (edge cases such as TC-003).
- ID optional (generated as `UP-###`), letters/digits/`-`/`_`, max. 32 characters.
- Video formats: mp4, webm, mov, mkv, avi; max. `MAX_UPLOAD_MB` (default 200).

## Configuration (environment variables)

| Variable | Default (local) | Docker | Meaning |
|---|---|---|---|
| `DATA_DIR` | `backend/data` | `/app/data` (volume) | SQLite DB and uploads |
| `DATASET_DIR` | `dataset` | `/app/dataset` | Generated benchmark dataset |
| `MAX_UPLOAD_MB` | `200` | `200` | Upload size limit (also `client_max_body_size` in `frontend/nginx.conf`) |
| `OPENAI_API_KEY` | – | Dokploy env | Used from CF-02 on, never committed (NFR-02) |

## REST API (CF-01)

Interactive documentation: `/api/docs` (OpenAPI: `/api/openapi.json`).

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Liveness check |
| GET | `/api/error-types` | Error type catalogue |
| GET | `/api/testcases?kind=&reference_id=&expected_result=` | List test cases |
| GET | `/api/testcases/{id}` | Single test case |
| GET | `/api/testcases/{id}/video` | Video file (supports range requests) |
| POST | `/api/testcases` | Upload clip + metadata (multipart) |
| DELETE | `/api/testcases/{id}` | Delete an uploaded test case (seed: 403, reference in use: 409) |

## Open points

- Tolerance (≈ 50 ms counts as OK) is still to be confirmed with ALTEN (see `dataset/README.md`).
- Terminology: the MVP PDF calls correct animations "positive", while MET-01 defines **NOK as the
  positive class** for the metrics. To be clarified before CF-06.
