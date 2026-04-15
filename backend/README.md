# YouTube Automation Backend

FastAPI backend for the YouTube Automation platform. This service handles authentication, YouTube account connections, video library operations, video-to-live streaming, AI features, analytics, billing, admin operations, notifications, realtime support, and external integrations.

## Overview

Main stack:

- Python 3.11
- FastAPI
- SQLAlchemy async
- PostgreSQL
- Redis
- Celery
- Alembic
- OpenTelemetry + Prometheus

The application entry point is [app/main.py](/d:/Project/youtube-automation/backend/app/main.py:1). All primary API routes are mounted under `"/api/v1"`.

## API Modules

Active modules in `app/modules`:

- `auth`
- `account`
- `video`
- `stream`
- `ai`
- `analytics`
- `moderation`
- `monitoring`
- `agent`
- `job`
- `notification`
- `system_monitoring`
- `security`
- `billing`
- `payment_gateway`
- `integration`
- `admin`
- `blog`
- `support`
- `transcoding`

Currently registered route areas:

- `/auth`
- `/accounts`
- `/videos`
- `/videos/library`
- `/streams`
- `/stream-jobs`
- `/ai`
- `/analytics`
- `/moderation`
- `/monitoring`
- `/agents`
- `/jobs`
- `/notifications`
- `/system`
- `/security`
- `/billing`
- `/admin/payment-gateways`
- `/payments`
- `/integration`
- `/admin`
- `/blog`
- `/contact`
- `/support`

## Backend Capabilities

- JWT authentication, password reset, audit logging, and TOTP/2FA
- Multi-account YouTube OAuth
- Video upload, metadata management, bulk actions, folders/library, thumbnails, and YouTube publishing
- Stream creation and video-to-live automation
- Stream jobs with health WebSocket updates
- AI title, description, thumbnail, and chatbot features
- Analytics aggregation and dashboard data services
- Moderation rules and chatbot moderation
- Notification delivery and escalation flows
- Billing, subscriptions, metering, and feature gating
- Payment gateway abstraction for Stripe, PayPal, Midtrans, and Xendit
- API key auth, webhooks, rate limiting, and external integrations
- Admin tooling for users, quotas, compliance, support, backups, AI config, and system config
- Realtime support via WebSocket
- Security, auditability, tracing, metrics, and alerting

## Directory Structure

```text
backend/
├── app/
│   ├── core/
│   └── modules/
├── alembic/
│   └── versions/
├── scripts/
├── tests/
├── docs/
├── supervisor/
├── systemd/
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## Configuration

Primary configuration reference:

- [backend/.env.example](/d:/Project/youtube-automation/backend/.env.example:1)

Important variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_automation
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me
KMS_ENCRYPTION_KEY=32-byte-key
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REDIRECT_URI=http://localhost:8000/api/v1/accounts/oauth/callback
CORS_ORIGINS=["http://localhost:3000"]
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_PUBLISHABLE_KEY=...
STRIPE_WEBHOOK_SECRET=...
```

The backend configuration also covers:

- `local`, `s3`, and `minio` storage backends
- CDN support
- SMTP
- Telegram bot integration
- separate Celery broker/result backend settings
- moderation/chatbot timeouts
- stream health settings

Runtime settings are defined in [app/core/config.py](/d:/Project/youtube-automation/backend/app/core/config.py:1).

## Running Locally

### 1. Start service dependencies

From the repository root:

```bash
make dev-db
```

This starts PostgreSQL and Redis via `docker-compose.dev.yml`.

### 2. Install Python dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
copy .env.example .env
```

Then update the credentials and integration values as needed.

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Start the API server

```bash
uvicorn app.main:app --reload
```

Access:

- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Running Background Workers

Worker:

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

Beat:

```bash
cd backend
celery -A app.core.celery_app beat --loglevel=info
```

Windows helper scripts:

- `scripts\run_celery.bat`
- `scripts\run_celery_beat.bat`
- `scripts\run_celery_all.bat`

Linux/macOS helper scripts:

- `scripts/run_celery_prod.sh`
- `scripts/run_celery_beat_prod.sh`

## Docker

From the repository root, the backend is started through:

```bash
make prod
```

Relevant services:

- `backend`
- `celery-worker`
- `celery-beat`
- `postgres`
- `redis`

Optional Celery monitoring:

```bash
make prod-monitor
```

Flower is available at `http://localhost:5555`.

## Operational Scripts

The `scripts/` directory includes a large number of operational utilities, such as:

- local dev setup and run scripts
- migrations
- admin setup
- seed data for plans, announcements, compliance, and moderation rules
- Stripe, PayPal, Midtrans, and Xendit configuration
- backup and billing utilities
- video conversion utilities
- data repair and debugging scripts

## Testing

The backend test suite includes:

- unit tests
- integration tests
- end-to-end flows
- property-based tests with Hypothesis

Visible coverage areas:

- auth
- account
- admin
- agent
- ai
- analytics
- billing
- integration
- job
- moderation
- monitoring
- notification
- payment gateway
- stream
- transcoding
- video
- e2e scenarios

Run tests:

```bash
cd backend
pytest
```

Or use the helper script:

```bash
scripts\run_tests.bat
```

## Observability

Backend startup enables:

- JSON logging
- request logging middleware
- correlation ID middleware
- tracing middleware
- metrics middleware
- usage metering middleware
- default alert thresholds

This is configured in [app/main.py](/d:/Project/youtube-automation/backend/app/main.py:1).

## Notes

- `backend/.env.example` is currently a more accurate backend setup reference than the root `.env.example`.
- Additional deployment documentation is available in [../DEPLOYMENT.md](/d:/Project/youtube-automation/DEPLOYMENT.md:1).
