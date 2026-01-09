# Essential Commands

## Build Commands

### mojo-api (Application Services)
```bash
bb up          # Production mode with rebuild
bb dev         # Development mode with logs  
bb down        # Stop all services
bb logs        # Show FastAPI logs
bb ps          # Show service status
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
# Development
cd mojo-api && bb dev

# Production
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

# View logs
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
