# YouTube Automation Platform

A full-stack SaaS platform for YouTube channel operations: multi-account connection, video management, video-to-live streaming, AI-assisted content, analytics, billing, admin operations, observability, and developer integrations.

## Product Overview

This repository is not just a video uploader. Based on the backend modules, frontend routes, migrations, test suite, and operational scripts, the application has evolved into a broader YouTube operations platform with three major areas:

- Creator operations: account management, video library, streaming, moderation, analytics
- Business operations: billing, subscriptions, payment gateways, support, notifications
- Platform operations: admin panel, observability, backups, compliance, API keys, webhooks

This monorepo contains:

- `backend/`: FastAPI + PostgreSQL + Redis + Celery
- `frontend/`: Next.js 14 + TypeScript + Tailwind + Radix UI
- `docker-compose.yml`: main runtime stack
- `docker-compose.dev.yml`: development stack for database services and GUI tools
- `DEPLOYMENT.md`: deployment and worker operations guide

## Core Features

### User-facing

- Login, registration, password reset, and 2FA/TOTP
- Multi-account YouTube connection via OAuth
- Analytics dashboards for subscribers, views, and watch time
- Video management: upload, import, metadata editing, thumbnails, templates, folders, bulk actions
- Dedicated video library endpoints separate from general video routes
- Video-to-live streaming for scheduled or recurring live streams
- Stream jobs, history, analytics, resource dashboards, and real-time health monitoring
- Moderation tools and chatbot-related features
- Notification center, support chat, and user settings
- Billing, subscriptions, checkout, usage tracking, and payment history

### Admin-facing

- User management and impersonation-related flows
- Subscription and billing administration
- Payment gateway configuration and statistics
- Compliance, quotas, audit logs, backups, security, and system configuration
- Blog, announcements, AI configuration, and support operations

### Developer-facing

- API documentation inside the dashboard
- Scoped API key management
- Webhooks
- Rate limiting
- JWT and API key authentication

## Architecture

### Backend

The backend is bootstrapped from [backend/app/main.py](/d:/Project/youtube-automation/backend/app/main.py:1). All major routers are mounted under `"/api/v1"`.

Active API areas:

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

Backend capabilities visible from the current module and router layout:

- JWT auth, TOTP, audit, password reset
- YouTube OAuth and account management
- Video metadata, storage, upload, conversion, and usage tracking
- Stream lifecycle management and stream jobs with health WebSocket support
- AI generation, thumbnails, and chatbot services
- Analytics, moderation, notifications, billing, and support
- API keys, webhooks, rate limiting, and external integrations
- Admin operations, compliance, backups, and system monitoring

### Frontend

The frontend uses the Next.js App Router and is organized into:

- public marketing pages
- auth area
- user dashboard
- admin dashboard
- dashboard docs for API integration

Main route areas visible in `frontend/src/app`:

- `/`
- `/about`
- `/contact`
- `/careers`
- `/privacy`
- `/terms`
- `/blog`
- `/dashboard/*`
- `/admin/*`

The frontend also includes dedicated realtime hooks and clients for:

- notifications
- support messaging
- stream health updates
- WebSocket client abstraction

### Async and Background Processing

For non-request/response workloads, the platform uses:

- Redis
- Celery worker
- Celery beat
- Flower as optional monitoring

Based on the current modules, background processing is used for at least:

- stream jobs
- analytics tasks
- billing tasks
- notifications
- integrations
- transcoding and video processing

## Technology Stack

### Backend

- Python 3.11
- FastAPI
- SQLAlchemy async
- Alembic
- PostgreSQL
- Redis
- Celery
- OpenAI SDK
- Boto3
- Pillow
- ReportLab
- Prometheus client
- OpenTelemetry

### Frontend

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Radix UI
- Framer Motion
- Recharts
- Vitest

## Repository Structure

```text
youtube-automation/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   └── modules/
│   ├── alembic/
│   ├── scripts/
│   ├── tests/
│   ├── docs/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   ├── public/
│   ├── docs/
│   ├── Dockerfile
│   └── package.json
├── docs/
├── storage/
├── docker-compose.yml
├── docker-compose.dev.yml
├── DEPLOYMENT.md
└── Makefile
```

## Database and Domain Model

The schema is managed with Alembic. From the migration history, the domain model already covers:

- auth and users
- YouTube accounts
- videos, playlists, streams, simulcast, and transcoding
- AI, moderation, and chatbot features
- analytics
- monitoring
- job queue and notifications
- billing, plans, subscriptions, and payment gateways
- admin, support, compliance, and audit logs
- blog

This is a fairly broad application model rather than an early-stage bootstrap project.

## Running the Application

### Option 1: Full stack via Docker

Prerequisites:

- Docker
- Docker Compose

Setup:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
make prod
```

Services started:

- `postgres`
- `redis`
- `backend`
- `celery-worker`
- `celery-beat`
- `frontend`

Access:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Optional monitoring:

```bash
make prod-monitor
```

Flower:

- `http://localhost:5555`

### Option 2: Hybrid local development

Start database services with Docker, then run the backend and frontend locally.

```bash
make dev-db
```

Backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Celery worker:

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

Frontend:

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

### Option 3: Development tools

```bash
make dev-tools
```

Additional services:

- pgAdmin: `http://localhost:5050`
- Redis Commander: `http://localhost:8081`

## Common Commands

### Makefile

- `make dev-db`
- `make dev-tools`
- `make dev-stop`
- `make prod`
- `make prod-scale`
- `make prod-monitor`
- `make prod-stop`
- `make build`
- `make logs`
- `make logs-worker`
- `make logs-beat`
- `make migrate`

### Backend scripts

The `backend/scripts` directory contains additional operational utilities, including:

- local dev and virtualenv setup
- Celery worker and beat runners
- migrations
- seed data scripts
- admin setup
- payment gateway configuration
- backup, billing, conversion, and debugging utilities

## Environment Variables

### Backend

Primary backend reference:

- [backend/.env.example](backend/.env.example)

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

The backend also supports:

- local storage
- S3 / MinIO / S3-compatible storage
- CDN
- SMTP
- Telegram bot integration
- separate Celery broker/result backends

### Frontend

Primary frontend reference:

- [frontend/.env.local.example](frontend/.env.local.example)

Minimum configuration:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=YouTube Automation Platform
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## API, Integrations, and Realtime

Built-in backend documentation endpoints:

- `GET /health`
- `GET /docs`
- `GET /redoc`

Integration surface visible in the backend and dashboard docs:

- scoped API keys
- webhook management
- rate limit status
- API docs inside the user dashboard

Realtime capabilities visible in the current source:

- stream job health WebSocket
- support WebSocket for users
- support WebSocket for admins

This means the platform supports live operational updates in areas where status changes matter.

## Testing

The backend test suite is fairly broad and includes:

- unit tests
- integration tests
- end-to-end scenarios
- property-based tests with Hypothesis

Visible test coverage areas:

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
- e2e flows

Run backend tests:

```bash
cd backend
pytest
```

Run frontend tests:

```bash
cd frontend
npm test
```

## Related Documentation

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [frontend/docs/E2E_TESTING.md](frontend/docs/E2E_TESTING.md)
