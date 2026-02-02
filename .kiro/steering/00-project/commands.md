---
inclusion: always
---
# Essential Commands

## ⚠️ BEFORE YOU RUN ANY COMMAND IN MOJO-API ⚠️

**Are you running a Python command?** → Activate venv first: `source .venv/bin/activate && <command>`

**See "command not found: python"?** → You forgot to activate venv. Don't troubleshoot, just activate and retry.

---

## Local Development Environment

**IMPORTANT**: User runs mojo-api locally (NOT in Docker) using:
```bash
cd /Users/yehuizhang/repo/mojo/mojo-api
bb dev         # Runs FastAPI locally with uvicorn auto-reload
```

- FastAPI runs on local machine at http://localhost:8000
- Connects to Redis at 192.168.0.105:6380
- Logs appear directly in terminal (not Docker logs)
- Code changes auto-reload via uvicorn watch

## Python Virtual Environment

🚨 **CRITICAL - READ THIS FIRST** 🚨

**BEFORE running ANY Python command in mojo-api, you MUST activate the virtual environment:**

```bash
source .venv/bin/activate
# Wait a few seconds for activation to complete
# Then run your commands
```

### When Virtual Environment is Required

**ALWAYS activate venv for these commands:**
- `python -m pytest` (running tests)
- `python -m <anything>` (any Python module)
- `bb dev` (local development server)
- `python <script>.py` (running any Python script)
- Any command that imports Python packages

**Commands that DON'T need venv:**
- Pure Docker commands: `docker compose`, `docker ps`, `docker logs`
- Pure bash commands: `ls`, `cd`, `grep`, `cat`
- Build scripts that run in Docker: `bb up`, `bb down`

### Error Patterns That Mean "You Forgot to Activate Venv"

If you see ANY of these errors, it means you forgot to activate the venv:
- ❌ `command not found: python`
- ❌ `command not found: pytest`
- ❌ `ModuleNotFoundError: No module named 'fastapi'`
- ❌ `ModuleNotFoundError: No module named 'pytest'`
- ❌ Any import error when running Python in mojo-api

**Correct response:** Don't troubleshoot the error. Just activate venv and try again.

### Standard Pattern for Running Python Commands

**ALWAYS use this pattern:**
```bash
source .venv/bin/activate && <your-python-command>
```

**Examples:**
```bash
# Running tests
source .venv/bin/activate && python -m pytest api/test/ --ignore=chronos -q

# Running dev server
source .venv/bin/activate && bb dev

# Running a script
source .venv/bin/activate && python playground/option.py
```

**Why this matters**: Without activating the venv, Python won't find the installed dependencies and commands will fail.

## Build Commands

### mojo-api (Application Services)
```bash
bb dev         # LOCAL: Run FastAPI with uvicorn (NOT Docker)
bb up          # Production mode with rebuild (Docker)
bb down        # Stop all services
bb logs        # Show FastAPI logs (Docker only)
bb ps          # Show service status (Docker only)
```

### mojo-infra (Infrastructure Services)
```bash
./build.sh ssl up      # Start SSL services (nginx + certbot)
./build.sh logging up  # Start ELK stack
./build.sh redis up    # Start Redis services
```

## Service Startup Order
```bash
# 1. Infrastructure
cd mojo-infra && ./build.sh redis up && ./build.sh logging up

# 2. Applications  
cd mojo-api && bb up

# 3. SSL (optional)
cd mojo-infra && ./build.sh ssl up
```

## Development Workflow
```bash
# Local Development (User's Setup)
cd /Users/yehuizhang/repo/mojo/mojo-api && bb dev

# Production (Docker)
cd mojo-api && bb up
```

## Health Checks
```bash
# Service status
docker ps --format "table {{.Names}}\t{{.Status}}"

# API health
curl https://api.yehuizhang.com/status

# Log count
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/mojo-logs-*/_count"
```

## Troubleshooting
```bash
# Restart nginx (502 errors)
cd mojo-infra && docker compose -f docker-compose.ssl.yml restart nginx

# Clear CloudFront cache (stale content after deployment)
# Distribution ID: E27QEWNM1GENUR
aws cloudfront create-invalidation --distribution-id E27QEWNM1GENUR --paths "/*"

# Check invalidation status
aws cloudfront get-invalidation --distribution-id E27QEWNM1GENUR --id <INVALIDATION_ID>

# View logs (LOCAL DEVELOPMENT)
# Logs appear directly in terminal where 'bb dev' is running
# No need for 'docker logs' - user runs locally!

# View logs (Docker/Production)
bb logs
docker logs fastapi-app

# Check networks
docker network ls | grep mojo
```

## Docker Compose Patterns
```bash
# Development
docker compose -f docker-compose.app.yml up -d

# Production  
docker compose -f docker-compose.app.yml -f docker-compose.app.prod.yml up -d
```
