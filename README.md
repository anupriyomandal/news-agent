# Reactive News Intelligence Web Application

Full-stack reactive news intelligence engine with:

- FastAPI backend
- SQLite + FAISS local vector index
- RSS ingestion job every 15 minutes
- Multi-stage LLM summarization pipeline
- Next.js App Router frontend + Tailwind CSS
- Modern newspaper-style report UI

## Project Structure

```text
backend/
  main.py
  config.py
  database.py
  models.py
  rss_fetcher.py
  embeddings.py
  pipeline.py
  faiss_index.py
  scheduler.py
  requirements.txt
  data/
frontend/
  app/
  components/
  styles/
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- OpenAI API key

## 1) Backend Setup

```bash
cd /Users/anupriyomandal/Documents/news-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp backend/.env.example backend/.env
```

Set `OPENAI_API_KEY` in `backend/.env`.

Run backend:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

- [http://localhost:8000/health](http://localhost:8000/health)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## 2) Frontend Setup

```bash
cd /Users/anupriyomandal/Documents/news-agent/frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## API

### `POST /search`

Request:

```json
{
  "query": "Israel Iran News"
}
```

Response:

```json
{
  "report_id": "e4f...",
  "headline": "...",
  "metadata": "Generated ... | N sources",
  "tldr": ["..."],
  "sections": {
    "Immediate Developments": "..."
  },
  "implications": "...",
  "sources": [
    { "title": "...", "url": "...", "source": "..." }
  ]
}
```

### `GET /report/{report_id}`

Fetch a previously generated report for dedicated article page rendering.

### `POST /ingest/now` (Protected)

Trigger immediate ingestion run.

Auth header:

```text
Authorization: Bearer <INGEST_API_TOKEN>
```

### `GET /ingest/status` (Protected)

Get last ingestion run status/result metadata.

## Pipeline Stages

1. Fact extraction per article
2. Semantic deduplication
3. Section organization
4. TL;DR generation
5. Full synthesis (`headline + section prose + implications`)

## Notes

- Vectors are stored in FAISS index files under `backend/data/`.
- SQLite stores metadata and `embedding_id` mapping only.
- RSS ingestion runs on startup and then every 15 minutes.
- Query-aware routing selects feed families by intent (sports, geopolitics, markets, technology, general) before synthesis.
- Query results are cached for 10 minutes.
- Section output order is deterministic.
- Retrieval depth defaults to `SEARCH_TOP_K=20`; synthesis cap defaults to `PIPELINE_MAX_ARTICLES=12` (can be increased for deeper long-form reports).

## Production Ingestion Strategy

- Recommended: set `ENABLE_INTERNAL_SCHEDULER=false` in production and trigger `POST /ingest/now` using an external scheduler (cron, Cloud Scheduler, GitHub Actions).
- Keep `INGEST_ON_STARTUP=true` for warm startup ingest on each deploy.
- Set a strong `INGEST_API_TOKEN` and call ingest endpoint with bearer auth.

Example external scheduler command:

```bash
curl -X POST https://your-api-domain/ingest/now \
  -H "Authorization: Bearer $INGEST_API_TOKEN"
```

## Deploy: Railway (Backend) + Vercel (Frontend)

### Do you need Docker for Railway?

- Not strictly required (Railway can use Nixpacks), but for this project Docker is recommended.
- Reason: deterministic Python/FAISS runtime and smoother deploy parity with local.
- This repo now includes `Dockerfile`, `.dockerignore`, and `railway.json`.

### Railway Backend Deployment

1. Create a new Railway project from this GitHub repo.
2. Ensure Railway service uses repo root (Dockerfile at root).
3. Add a persistent volume and mount it to `/data`.
4. Set Railway env vars:
   - `OPENAI_API_KEY=...`
   - `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
   - `OPENAI_LLM_MODEL=gpt-5.2` (or your chosen model)
   - `DATA_DIR=/data`
   - `CORS_ORIGINS=https://<your-vercel-domain>`
   - `SEARCH_TOP_K=20`
   - `PIPELINE_MAX_ARTICLES=14`
   - `FRESH_SEARCH_ONLY=true`
   - `INGEST_API_TOKEN=<long-random-secret>`
   - `ENABLE_INTERNAL_SCHEDULER=false` (recommended in production)
   - `INGEST_ON_STARTUP=true`
5. Deploy and copy your Railway public URL (example: `https://news-api.up.railway.app`).

### Vercel Frontend Deployment

1. Import the same repo in Vercel.
2. Set root directory to `frontend`.
3. Set env var in Vercel:
   - `NEXT_PUBLIC_API_BASE=https://<your-railway-backend-domain>`
4. Deploy.

### Production Ingestion Scheduling

Recommended:

- Keep `ENABLE_INTERNAL_SCHEDULER=false` on Railway.
- Use an external scheduler (GitHub Actions, cron, or cloud scheduler) to call:

```bash
curl -X POST https://<your-railway-backend-domain>/ingest/now \
  -H "Authorization: Bearer <INGEST_API_TOKEN>"
```

- Frequency: every 10-15 minutes.

Optional status check:

```bash
curl https://<your-railway-backend-domain>/ingest/status \
  -H "Authorization: Bearer <INGEST_API_TOKEN>"
```
