# YouTube Automation Backend

Platform SaaS untuk mengelola multiple akun YouTube, mengotomatisasi live streaming, dan memanfaatkan AI untuk optimasi konten.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL dengan SQLAlchemy 2.0 (async)
- **Cache/Queue**: Redis dengan Celery
- **Migrations**: Alembic
- **Testing**: pytest + Hypothesis (property-based testing)

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL
- Redis

### 2. Setup Virtual Environment

```bash
# Windows
cd backend
scripts\setup_venv.bat

# Manual (semua OS)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` ke `.env` dan sesuaikan:

```bash
copy .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/youtube_automation
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-in-production
```

### 4. Setup Database

```bash
# Buat database di PostgreSQL
createdb youtube_automation

# Jalankan migrations
scripts\run_migrations.bat
# atau
alembic upgrade head
```

### 5. Run Development Server

```bash
# Windows
scripts\run_dev.bat

# Manual
uvicorn app.main:app --reload
```

Server akan berjalan di http://localhost:8000

- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc

### 6. Run Celery Worker (untuk background jobs)

```bash
# Windows
scripts\run_celery.bat

# Manual
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

### 7. Run Tests

```bash
# Windows
scripts\run_tests.bat

# Manual
pytest app/ -v --cov=app
```

## Project Structure

```
backend/
├── alembic/                 # Database migrations
│   ├── versions/            # Migration files
│   └── env.py               # Alembic config
├── app/
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings from env
│   │   ├── database.py      # SQLAlchemy setup
│   │   ├── celery_app.py    # Celery configuration
│   │   └── redis.py         # Redis client
│   ├── modules/             # Feature modules
│   │   ├── auth/            # Authentication
│   │   ├── account/         # YouTube accounts
│   │   ├── video/           # Video management
│   │   ├── stream/          # Live streaming
│   │   ├── ai/              # AI services
│   │   ├── analytics/       # Analytics
│   │   ├── moderation/      # Chat/comment moderation
│   │   ├── notification/    # Notifications
│   │   ├── billing/         # Billing
│   │   ├── agent/           # Worker agents
│   │   └── job/             # Job queue
│   └── main.py              # FastAPI app entry
├── scripts/                 # Helper scripts
├── .env                     # Environment variables
├── .env.example             # Example env file
├── requirements.txt         # Dependencies
└── pyproject.toml           # Project config
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `scripts\setup_venv.bat` | Setup virtual environment dan install dependencies |
| `scripts\run_dev.bat` | Jalankan development server |
| `scripts\run_celery.bat` | Jalankan Celery worker |
| `scripts\run_tests.bat` | Jalankan tests dengan coverage |
| `scripts\run_migrations.bat` | Jalankan database migrations |

## API Endpoints

### Health Check
- `GET /health` - Check API health status

### Authentication (Coming Soon)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/2fa/enable` - Enable 2FA
- `POST /api/v1/auth/2fa/verify` - Verify 2FA

### YouTube Accounts (Coming Soon)
- `GET /api/v1/accounts` - List connected accounts
- `POST /api/v1/accounts/connect` - Initiate OAuth
- `GET /api/v1/accounts/{id}` - Get account details

## Testing Strategy

Project ini menggunakan dual testing approach:

1. **Unit Tests**: Verify specific examples dan edge cases
2. **Property-Based Tests**: Verify universal properties dengan Hypothesis

Contoh property test untuk retry logic:
```python
@given(attempt=st.integers(min_value=1, max_value=20))
def test_delay_follows_exponential_pattern(self, attempt):
    """Delay SHALL follow exponential backoff formula."""
    config = RetryConfig(...)
    delay = config.calculate_delay(attempt)
    expected = initial_delay * (multiplier ** (attempt - 1))
    assert delay == min(expected, max_delay)
```

## Development Progress

Lihat `.kiro/specs/youtube-automation/tasks.md` untuk progress implementasi.

Current Phase: **Phase 1 - Project Setup & Core Infrastructure**
- [x] FastAPI project setup
- [x] Database & migrations
- [x] Redis & Celery setup
- [ ] Property tests for retry logic (in progress)
