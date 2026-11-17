# FinSight AI

**AI-powered personal credit card & rewards intelligence platform.**

FinSight AI helps you manage multiple credit cards, ingest bank statements, track transactions and payments, understand card-specific cashback and reward rules, monitor reward caps, and determine which card provides the best benefit for a planned purchase.

> **Disclaimer:** Reward estimates depend on configured and verified issuer terms and may differ from actual bank postings. All sample reward rules in this repository are synthetic examples for development purposes only.

## Features (Planned)

- 💳 **Card Management** — Add, edit, and track multiple credit cards
- 📄 **Statement Ingestion** — Upload PDFs, auto-extract transactions
- 💰 **Transaction Tracking** — Categorize, search, and analyze spending
- 📅 **Payment & Bill Tracking** — Due dates, reminders, payment status
- 🎁 **Rewards Intelligence** — Configurable rules, cap tracking, pre-purchase recommendations
- 📊 **Dashboard & Analytics** — Spend breakdown, trends, reward utilization
- 📧 **Gmail Integration** — Auto-discover and ingest statement emails
- 🤖 **AI Assistant** — Natural language queries over your financial data
- 📚 **Document RAG** — Search official bank terms and policies

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui, Recharts, TanStack Query |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic |
| Database | PostgreSQL 16 |
| AI | LangGraph, OpenAI API (optional, behind provider abstraction) |

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Git

### 1. Clone and configure

```bash
git clone <repo-url> finsight-ai
cd finsight-ai
cp .env.example .env
# Edit .env with your preferred passwords and settings
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** on port `5432`
- **Backend API** on [http://localhost:8000](http://localhost:8000)
- **Frontend** on [http://localhost:3000](http://localhost:3000)

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Verify

- Frontend dashboard: [http://localhost:3000](http://localhost:3000)
- API health check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- API docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

## Development

### Backend (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Start with a local PostgreSQL
export DATABASE_URL="postgresql+asyncpg://finsight:finsight_dev@localhost:5432/finsight"
uvicorn app.main:app --reload
```

### Frontend (without Docker)

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend unit tests (no database needed)
cd backend
pytest tests/ -v

# With database
docker compose exec backend pytest tests/ -v
```

### Linting & Formatting

```bash
cd backend
ruff check .
ruff format .
mypy app/
```

## Project Structure

```
finsight-ai/
├── docker-compose.yml          # All services
├── .env.example                # Configuration template
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI application
│   │   ├── config.py           # Settings
│   │   ├── database.py         # SQLAlchemy async engine
│   │   ├── models/             # ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── api/                # Route handlers
│   │   └── services/           # Business logic
│   ├── alembic/                # Database migrations
│   └── tests/                  # Test suite
├── frontend/
│   └── src/
│       ├── app/                # Next.js pages
│       ├── components/         # React components
│       ├── lib/                # Utilities & API client
│       └── hooks/              # Custom hooks
└── docs/                       # Documentation
```

## Security & Privacy

- No full card numbers, CVVs, PINs, or bank credentials are stored
- PDFs and financial data remain local to your instance
- AI features are optional — disable by setting `AI_ENABLED=false`
- OAuth tokens are encrypted at rest
- Never commit `.env` or real financial data

## License

MIT
