# FlowPilot AI - Production Deployment Guide

This guide details the end-to-end production deployment process, system architecture, background worker supervision, database migration workflow, and disaster recovery procedures for **FlowPilot AI**.

---

## 1. Production Architecture Overview

FlowPilot AI follows an enterprise micro-services and asynchronous event-driven pattern:

```
                  ┌─────────────────────────────────────┐
                  │        HTTPS Reverse Proxy          │
                  │   (Nginx / Caddy / Cloudflare)      │
                  └──────────────────┬──────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
                 ▼                                       ▼
    ┌─────────────────────────┐             ┌─────────────────────────┐
    │ Next.js 14 Web UI App   │             │ FastAPI Gateway Backend │
    │  (Static + SSR Node)    │             │  (Port 8000 / Gunicorn) │
    └─────────────────────────┘             └────────────┬────────────┘
                                                         │
         ┌───────────────────┬───────────────────────────┼───────────────────────────┐
         │                   │                           │                           │
         ▼                   ▼                           ▼                           ▼
┌─────────────────┐ ┌──────────────────┐    ┌─────────────────────────┐  ┌─────────────────────────┐
│ PostgreSQL 15+  │ │  Redis 7 Cache   │    │ Background Job Workers  │  │ LLM & Integration APIs  │
│  (Persistent)   │ │  & Rate Limiter  │    │  (Async Automation)     │  │ (Gemini / Anthropic /   │
└─────────────────┘ └──────────────────┘    └─────────────────────────┘  │  GitHub / Slack / etc.) │
                                                                         └─────────────────────────┘
```

---

## 2. Environment Prerequisites

- **Host OS**: Linux (Ubuntu 22.04 LTS recommended) / Docker Engine 24.0+
- **Python**: Python 3.11 or Python 3.12
- **Node.js**: Node.js 18 LTS or Node.js 20 LTS
- **Database**: PostgreSQL 15+ with SSL enabled
- **Cache / Event Bus**: Redis 7.0+ with password authentication
- **Process Manager**: Docker Compose or Systemd + Supervisor

---

## 3. Step-by-Step Production Setup

### Step 1: Clone Repository & Create Production Environment Files
```bash
cd /opt/flowpilot
cp backend/.env.example backend/.env.production
cp frontend/.env.example frontend/.env.production
```

Configure `backend/.env.production` with non-default production credentials (see `ENVIRONMENT.md` for variable guidelines).

### Step 2: Database Initialization & Migrations
```bash
cd /opt/flowpilot/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run SQLAlchemy schema creation & database migrations
python -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"
```

### Step 3: Production Docker Deployment
```bash
# Launch multi-container production cluster
docker-compose -f docker-compose.prod.yml up -d --build
```

#### Production `docker-compose.prod.yml` Reference:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: flowpilot-db
    restart: always
    environment:
      POSTGRES_DB: flowpilot_prod
      POSTGRES_USER: flowpilot_app
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flowpilot_app -d flowpilot_prod"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: flowpilot-redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: flowpilot-api
    restart: always
    env_file: ./backend/.env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ready"]
      interval: 15s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: flowpilot-ui
    restart: always
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

---

## 4. Background Worker Supervision (Systemd)

To monitor and automatically restart background task workers:

Create `/etc/systemd/system/flowpilot-worker.service`:
```ini
[Unit]
Description=FlowPilot AI Background Automation Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=flowpilot
WorkingDirectory=/opt/flowpilot/backend
ExecStart=/opt/flowpilot/backend/venv/bin/python -m app.services.automation_service
Restart=always
RestartSec=5
Environment=ENVIRONMENT=production

[Install]
WantedBy=multi-user.target
```

Enable and start worker service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable flowpilot-worker
sudo systemctl start flowpilot-worker
sudo systemctl status flowpilot-worker
```

---

## 5. Health, Readiness, and Version Probes

The system provides 3 container orchestrator probes:

| Route | Endpoint | Purpose | Expected Response |
| :--- | :--- | :--- | :--- |
| **Liveness** | `GET /health` | Validates process HTTP readiness | `HTTP 200 {"status": "active"}` |
| **Readiness** | `GET /ready` | Validates PostgreSQL DB & Redis connectivity | `HTTP 200 {"status": "ready", "database": "connected"}` |
| **Version** | `GET /version` | Returns application build metadata | `HTTP 200 {"version": "1.0.0", "buildSha": "..."}` |

---

## 6. Database Backup & Disaster Recovery Strategy

### Automated Nightly Database Dump Script (`pg_backup.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/flowpilot"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="$BACKUP_DIR/flowpilot_backup_$TIMESTAMP.sql.gz"

mkdir -p $BACKUP_DIR

# Execute compressed PostgreSQL dump
PGPASSWORD="${DATABASE_PASSWORD}" pg_dump -h localhost -U flowpilot_app flowpilot_prod | gzip > $FILENAME

# Retain backups for 30 days
find $BACKUP_DIR -name "flowpilot_backup_*.sql.gz" -mtime +30 -delete

echo "Backup created successfully: $FILENAME"
```

### Database Recovery Procedure:
```bash
# Gunzip and restore PostgreSQL dump
gunzip -c /var/backups/flowpilot/flowpilot_backup_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -U flowpilot_app -d flowpilot_prod
```
