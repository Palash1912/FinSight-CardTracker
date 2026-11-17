# FinSight AI — Project Implementation Progress & Roadmap

> **Last Updated**: November 17, 2026  
> **Overall Status**: Phase 1 & 2 Completed ✅ | Phase 3 (Statement Ingestion) Queued ⏳  
> **Progress**: **~30% Complete**

---

## Executive Summary

| Phase | Description | Status | Progress |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Inspection, Architecture & Schema Planning | **Completed** ✅ | 100% |
| **Phase 1** | Project Scaffold, Docker Stack, Migrations & Base Shell | **Completed** ✅ | 100% |
| **Phase 2** | Credit Card Management & CRUD APIs | **Completed** ✅ | 100% |
| **Phase 3** | Statement Ingestion (PDF Parsers & Dedup Pipeline) | **Pending** ⏳ | 0% |
| **Phase 4** | Payments, Bill Tracking & Core Analytics | **Pending** ⏳ | 0% |
| **Phase 5** | Rewards Engine & Pre-Purchase Recommendation (Core Differentiator) | **Pending** ⏳ | 0% |
| **Phase 6** | Post-Purchase Reward Reconciliation & Dashboard | **Pending** ⏳ | 0% |
| **Phase 7** | Gmail OAuth Statement Discovery & Ingestion | **Pending** ⏳ | 0% |
| **Phase 8** | LangGraph AI Financial Assistant with Safe Deterministic Tools | **Pending** ⏳ | 0% |
| **Phase 9** | Document Knowledge & Policy RAG | **Pending** ⏳ | 0% |
| **Phase 10** | Security Hardening, Backup/Restore, CI & Release Readiness | **Pending** ⏳ | 0% |

---

## Detailed Phase Breakdown

### Phase 0: Architecture & System Design ✅ (100%)
- [x] Inspect local tooling (Node 25, Python 3.11/3.12, Docker, Compose, Git)
- [x] High-level architecture definition (Modular monolith: Next.js + FastAPI + PostgreSQL)
- [x] Database ER diagram (20+ normalized entities with UUID PKs, audit trail, ownership boundary)
- [x] Technical decisions documentation (Decimal precision for financial arithmetic, config-driven reward rules, local storage abstraction)
- [x] Comprehensive master plan created and approved (`finsight-ai-architecture-plan.md`)

---

### Phase 1: Project Scaffold & Environment Setup ✅ (100%)
- [x] Root configuration (`.gitignore`, `.env.example`, `.env`, `docker-compose.yml`, `README.md`)
- [x] Backend scaffolding:
  - [x] `Dockerfile` (Python 3.12-slim, system build deps)
  - [x] `pyproject.toml` (FastAPI 0.115, Pydantic v2, SQLAlchemy 2 async, Alembic, httpx, test deps)
  - [x] `alembic.ini` and async/sync driver separation in `alembic/env.py`
  - [x] Initial Alembic migration created: `0001_initial_users_and_cards.py`
  - [x] Application factory, CORS middleware, lifespan in `app/main.py`
  - [x] Settings management in `app/config.py`
  - [x] Async engine & session factory in `app/database.py`
  - [x] Base model with UUID primary keys & timestamp mixin in `app/models/base.py`
  - [x] User model with ownership boundary in `app/models/user.py`
  - [x] Health check endpoints (`/api/v1/health`, `/api/v1/health/db`)
  - [x] Pytest fixtures & health endpoint integration tests
- [x] Frontend scaffolding:
  - [x] `Dockerfile` (Node 20 Alpine multi-stage)
  - [x] `package.json` (Next.js 15, React 19, TanStack Query, Tailwind, shadcn/ui, Recharts, Lucide)
  - [x] Tailwind CSS + PostCSS configuration with financial color tokens
  - [x] UI component library primitives (`Button`, `Card`, `Badge`)
  - [x] Navigation sidebar (collapsible, mobile-responsive) and top Header bar
  - [x] Dashboard shell (`OverviewCards`, `QuickActions`, `RecentTransactions` empty state)
  - [x] API client (`apiFetch`, typed methods) and TanStack query hooks
- [x] Docker images built (`finsight-ai-backend:latest`, `finsight-ai-frontend:latest`)

---

### Phase 2: Credit Card Management (Core Module 1) ✅ (100%)
- [x] Database migration: `credit_cards` table in `0001_initial_users_and_cards.py`
- [x] SQLAlchemy models: `CreditCard` model in `app/models/card.py`
- [x] Pydantic v2 schemas: `CardCreate`, `CardUpdate`, `CardResponse`, `CardSummary` in `app/schemas/card.py`
- [x] Card repository: `CardRepository` in `app/repositories/card_repository.py`
- [x] Billing calculations: cycle & due date logic in `app/services/billing.py`
- [x] Card service layer: `CardService` in `app/services/card_service.py`
- [x] API endpoints: full CRUD + archive under `/api/v1/cards` in `app/api/cards.py`
- [x] Backend tests:
  - [x] Unit tests for billing calculations (`tests/unit/test_billing.py`)
  - [x] Unit tests for card schemas (`tests/unit/test_card_schemas.py`)
  - [x] Integration tests for Card REST API (`tests/integration/test_cards_api.py`)
- [x] Frontend:
  - [x] Card list page (`src/app/cards/page.tsx`) with status badges, aggregate metrics, active/archived filters
  - [x] Visual card component (`src/components/cards/card-visual.tsx`) with EMV chip, issuer branding, masked PAN
  - [x] Card summary card (`src/components/cards/card-summary-card.tsx`) with dynamic utilization progress bar, due date proximity badges, statement date
  - [x] Add/Edit Card dialog (`src/components/cards/card-form-dialog.tsx`) with form validation & bank suggestions
  - [x] React Query hooks (`src/hooks/use-cards.ts`) for list, get, create, update, and archive operations
  - [x] Live dashboard overview metrics integration (`src/components/dashboard/overview-cards.tsx`)

---

### Phase 3: Statement Ingestion & Transaction Pipeline (Core Modules 2 & 3) ⏳
- [ ] Database migration: `statements`, `transactions`, `categories`, `merchants`, `ingestion_jobs`
- [ ] Local storage abstraction (`storage/base.py`, `storage/local.py`)
- [ ] PDF upload endpoint with file type, size validation & SHA-256 duplicate detection
- [ ] Statement parser adapter interface (`parsers/base.py`)
  - [ ] ICICI Bank parser adapter
  - [ ] HDFC Bank parser adapter
  - [ ] HSBC Bank parser adapter
  - [ ] Generic fallback tabular parser
- [ ] Transaction normalizer & SHA-256 fingerprinting for row-level deduplication
- [ ] Review & reconciliation screen before final import
- [ ] Reprocessing and safe rollback mechanisms
- [ ] Synthetic statement test fixtures and parser unit tests

---

### Phase 4: Payments & Bill Tracking, Core Analytics (Core Modules 4 & 6) ⏳
- [ ] Database migration: `payments` table
- [ ] Payment service: link payments to statements, track partial/full settlements
- [ ] Due date reminder logic and overdue warning indicators
- [ ] Analytics service (pure SQL/deterministic queries):
  - [ ] Monthly spend aggregation
  - [ ] Category spend breakdown
  - [ ] Merchant spend breakdown
  - [ ] Card-wise spend comparison
- [ ] Frontend dashboard integration:
  - [ ] Connect Overview Cards to live database metrics
  - [ ] Interactive spend charts using Recharts
  - [ ] Date range, card, category, and merchant filtering
- [ ] Payment and analytics unit/API tests

---

### Phase 5: Rewards & Benefits Intelligence Engine (Core Differentiator — Core Module 5) ⏳
- [ ] Database migration: `reward_programs`, `reward_rules`, `reward_caps`, `reward_periods`, `reward_ledger`, `reward_redemptions`
- [ ] Rule configuration API (versioned, effective-dated rules with source document references)
- [ ] Deterministic Reward Calculator (`reward_engine.py`):
  - [ ] Base rates, category accelerators, merchant accelerators, online/offline channels
  - [ ] Min/max transaction limits and exclusion lists
- [ ] Cap Tracking Engine (`cap_tracker.py`):
  - [ ] Calendar month, quarter, year, billing cycle reset rules
  - [ ] Track earned, pending, confirmed, credited, reversed, remaining amounts
  - [ ] Configurable pending cap consumption and refund reversal semantics
- [ ] Pre-Purchase Recommendation Engine (`purchase_advisor.py`):
  - [ ] Evaluate planned purchase across all user cards
  - [ ] Compare net benefits, remaining cap, and explain decision logic
  - [ ] Interactive UI purchase simulator & comparison table
- [ ] Comprehensive unit tests with synthetic bank rule fixtures

---

### Phase 6: Post-Purchase Reward Reconciliation & Dashboard ⏳
- [ ] Statement transaction rule matching & expected reward ledger calculation
- [ ] Discrepancy detection (missing, short, reversed rewards)
- [ ] Reward Dashboard UI:
  - [ ] Total rewards earned, pending, confirmed, credited, redeemed
  - [ ] Points balance and redemption value
  - [ ] Cap utilization progress bars per card
  - [ ] Expiring rewards and fee-waiver threshold tracker
- [ ] Reconciliation tests

---

### Phase 7: Gmail Statement Ingestion (Core Module 7) ⏳
- [ ] Database migration: `email_connections`, `email_imports`
- [ ] Gmail OAuth integration (read-only scope) with encrypted token storage
- [ ] Sender and subject filter rules configuration
- [ ] Background polling/discovery worker
- [ ] Attachment downloader, deduplication check & handoff to Phase 3 statement pipeline
- [ ] Disconnect and token revocation UI

---

### Phase 8: AI Financial Assistant (Core Module 8) ⏳
- [ ] Database migration: `ai_conversations`, `ai_messages`
- [ ] LLM provider abstraction (OpenAI / local LLMs / offline disable toggle)
- [ ] LangGraph orchestration graph
- [ ] Deterministic read-only tool suite:
  - [ ] `get_card_details`, `get_statement_summary`, `get_transactions`
  - [ ] `get_spending_analytics`, `get_due_dates`, `evaluate_purchase_rewards`
  - [ ] `get_remaining_reward_cap`, `compare_cards`, `detect_missing_rewards`
- [ ] Input/output validation and strict ownership enforcement
- [ ] Frontend conversational assistant chat interface (drawer or dedicated page)
- [ ] Assistant unit and safety tests

---

### Phase 9: Document Knowledge & Policy RAG (Core Module 9) ⏳
- [ ] Database migration: `documents`, `document_chunks` (pgvector)
- [ ] Policy PDF ingestion, chunking, and embedding pipeline
- [ ] RAG retriever for terms explanation with citation linking
- [ ] Discrepancy detector (flags conflicts between uploaded PDF and configured rules)
- [ ] Document management UI

---

### Phase 10: Security Hardening, Backup/Restore & Open-Source Release Readiness ⏳
- [ ] Security audit: CORS configuration, input sanitization, rate limiting, sensitive data masking
- [ ] Data export (JSON/CSV) and purge/deletion endpoints
- [ ] Database backup and restore shell scripts (`scripts/backup.sh`, `scripts/restore.sh`)
- [ ] Complete documentation:
  - [ ] `docs/architecture.md`
  - [ ] `docs/database-er.md`
  - [ ] `docs/api.md`
  - [ ] `docs/security.md`
  - [ ] `docs/contributing.md`
- [ ] GitHub Actions CI pipeline (linting with Ruff/ESLint, mypy type checks, pytest suite, docker build)
- [ ] Final release verification against Core Product Principles
