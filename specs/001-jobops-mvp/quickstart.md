# Quickstart: JobOps AI — MVP

## Prerequisites
- Docker + Docker Compose, or Python 3.11+ for local backend dev.

## Run with Docker
```bash
cp backend/.env.example backend/.env   # mock providers are the default; set a SECRET_KEY
docker compose up --build              # db (pgvector) + backend on :8000
```
Open http://localhost:8000/docs for the live OpenAPI.

## Seed the single user
```bash
docker compose exec backend python -m app.seed   # creates the JWT user (+ optional sample profile)
```
Default creds come from env (`SEED_USER_EMAIL`, `SEED_USER_PASSWORD`).

## Demo flow (under 1 minute)
1. `POST /api/v1/auth/login` → copy `access_token`.
2. `PUT /api/v1/profile` and add skills/projects (or use the seeded sample profile).
3. `POST /api/v1/jobs` with a structured job payload.
4. `POST /api/v1/jobs/{id}/score` → see the 1–10 score, recommendation, and component breakdown.
5. `POST /api/v1/applications` → the job appears on the board in `nueva`.
6. `POST /api/v1/applications/{id}/messages` → generate the recruiter message.
7. `PATCH /api/v1/applications/{id}/state` → move through the board; `GET /applications/board`.

## Tests (deterministic, no network)
```bash
cd backend
pip install ".[dev]"
LLM_PROVIDER=mock EMBEDDING_PROVIDER=mock pytest -q
```
Key test: `tests/test_scoring.py` asserts the same input yields an identical score and that the
breakdown's weighted sum reconciles to the final value.

## CI
GitHub Actions runs ruff → mypy → alembic upgrade → pytest with mock providers (no LLM keys needed).
