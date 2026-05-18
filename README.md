# PromptScope — AI Visibility Monitoring Platform

Track how your brand appears in AI-generated responses across ChatGPT, Claude, Gemini, and Perplexity.

## Quick Start

```bash
cp backend/.env.example backend/.env
# Add your LLM API keys to backend/.env

docker compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **API Docs**: http://localhost:8000/docs

## Architecture

```
PromptScope/
├── backend/          # FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/
│   │   ├── api/v1/   # REST endpoints (brands, prompts, jobs, analytics)
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── llm/          # OpenAI, Anthropic, Gemini, Perplexity providers
│   │   │   ├── extraction/   # Brand mention extraction + sentiment analysis
│   │   │   ├── ranking/      # Visibility scoring (0–100)
│   │   │   └── cache/        # Redis cache
│   │   └── workers/  # Async job pipeline + APScheduler
│   └── alembic/      # DB migrations
└── frontend/         # Next.js 14 + Tailwind + Recharts
    └── src/
        ├── app/      # Dashboard, Brands, Prompts, Jobs, Analytics pages
        └── components/
```

## Core Concepts

**Visibility Score (0–100):** Computed per brand per job run from four weighted components:
- **Mention score** (30 pts): how many times the brand appears
- **Rank score** (40 pts): position in numbered lists (rank 1 = 40, rank 2 = 32, …)
- **Sentiment score** (±20 pts): ratio of positive vs negative context keywords
- **Coverage score** (10 pts): fraction of LLM providers that mentioned the brand

**Job Pipeline:**
1. User creates a Prompt (e.g. "What are the best CRM tools?")
2. Job triggers concurrent queries to all configured LLM providers
3. Raw responses are stored per-provider
4. Entity extractor finds brand mentions with position + rank
5. Sentiment analyzer scores each mention context
6. Visibility scorer aggregates into per-brand scores
7. Results available in the Analytics dashboard

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (GPT-4o-mini) |
| `ANTHROPIC_API_KEY` | Anthropic API key (Claude Haiku) |
| `GOOGLE_API_KEY` | Google AI API key (Gemini 1.5 Flash) |
| `PERPLEXITY_API_KEY` | Perplexity API key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |

At least one LLM API key is required. Providers without keys are skipped automatically.

## Development

```bash
# Backend only
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only
cd frontend
npm install
npm run dev

# Run DB migrations
cd backend
alembic upgrade head
```
