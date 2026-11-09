# Team n2

Ilias Team Registration 230916:
- Tobias Leibfritz
- Sebastian Sighart
- Wyatt Irmscher

## Development

Architecture and decisions: [docs/Architecture.md](docs/Architecture.md).
Benchmark dataset: [dataset/README.md](dataset/README.md).

### Backend (Python ≥ 3.12)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows; Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://localhost:8000/api/docs
pytest                          # API tests
```

On start, the backend imports `dataset/testcases.csv` into its SQLite database (`backend/data/`).

### Frontend (Node ≥ 20)

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173, /api is proxied to the backend
```

### Docker / Dokploy

```bash
docker compose up --build
```

API keys are set as environment variables in Dokploy, never in the repository.
# SoPraTest
