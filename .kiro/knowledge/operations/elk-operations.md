# ELK Stack Operations Guide

## Architecture
```
FastAPI App → Log Files → Filebeat → Elasticsearch → Kibana
```

## Quick Start
```bash
# Infrastructure
cd mojo-infra && ./build.sh redis up && ./build.sh logging up

# Applications  
cd mojo-api && docker compose -f docker-compose.app.yml -f docker-compose.app.prod.yml up -d

# Access Kibana: http://localhost:5601 (elastic / ${ELK_PASSWORD})
```

## Health Checks
```bash
# Service status
docker ps --format "table {{.Names}}\t{{.Status}}"

# Log count
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/mojo-logs-*/_count"

# Elasticsearch health
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/_cluster/health"

# Filebeat test
docker exec filebeat filebeat test config
docker exec filebeat filebeat test output
```

## Troubleshooting

### No Logs Appearing
1. Check application logging: `docker exec fastapi-app ls -la /var/log/mojo/`
2. Check Filebeat: `docker logs filebeat | grep harvester`
3. Check Elasticsearch: `curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/_cat/indices?v"`

### Service Won't Start
1. Fix permissions: `sudo chown -R 1000:1000 _local/elasticsearch_data/`
2. Check ports: `netstat -tulpn | grep -E "(9200|5601)"`
3. Reduce memory: `ES_JAVA_OPTS=-Xms512m -Xmx512m`

### Field Mapping Errors
Use custom field names in filebeat.yml:
```yaml
fields:
  app_name: fastapi-app  # Not 'service'
  environment: production # Not 'env'
```

## Maintenance
```bash
# Cleanup logs
curl -X DELETE -u elastic:${ELK_PASSWORD} "http://localhost:9200/mojo-logs-2025.01.01"

# Backup data
tar -czf elasticsearch-backup-$(date +%Y%m%d).tar.gz _local/elasticsearch_data/

# Monitor performance
docker stats --no-stream
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/_nodes/stats"
```

## Docker Compose Patterns
```bash
# Development
docker compose -f docker-compose.app.yml up -d

# Production
docker compose -f docker-compose.app.yml -f docker-compose.app.prod.yml up -d
```

## Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```
