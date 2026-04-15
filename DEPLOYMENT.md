# Deployment Guide - YouTube Automation Platform

## Table of Contents
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Celery Configuration](#celery-configuration)
- [Scaling](#scaling)
- [Monitoring](#monitoring)

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone and Configure
```bash
git clone <repository-url>
cd youtube-automation

# Copy environment file
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start Services
```bash
# Development (database only)
make dev-db

# Production (all services)
make prod
```

---

## Development Setup

### Option 1: Docker for Database Only
```bash
# Start PostgreSQL and Redis
make dev-db

# Run backend locally
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run Celery locally (separate terminal)
celery -A app.core.celery_app worker --beat --loglevel=info --pool=threads

# Run frontend locally (separate terminal)
cd frontend
npm install
npm run dev
```

### Option 2: Full Docker Development
```bash
make dev-tools  # Includes pgAdmin and Redis Commander
```

Access:
- pgAdmin: http://localhost:5050 (admin@admin.com / admin)
- Redis Commander: http://localhost:8081

---

## Production Deployment

### Docker Compose (Recommended)
```bash
# Build images
make build

# Start all services
make prod

# Or with monitoring (Flower)
make prod-monitor
```

### Manual Deployment (Linux Server)

#### 1. Install Dependencies
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql redis-server ffmpeg nginx supervisor
```

#### 2. Setup Application
```bash
cd /app
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configure Supervisor
```bash
# Copy supervisor config
sudo cp backend/supervisor/celery.conf /etc/supervisor/conf.d/

# Create log directory
sudo mkdir -p /var/log/celery
sudo chown www-data:www-data /var/log/celery

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
```

#### 4. Configure Systemd (Alternative to Supervisor)
```bash
# Copy service files
sudo cp backend/systemd/celery-worker.service /etc/systemd/system/
sudo cp backend/systemd/celery-beat.service /etc/systemd/system/

# Create directories
sudo mkdir -p /var/run/celery /var/log/celery /var/lib/celery
sudo chown www-data:www-data /var/run/celery /var/log/celery /var/lib/celery

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
```

---

## Celery Configuration

### Understanding Worker vs Beat

| Component | Purpose | Instances |
|-----------|---------|-----------|
| **Worker** | Executes tasks | Multiple OK |
| **Beat** | Schedules periodic tasks | **Only 1!** |

### Windows Development
```batch
REM Option 1: Separate processes (2 terminals)
scripts\run_celery.bat      REM Worker (Terminal 1)
scripts\run_celery_beat.bat REM Beat (Terminal 2)

REM Option 2: Combined (auto-opens 2 windows)
scripts\run_celery_all.bat
```

> **Note**: Windows tidak support `--beat` flag dalam satu proses.
> Script `run_celery_all.bat` akan membuka 2 window secara otomatis.

### Linux/Mac Development
```bash
# Option 1: Separate processes
./scripts/run_celery_prod.sh      # Worker
./scripts/run_celery_beat_prod.sh # Beat

# Option 2: Combined
celery -A app.core.celery_app worker --beat --loglevel=info
```

### Pool Types

| Pool | Best For | Platform |
|------|----------|----------|
| `prefork` | CPU-bound tasks | Linux/Mac |
| `threads` | I/O-bound tasks | All (Windows compatible) |
| `gevent` | High concurrency | Linux/Mac |
| `solo` | Debugging only | All |

---

## Scaling

### Horizontal Scaling (Multiple Workers)
```bash
# Docker Compose
docker-compose up -d --scale celery-worker=4

# Supervisor (edit numprocs)
[program:celery-worker]
numprocs=4
```

### Vertical Scaling (More Concurrency)
```bash
# Increase concurrency per worker
celery -A app.core.celery_app worker --concurrency=8
```

### Recommended Configuration

| Streams | Workers | Concurrency | Total Capacity |
|---------|---------|-------------|----------------|
| 1-10 | 1 | 4 | 4 tasks |
| 10-50 | 2 | 4 | 8 tasks |
| 50-100 | 4 | 4 | 16 tasks |
| 100+ | 8+ | 4 | 32+ tasks |

---

## Monitoring

### Flower (Celery Monitoring)
```bash
# Start with monitoring profile
make prod-monitor

# Access Flower
open http://localhost:5555
```

### Health Checks
```bash
# Check worker status
celery -A app.core.celery_app inspect active

# Check scheduled tasks
celery -A app.core.celery_app inspect scheduled

# Check registered tasks
celery -A app.core.celery_app inspect registered
```

### Logs
```bash
# Docker
make logs-worker
make logs-beat

# Supervisor
tail -f /var/log/celery/worker-00.log
tail -f /var/log/celery/beat.log

# Systemd
journalctl -u celery-worker -f
journalctl -u celery-beat -f
```

---

## Troubleshooting

### Tasks Not Executing
1. Check Redis connection: `redis-cli ping`
2. Check worker is running: `celery -A app.core.celery_app inspect active`
3. Check task is registered: `celery -A app.core.celery_app inspect registered`

### Beat Running Multiple Times
- **Cause**: Multiple beat instances
- **Fix**: Ensure only 1 beat process runs

### Worker Blocking
- **Cause**: Using `--pool=solo` with long-running tasks
- **Fix**: Use `--pool=threads` or `--pool=prefork`

### WebSocket Not Connecting
1. Check backend is running
2. Check URL: `ws://localhost:8000/api/v1/stream-jobs/{id}/health/ws`
3. Check browser console for errors

---

## Environment Variables

See `.env.example` for all available configuration options.

### Required for Production
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
SECRET_KEY=your-secure-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```
