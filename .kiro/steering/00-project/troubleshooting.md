---
inclusion: always
---
# Common Issues & Solutions

## 502 Bad Gateway

**Problem**: nginx keeps stale connections after container restart

**Solution**: 
```bash
# Quick fix - restart nginx
cd mojo-infra && docker compose -f docker-compose.ssl.yml restart nginx

# Permanent fix - configure upstream retry in nginx.conf
upstream fastapi {
    server fastapi-app:8000 max_fails=3 fail_timeout=30s;
}
```

## Stale Content After Deployment

**Problem**: CloudFront caches old content, users see outdated pages

**Solution**:
```bash
# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E27QEWNM1GENUR --paths "/*"

# Check invalidation status
aws cloudfront get-invalidation --distribution-id E27QEWNM1GENUR --id <INVALIDATION_ID>

# Wait 1-3 minutes, then hard refresh browser
# Mac: Cmd+Shift+R
# Windows/Linux: Ctrl+Shift+R
```

**When to invalidate**:
- After deploying new code
- After changing environment variables
- After updating static assets
- When users report seeing old content

## CORS Errors with Credentials

**Problem**: `allow_origins=["*"]` with `allow_credentials=True` is not allowed

**Solution**:
```python
# FastAPI - specify exact origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yehuizhang.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

```nginx
# nginx - handle OPTIONS preflight separately
if ($request_method = 'OPTIONS') {
    add_header 'Access-Control-Allow-Origin' 'https://yehuizhang.com' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    add_header 'Access-Control-Max-Age' 600 always;
    return 204;
}
```

**Note**: 
- nginx must handle OPTIONS preflight requests separately (bypass CloudFront verification)
- CORS only affects browsers, not Postman/curl

## Next.js "Failed to fetch" Errors

**Checklist**:
1. Check browser console for actual error
2. Look for CORS errors
3. Verify API URL in network tab
4. Check if CloudFront cache is stale
5. Verify environment variables:
   ```bash
   docker exec nextjs-app printenv | grep NEXT_PUBLIC
   ```

## Container Restarts

**After restarting Next.js container**:
```bash
# 1. Restart nginx
docker compose -f docker-compose.ssl.yml restart nginx

# 2. Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E27QEWNM1GENUR --paths "/*"

# 3. Hard refresh browser
```

## Python Virtual Environment Issues

**Problem**: Commands fail with "module not found" errors

**Solution**:
```bash
# Always activate venv first
source .venv/bin/activate

# Wait a few seconds for activation
# Then run your commands
```

**Applies to**:
- Running tests: `python -m pytest api/test/ --ignore=chronos -q`
- Running dev server: `bb dev`
- Any Python commands in mojo-api directory

## Redis Connection Issues

**Problem**: FastAPI can't connect to Redis

**Check**:
```bash
# 1. Verify Redis is running
docker ps | grep redis

# 2. Check Redis connectivity
redis-cli -h 192.168.0.105 -p 6380 ping

# 3. Verify environment variables
echo $REDIS_HOST
echo $REDIS_PORT
```

**Solution**:
```bash
# Start Redis if not running
cd mojo-infra && ./build.sh redis up
```

## Build Script Issues

**Problem**: `./build.sh web down` shows "Command is not supported"

**Solution**: Ensure two-word commands have `exit 0` after execution to prevent falling through to second case statement

## Health Check Failures

**Alpine-based images**: Use `wget` instead of `curl` (curl not available in alpine)

```dockerfile
# Correct health check for Next.js
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1
```

## ELK Stack Issues

**Problem**: Logs not appearing in Kibana

**Check**:
```bash
# 1. Verify Filebeat is running (production only)
docker ps | grep filebeat

# 2. Check log files exist
ls -la /var/log/mojo/  # Production
ls -la ./_local/logs/  # Development

# 3. Check Elasticsearch
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/_cat/indices?v"

# 4. Check log count
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/mojo-logs-*/_count"
```

**Solution**:
```bash
# Restart logging stack
cd mojo-infra && ./build.sh logging down && ./build.sh logging up
```

## Network Issues

**Problem**: Services can't communicate

**Check**:
```bash
# Verify networks exist
docker network ls | grep mojo

# Check which containers are on which networks
docker network inspect mojo_app
```

**Solution**:
```bash
# Recreate networks
docker compose down
docker compose up -d
```
