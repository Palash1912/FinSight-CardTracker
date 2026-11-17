# FinSight AI — Project Implementation Progress & Roadmap

> **Last Updated**: November 17, 2026  
> **Overall Status**: Phases 1 through 8 Completed ✅ | Phase 9 (Policy RAG) Queued ⏳  
> **Progress**: **~90% Complete**

---

## Executive Summary

| Phase | Description | Status | Progress |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Inspection, Architecture & Schema Planning | **Completed** ✅ | 100% |
| **Phase 1** | Project Scaffold, Docker Stack, Migrations & Base Shell | **Completed** ✅ | 100% |
| **Phase 2** | Credit Card Management & CRUD APIs | **Completed** ✅ | 100% |
| **Phase 3** | Statement Ingestion (PDF Parsers & Dedup Pipeline) | **Completed** ✅ | 100% |
| **Phase 4** | Payments, Bill Tracking & Core Analytics | **Completed** ✅ | 100% |
| **Phase 5** | Rewards Engine & Pre-Purchase Recommendation (Core Differentiator) | **Completed** ✅ | 100% |
| **Phase 6** | Post-Purchase Reward Reconciliation & Dashboard | **Completed** ✅ | 100% |
| **Phase 7** | Gmail OAuth Statement Discovery & Ingestion | **Completed** ✅ | 100% |
| **Phase 8** | LangGraph AI Financial Assistant with Safe Deterministic Tools | **Completed** ✅ | 100% |
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

### Phase 3: Statement Ingestion & Transaction Pipeline (Core Modules 2 & 3) ✅ (100%)
- [x] Database migration: `statements` and `transactions` tables in `0002_statements_and_transactions.py`
- [x] Local storage provider with path traversal safeguards (`app/storage/base.py`, `app/storage/local.py`)
- [x] PDF text extraction and parser adapter architecture:
  - [x] ICICI Bank statement parser (`app/parsers/icici.py`)
  - [x] HDFC Bank statement parser (`app/parsers/hdfc.py`)
  - [x] HSBC Bank statement parser (`app/parsers/hsbc.py`)
  - [x] Generic fallback statement parser (`app/parsers/generic.py`)
  - [x] Parser detector & registry (`app/parsers/detector.py`)
- [x] Transaction normalizer, merchant extractor, categorizer, and SHA-256 fingerprint deduplication (`app/parsers/normalizer.py`)
- [x] Statement ingestion service (`app/services/statement_service.py`):
  - [x] Size and type validation
  - [x] SHA-256 file-level duplicate detection
  - [x] Automatic target card association
  - [x] Staged import in `pending_review` state
  - [x] Total reconciliation comparing calculated net against total amount due
  - [x] Safe confirmation & rollback/delete cascades
- [x] Transaction management service (`app/services/transaction_service.py`)
- [x] REST APIs:
  - [x] `POST /api/v1/statements/upload` (multipart PDF upload & processing)
  - [x] `GET /api/v1/statements`, `GET /api/v1/statements/{id}`
  - [x] `POST /api/v1/statements/{id}/confirm`
  - [x] `DELETE /api/v1/statements/{id}` (safe rollback)
  - [x] `GET /api/v1/transactions` (filtered & paginated)
  - [x] `PATCH /api/v1/transactions/{id}`, `DELETE /api/v1/transactions/{id}`
- [x] Unit test suite for parsers and normalizer (`tests/unit/test_parsers.py`)
- [x] Frontend statement & transaction UI:
  - [x] Statements overview dashboard (`src/app/statements/page.tsx`)
  - [x] Drag & drop PDF upload modal (`src/components/statements/upload-dialog.tsx`)
  - [x] Review & reconciliation screen with transaction exclusion toggle and match indicator (`src/app/statements/[id]/review/page.tsx`)
  - [x] Full transaction management page with search, filters, inline category editing (`src/app/transactions/page.tsx`)
  - [x] Live dashboard recent transactions integration (`src/components/dashboard/recent-transactions.tsx`)

---

### Phase 4: Payments & Bill Tracking, Core Analytics (Core Modules 4 & 6) ✅ (100%)
- [x] Database migration: `payments` table in `0003_payments.py`
- [x] Payment tracking service (`app/services/payment_service.py`):
  - [x] Record full or partial payments, automatic card balance reduction
  - [x] Multi-payment statement settlement tracking
  - [x] Consolidated card billing & due date calculator with overdue detection
  - [x] Safe payment rollback / deletion
- [x] Deterministic SQL analytics service (`app/services/analytics_service.py`):
  - [x] Monthly spend aggregation time series
  - [x] Category spend breakdown and percentage distributions
  - [x] Top merchants ranking by spend
  - [x] Card spend distribution
  - [x] Live dashboard summary metrics (utilization, upcoming dues count & total, month-over-month spend delta)
- [x] REST APIs:
  - [x] `POST /api/v1/payments`, `GET /api/v1/payments`, `GET /api/v1/payments/bills`, `DELETE /api/v1/payments/{id}`
  - [x] `GET /api/v1/analytics/summary`, `/monthly`, `/categories`, `/merchants`, `/cards`
- [x] Unit test suite for payment and analytics schemas (`tests/unit/test_payments_and_analytics.py`)
- [x] Frontend UI:
  - [x] Payments & Bill Tracking page (`src/app/payments/page.tsx`) with overdue warning banner and billing status table
  - [x] Record Payment modal dialog (`src/components/payments/record-payment-dialog.tsx`) with quick pay actions
  - [x] Historical payment audit log with delete/rollback action
  - [x] Interactive Recharts visualizations (`src/components/dashboard/spend-charts.tsx`): Monthly spend area chart and category donut chart
  - [x] Live home dashboard summary card metrics integration (`src/components/dashboard/overview-cards.tsx`)

---

### Phase 5: Rewards & Benefits Intelligence Engine (Core Differentiator — Core Module 5) ✅ (100%)
- [x] Database migration: `reward_programs`, `reward_rules`, `reward_caps`, and `reward_ledger` tables in `0004_rewards.py`
- [x] SQLAlchemy models: `RewardProgram`, `RewardRule`, `RewardCap`, `RewardLedger` in `app/models/reward.py`
- [x] Pydantic v2 schemas: `RewardProgramRead`, `RewardRuleRead`, `RewardCapRead`, `CardRecommendationRequest`, `CardRecommendationItem`, `CardRecommendationResponse`, `CapUtilizationItem`, `RewardSummaryOverview` in `app/schemas/reward.py`
- [x] Deterministic Reward Calculator (`app/services/reward_engine.py`):
  - [x] Base rates, category accelerators, merchant regex accelerators, online/offline channels
  - [x] Min/max transaction limits and exclusion lists (Fuel, Rent, Wallet Reload, Government)
- [x] Cap Tracking Engine (`app/services/cap_tracker.py`):
  - [x] Calendar month, quarter, year, billing cycle reset rules and date arithmetic
  - [x] Track consumed vs remaining benefits with ledger query aggregation
- [x] Pre-Purchase Recommendation Engine (`app/services/purchase_advisor.py`):
  - [x] Evaluate planned purchase across all user cards
  - [x] Rank by net INR benefit and flag winner
  - [x] Explain decision logic and cap exhaustion warnings
- [x] Realistic bank reward fixtures seeding service (`app/services/seed_rewards.py`):
  - [x] Amazon Pay ICICI (5% Amazon, 2% Bill Pay, 1% Base)
  - [x] HDFC Millennia (5% Partner Merchants with ₹1,000/mo cap, 1% Base with ₹1,000/mo cap)
  - [x] HSBC Cashback / Live+ (10% Dining with ₹1,000/cycle cap, 1.5% Base)
  - [x] Axis Flipkart (5% Flipkart, 4% Preferred Partners, 1.5% Base)
  - [x] Generic points fixture (2 pts per ₹100, ₹0.25/pt)
- [x] REST APIs under `/api/v1/rewards`:
  - [x] `POST /api/v1/rewards/recommend` (simulator)
  - [x] `GET /api/v1/rewards/caps` (live cap utilization)
  - [x] `GET /api/v1/rewards/summary` (overall balances)
  - [x] `GET /api/v1/rewards/programs` (configured rules)
  - [x] `POST /api/v1/rewards/seed` (seed/reload default bank rules)
- [x] Unit test suite for Reward Engine, Cap Tracker, and Schemas (`tests/unit/test_rewards.py`)
- [x] Frontend UI:
  - [x] Interactive Pre-Purchase Card Advisor Simulator (`src/components/rewards/purchase-simulator.tsx`) with quick presets and winner card spotlight
  - [x] Live Cap Monitoring list (`src/components/rewards/cap-utilization-card.tsx`) with visual progress bars and reset countdowns
  - [x] Full Rewards Dashboard (`src/app/rewards/page.tsx`) with overview metrics, advisor, cap tracking, and rule inspection tabs
  - [x] React Query hooks (`src/hooks/use-rewards.ts`) and TypeScript types (`src/lib/types.ts`)

---

### Phase 6: Post-Purchase Reward Reconciliation & Dashboard ✅ (100%)
- [x] Statement transaction rule matching & expected reward ledger calculation (`app/services/reward_reconciliation.py`)
- [x] Running cap consumption tracking across statement transactions
- [x] Discrepancy detection (missing rewards, excluded spend warnings, cap losses, refund reversals)
- [x] Automatic reward reconciliation on statement confirmation (`app/services/statement_service.py`)
- [x] REST APIs under `/api/v1/rewards`:
  - [x] `GET /api/v1/rewards/reconciliation` (retrieval with card and statement filters)
  - [x] `POST /api/v1/rewards/reconciliation/run` (manual trigger & force recalculate)
- [x] Unit tests for reconciliation schemas and discrepancy flags (`tests/unit/test_rewards.py`)
- [x] Frontend UI:
  - [x] Reward Reconciliation Audit tab (`src/components/rewards/reward-reconciliation-view.tsx`)
  - [x] Reconciliation KPI metric cards (Total Expected Rewards, Excluded Spend, Cap Losses, Audit Flags)
  - [x] Interactive card filter and discrepancy toggle
  - [x] Detailed audit table with date, card, merchant, applied rule, rate %, expected reward, and status/reason badges
  - [x] Connected to React Query hooks (`useRewardReconciliation`, `useRunReconciliation`)

---

### Phase 7: Gmail Statement Ingestion (Core Module 7) ✅ (100%)
- [x] Database migration: `email_connections` and `email_imports` tables in `0005_email_imports.py`
- [x] SQLAlchemy models: `EmailConnection` and `EmailImport` in `app/models/email.py`
- [x] Token encryption service (`app/services/token_encryption.py`) with Fernet symmetric cipher and PBKDF2 key derivation
- [x] Gmail OAuth integration with read-only (`gmail.readonly`) scope and configuration in `app/config.py`
- [x] Bank statement discovery filter query generator targeting Indian issuers (HDFC, ICICI, HSBC, Axis, SBI) in `app/services/gmail_service.py`
- [x] Attachment downloader, SHA-256 deduplication check, and seamless handoff to Phase 3 statement pipeline
- [x] Simulated discovery engine for sandbox / local test demonstrations without requiring live Google Cloud Console credentials
- [x] REST APIs under `/api/v1/email`:
  - [x] `GET /api/v1/email/connections` (list active connections)
  - [x] `GET /api/v1/email/auth-url` (OAuth consent URL)
  - [x] `POST /api/v1/email/callback` (exchange authorization code)
  - [x] `POST /api/v1/email/sync` (trigger statement discovery & download)
  - [x] `DELETE /api/v1/email/connections/{id}` (disconnect & revoke tokens)
  - [x] `GET /api/v1/email/imports` (audit log of discovered emails and statuses)
- [x] Unit test suite for Gmail queries, token encryption, and schemas (`tests/unit/test_email_service.py`)
- [x] Frontend UI:
  - [x] `GmailSyncCard` embedded on Statements page (`src/components/statements/gmail-sync-card.tsx`)
  - [x] Real-time sync progress indicator and discovery outcome banner
  - [x] Discovery audit history drawer listing subject, sender, attachment, and status badges (`ingested`, `skipped_duplicate`, `failed`)
  - [x] React Query hooks (`useEmailConnections`, `useGmailAuthUrl`, `useSyncGmail`, `useEmailImports`) in `src/hooks/use-email.ts`

---

### Phase 8: AI Financial Assistant (Core Module 8) ✅ (100%)
- [x] Database migration: `ai_conversations` and `ai_messages` tables in `0006_ai_assistant.py`
- [x] SQLAlchemy models: `AIConversation` and `AIMessage` in `app/models/assistant.py`
- [x] Pydantic v2 schemas: `ChatMessageRead`, `AIConversationRead`, `ChatRequest`, `ChatResponse` in `app/schemas/assistant.py`
- [x] Zero LLM arithmetic architecture & system prompt enforcing strict deterministic tool data
- [x] Deterministic read-only tool suite in `app/services/assistant_tools.py`:
  - [x] `get_card_summary`: Card limits, balances, utilization %, statement/due dates
  - [x] `get_upcoming_dues`: Outstanding bills, minimum amounts due, overdue detection
  - [x] `get_spending_analytics`: Current month spend, MoM delta, category breakdown, top merchants
  - [x] `evaluate_purchase_rewards`: Pre-purchase best card evaluation, net INR benefit, rate %
  - [x] `get_cap_status`: Active monthly/quarterly spend cap utilization
  - [x] `detect_missing_rewards`: Reward reconciliation audit for unrewarded spend & cap losses
  - [x] `search_transactions`: Transaction keyword search
- [x] Assistant orchestration engine (`app/services/assistant_service.py`):
  - [x] OpenAI-compatible structured tool calling loop with execution logging
  - [x] Offline / local rule-based intent matching fallback when AI is disabled or offline
- [x] REST APIs under `/api/v1/assistant`:
  - [x] `POST /api/v1/assistant/chat` (send message & receive tool-backed reply)
  - [x] `GET /api/v1/assistant/conversations` (list user advisory sessions)
  - [x] `GET /api/v1/assistant/conversations/{id}` (session message history)
  - [x] `DELETE /api/v1/assistant/conversations/{id}` (delete session)
- [x] Unit test suite for assistant tool definitions, system prompt, and schemas (`tests/unit/test_assistant.py`)
- [x] Frontend UI:
  - [x] Conversational chat page (`src/app/assistant/page.tsx`) with session history sidebar and "+ New Session" action
  - [x] Quick financial prompt cards (Amazon spend evaluation, upcoming dues, spend breakdown, cap limits, reward leak audit)
  - [x] Executed tool call badges in assistant messages
  - [x] React Query hooks (`useConversations`, `useConversation`, `useSendMessage`, `useDeleteConversation`) in `src/hooks/use-assistant.ts`

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
