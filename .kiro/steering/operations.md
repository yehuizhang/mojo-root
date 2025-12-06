# Operations Guide

## Logging & Monitoring

### ELK Stack Architecture

```
FastAPI App → Log Files → Filebeat → Elasticsearch → Kibana
     ↓           ↓          ↓           ↓           ↓
  /var/log/   *.log     Harvester   Index      Visualize
```

### Quick Start Commands

#### Development Environment

```bash
# Start infrastructure services (from mojo-infra)
cd mojo-infra
./build.sh redis up
./build.sh logging up

# Start applications (from mojo-api)
cd mojo-api
./build.sh dev
```

#### Production Environment with Logging

```bash
# Start infrastructure services (from mojo-infra)
cd mojo-infra
./build.sh redis up
./build.sh logging up
./build.sh ssl up

# Start applications with logging (from mojo-api)
cd mojo-api
docker compose -f docker-compose.app.yml -f docker-compose.app.prod.yml up -d

# Access Kibana
open http://localhost:5601
# Login: elastic / ${ELK_PASSWORD}
```

### Health Checks

#### Quick Status Check

```bash
# Check all services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check log count
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/mojo-logs-*/_count"
```

#### Detailed Health Check

```bash
# Elasticsearch health
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/_cluster/health"

# Kibana status
curl "http://localhost:5601/api/status"

# Filebeat configuration test
docker exec filebeat filebeat test config
docker exec filebeat filebeat test output
```

### Common Operations

#### View Recent Logs

```bash
# Via Elasticsearch API
curl -u elastic:${ELK_PASSWORD} \
  "http://localhost:9200/mojo-logs-*/_search?size=5&sort=@timestamp:desc&pretty"

# Via Kibana
# Go to Analytics → Discover → Select mojo-logs-* data view
```

#### Generate Test Logs

```bash
# Create API traffic
for i in {1..10}; do
  curl "http://localhost:58080/status"
  curl "http://localhost:58080/"
done
```

#### Restart Logging Pipeline

```bash
# Restart just Filebeat
docker compose -f docker-compose.app.yml -f docker-compose.app.prod.yml restart filebeat

# Restart entire ELK stack
docker compose -f docker-compose.infra.yml restart elasticsearch kibana
```

### Troubleshooting

#### No Logs Appearing

1. **Check application logging**:
   ```bash
   docker exec fastapi-app ls -la /var/log/mojo/
   docker exec fastapi-app env | grep -E "(STAGE|APP_NAME)"
   ```

2. **Check Filebeat harvesting**:
   ```bash
   docker logs filebeat --tail 20
   docker logs filebeat | grep -E "(harvester|published)"
   ```

3. **Check Elasticsearch**:
   ```bash
   curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/_cat/indices?v"
   docker logs elasticsearch --tail 20
   ```

#### Service Won't Start

1. **Permission issues**:
   ```bash
   # Fix Elasticsearch data permissions
   sudo chown -R 1000:1000 _local/elasticsearch_data/
   
   # Filebeat config permissions handled by init container
   ```

2. **Port conflicts**:
   ```bash
   # Check port usage
   netstat -tulpn | grep -E "(9200|5601)"
   
   # Change ports in .env if needed
   ```

3. **Memory issues**:
   ```bash
   # Check available memory
   free -h
   
   # Reduce Elasticsearch memory if needed
   ES_JAVA_OPTS=-Xms512m -Xmx512m
   ```

#### Field Mapping Errors

```bash
# Common error: ECS field conflicts
# Solution: Use custom field names in filebeat.yml
fields:
  app_name: fastapi-app  # Not 'service'
  environment: production # Not 'env'
```

### Maintenance

#### Log Cleanup

```bash
# Docker logs are auto-rotated (10MB, 3 files)
# Elasticsearch indices can be cleaned manually:
curl -X DELETE -u elastic:${ELK_PASSWORD} "http://localhost:9200/mojo-logs-2025.01.01"
```

#### Backup Important Data

```bash
# Backup Elasticsearch data
tar -czf elasticsearch-backup-$(date +%Y%m%d).tar.gz _local/elasticsearch_data/

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env filebeat.yml docker-compose.*.yml
```

#### Performance Monitoring

```bash
# Check resource usage
docker stats --no-stream

# Monitor Elasticsearch performance
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/_nodes/stats"

# Check Filebeat metrics
docker logs filebeat | grep "Non-zero metrics" | tail -5
```

## Docker Compose Patterns

### File Organization

**mojo-api** (Application Services):
- `docker-compose.app.yml`: Base application services
- `docker-compose.app.dev.yml`: Development overrides
- `docker-compose.app.prod.yml`: Production overrides (logging, health checks, resources)

**mojo-infra** (Infrastructure Services):
- `docker-compose.ssl.yml`: SSL/nginx services
- `docker-compose.logging.yml`: ELK stack services
- `docker-compose.redis.yml`: Database services (Redis)

### Environment-Specific Deployment

**Application Services** (from mojo-api):
```bash
# Development
docker compose -f docker-compose.app.yml up -d

# Production
docker compose -f docker-compose.app.yml -f docker-compose.app.prod.yml up -d
```

**Infrastructure Services** (from mojo-infra):
```bash
# SSL/Nginx
docker compose -f docker-compose.ssl.yml up -d

# Logging (ELK)
docker compose -f docker-compose.logging.yml up -d

# Databases (Redis)
docker compose -f docker-compose.redis.yml up -d
```

### Resource Management

```yaml
# Production resource limits example
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Health Check Patterns

```yaml
# Application health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/status"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# Database health check
healthcheck:
  test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -q 'green\\|yellow'"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 30s
```

## Security Considerations

### Access Control

- Elasticsearch requires authentication (elastic user)
- Kibana uses kibana_system user
- All passwords managed via environment variables
- Network isolation via Docker bridge

### File Permissions

- Filebeat config must be owned by root (handled by init container)
- Elasticsearch data owned by UID 1000
- Log files readable by filebeat user

### Network Security

- Services communicate via internal Docker network
- Only necessary ports exposed to host
- No hardcoded credentials in compose files

## Monitoring and Alerting

### Key Metrics to Monitor

- Log ingestion rate (events/second)
- Elasticsearch cluster health
- Disk usage for log storage
- Container resource usage
- Application error rates

### Simple Health Check Script

```bash
#!/bin/bash
# health-check.sh

# Check service health
docker ps --filter "health=healthy" | grep -q elasticsearch || echo "❌ Elasticsearch unhealthy"
docker ps --filter "health=healthy" | grep -q kibana || echo "❌ Kibana unhealthy"
docker ps | grep -q "filebeat.*Up" || echo "❌ Filebeat not running"

# Check log flow
count=$(curl -s -u elastic:$ELK_PASSWORD "http://localhost:9200/mojo-logs-*/_count" | jq -r '.count // 0')
echo "📊 Total logs: $count"

# Check recent activity (last 5 minutes)
recent=$(curl -s -u elastic:$ELK_PASSWORD "http://localhost:9200/mojo-logs-*/_search" \
  -H "Content-Type: application/json" \
  -d '{"query":{"range":{"@timestamp":{"gte":"now-5m"}}},"size":0}' | jq -r '.hits.total.value // 0')
echo "🕐 Recent logs (5min): $recent"
```

## Emergency Procedures

### Complete System Reset

```bash
# Stop all services
docker compose -f docker-compose.app.yml -f docker-compose.app.prod.yml down
docker compose -f docker-compose.infra.yml down

# Clear data (DESTRUCTIVE)
sudo rm -rf _local/elasticsearch_data/*
docker volume prune -f

# Restart from scratch
docker compose -f docker-compose.infra.yml up -d
# Wait for healthy status
docker compose -f docker-compose.app.yml -f docker-compose.app.prod.yml up -d
```

### Filebeat Recovery

```bash
# Clear filebeat registry
docker volume rm mojo-py_filebeat_config

# Restart filebeat
docker-compose -f docker-compose.app.yml -f docker-compose.app.prod.yml up -d filebeat
```

This operations guide provides the essential knowledge for managing the Mojo platform's logging infrastructure and
Docker-based deployment.