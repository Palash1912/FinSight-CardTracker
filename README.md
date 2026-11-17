# FinSight AI 💳 ⚡

**Personal Credit Card Intelligence, Deterministic Rewards Optimizer & Statement Pipeline.**

FinSight AI is a self-hostable, privacy-first personal finance platform designed to manage credit cards, automate PDF & Gmail statement ingestion, track payments, audit reward earnings, monitor spend caps, and recommend the best credit card for every purchase with zero LLM arithmetic.

> **Disclaimer:** Reward calculations depend on configured and verified issuer terms. Calculations are executed exclusively by deterministic SQL and Python calculation engines.

---

## 🌟 Key Features

- 💳 **Credit Card Portfolio**: Track limits, balances, dynamic utilization bars, statement generation dates, and countdown to due dates.
- 📄 **Statement Ingestion Pipeline**: Ingest PDF statements from ICICI, HDFC, HSBC, Axis, and generic issuers with SHA-256 deduplication and staged review screens.
- 💰 **Transaction Engine**: Automatic merchant normalization, category heuristics, and inline editing.
- 📅 **Payments & Bill Tracking**: Multi-payment statement settlements, overdue warning banners, and historical audit logs.
- 🎁 **Rewards Intelligence & Pre-Purchase Advisor**:
  - Deterministic evaluation of base rates, merchant accelerators (e.g. 5% on Amazon), and category accelerators (e.g. 10% on Dining).
  - Multi-card recommendation simulator ranking cards by net INR benefit with cap remaining disclosures.
  - Active cap trackers across calendar months, quarters, and statement cycles.
- 🔍 **Post-Purchase Reward Reconciliation**: Audits statement transactions for reward leaks, unrewarded spend (fuel/rent exclusions), and forfeited benefits due to exhausted caps.
- 📧 **Gmail Statement Ingestion**: Automated discovery of credit card statement emails using read-only OAuth (`gmail.readonly`) with Fernet AES token encryption.
- 🤖 **AI Financial Assistant**: Conversational financial advisor backed by strict read-only deterministic tools. Never performs mental math.
- 📚 **Document Knowledge & Policy RAG**: Search official bank cardmember agreements with grounded page-level citations (`[HDFC Millennia Circular, Page 2]`).
- 🛡️ **Data Sovereignty & Privacy**: GDPR-compliant 1-click JSON export, CSV transaction export, database backup/restore scripts, and complete data purge.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Next.js 15 (React 19)                │
│       Tailwind CSS • shadcn/ui • Recharts • TanStack   │
└───────────────────────────▲────────────────────────────┘
                            │ REST APIs
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Backend                     │
│  ┌───────────────────────┐  ┌───────────────────────┐  │
│  │   Reward Engine       │  │   Statement Parser    │  │
│  │ (Deterministic Money) │  │  (PDF / SHA-256 Dedup)│  │
│  └───────────────────────┘  └───────────────────────┘  │
│  ┌───────────────────────┐  ┌───────────────────────┐  │
│  │  AI Assistant Tools   │  │   Policy RAG & Chunks │  │
│  │ (Zero LLM Arithmetic) │  │  (Page Citations)     │  │
│  └───────────────────────┘  └───────────────────────┘  │
└───────────────────────────▲────────────────────────────┘
                            │ SQLAlchemy 2 (Async)
┌───────────────────────────▼────────────────────────────┐
│                  PostgreSQL 16 Engine                  │
│       20+ Normalized Entities • Numeric(18, 4) Money    │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Docker Compose)

### 1. Clone & Configure Environment

```bash
git clone https://github.com/Palash1912/FinSight-CardTracker.git finsight-ai
cd finsight-ai
cp .env.example .env
```

### 2. Start Services

```bash
docker compose up --build -d
```

This starts:
- **PostgreSQL 16**: Port `5432`
- **FastAPI API**: [http://localhost:8000](http://localhost:8000) (Swagger Docs at `/docs`)
- **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)

### 3. Run Migrations & Seed Default Bank Rules

```bash
# Run database migrations to head
docker compose exec backend alembic upgrade head
```

Open [http://localhost:3000](http://localhost:3000) in your browser!

---

## 🧪 Testing & Quality Assurance

### Run Unit Tests (Backend)

```bash
docker compose exec backend pytest tests/unit -v
```

The test suite covers:
- Billing cycle & due date calculations (`test_billing.py`)
- Statement PDF parsers & normalizers (`test_parsers.py`)
- Payment settlement & analytics schemas (`test_payments_and_analytics.py`)
- RewardEngine, accelerator matching, and cap limits (`test_rewards.py`)
- Gmail query builders and token encryption (`test_email_service.py`)
- AI Assistant deterministic tool definitions (`test_assistant.py`)
- Document sliding chunking and relevance scoring (`test_documents.py`)
- CSV export and security headers (`test_data_export.py`)

---

## 💾 Database Backup & Restore

FinSight AI provides one-command CLI scripts for data protection:

```bash
# Create a compressed database backup in ./backups/
bash scripts/backup.sh

# Restore from a backup archive
bash scripts/restore.sh backups/finsight_backup_YYYYMMDD_HHMMSS.sql.gz
```

---

## 🔒 Security Principles

1. **Numeric(18, 4) Precision**: Financial values use Decimal numbers — floating-point arithmetic is prohibited.
2. **Zero PAN Storage**: Credit cards store only issuer, network, and last 4 digits (`**** 1234`). Full card numbers, PINs, and CVVs are never requested or stored.
3. **Encrypted Tokens**: Gmail OAuth tokens are encrypted at rest using Fernet symmetric encryption with PBKDF2 key derivation.
4. **Defensive Headers**: Built-in middleware enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict referrer policies.
5. **Data Sovereignty**: 1-click JSON and CSV export under Settings, with complete data purge functionality.

---

## 📜 License

Licensed under the MIT License. Contributions and PRs welcome!
