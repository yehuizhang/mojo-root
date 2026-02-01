# Essential Commands

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
