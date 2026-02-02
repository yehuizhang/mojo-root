# Visitor Logging Deployment Guide

## Changes Made

### 1. FastAPI Logging (mojo-api/api/main.py)
- ✅ Removed skip conditions - now logs ALL requests
- ✅ Logs: IP address, method, path, user-agent for every visitor

### 2. nginx Access Logs (mojo-infra/nginx/nginx.conf)
- ✅ Added `access_log /var/log/nginx/api_access.log main;` for API domain
- ✅ Added `access_log /var/log/nginx/web_access.log main;` for website domain
- ✅ Logs include: IP, timestamp, request, status, user-agent, referer

### 3. Filebeat Configuration (mojo-infra/config/filebeat.yml)
- ✅ Added `nginx-api-access` input for API visitor logs
- ✅ Added `nginx-web-access` input for website visitor logs
- ✅ Added `nginx-security` input for blocked requests
- ✅ All logs tagged with proper fields for Kibana filtering

## Deployment Steps

### Step 1: Restart nginx (Apply nginx.conf changes)
```bash
cd mojo-infra
docker compose -f docker-compose.ssl.yml restart nginx
```

### Step 2: Restart Filebeat (Apply filebeat.yml changes)
```bash
cd mojo-infra
docker compose -f docker-compose.logging.yml restart filebeat
```

### Step 3: Restart FastAPI (Apply main.py changes)
```bash
# If running locally (development)
cd mojo-api
# Stop current process (Ctrl+C)
bb dev

# If running in Docker (production)
cd mojo-api
bb down && bb up
```

### Step 4: Verify Logs are Being Created
```bash
# Check nginx logs
ls -lh /var/log/mojo/nginx/

# Should see:
# - api_access.log (NEW)
# - web_access.log (NEW)
# - blocked_http.log
# - blocked_origin.log
# - blocked_direct.log
# - error.log

# Tail API access logs
tail -f /var/log/mojo/nginx/api_access.log

# Tail website access logs
tail -f /var/log/mojo/nginx/web_access.log
```

### Step 5: Verify Filebeat is Collecting Logs
```bash
# Check Filebeat logs
docker logs filebeat --tail 50

# Should see messages like:
# "Harvester started for file: /var/log/mojo/nginx/api_access.log"
# "Harvester started for file: /var/log/mojo/nginx/web_access.log"
```

## Viewing Logs in Kibana

### Access Kibana
```
http://localhost:5601
```

### Create Index Pattern (First Time Only)
1. Go to **Management** → **Stack Management** → **Index Patterns**
2. Click **Create index pattern**
3. Index pattern: `mojo-logs-*`
4. Time field: `@timestamp`
5. Click **Create index pattern**

### View Visitor Logs

#### Filter by Log Type
In Kibana Discover:

**API Visitors:**
```
log_type: "api_access" AND domain: "api.yehuizhang.com"
```

**Website Visitors:**
```
log_type: "web_access" AND domain: "yehuizhang.com"
```

**Blocked/Malicious Requests:**
```
log_type: "security" AND security_event: "blocked"
```

**All nginx Logs:**
```
service_type: "nginx"
```

#### Key Fields to Display
Add these columns in Kibana Discover:
- `message` - Full log line with IP, request, status
- `log_type` - Type of log (api_access, web_access, security)
- `domain` - Which domain (api.yehuizhang.com or yehuizhang.com)
- `service_type` - Service name (nginx)

### Example Log Format

**nginx access log:**
```
192.168.1.100 - - [01/Feb/2026:10:30:45 +0000] "GET /zyh/finance HTTP/2.0" 200 1234 "https://yehuizhang.com/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
```

**FastAPI log (in ELK):**
```json
{
  "timestamp": "2026-02-01T10:30:45.123Z",
  "level": "INFO",
  "message": "Request: host=192.168.1.100, Method=GET, Path=/finance/dashboard, User-Agent=Mozilla/5.0..."
}
```

## Analyzing Visitor Data

### Find All Unique IPs
In Kibana, create visualization:
1. **Visualize** → **Create visualization** → **Data table**
2. Metrics: **Unique Count** of `message` (or parse IP field)
3. Buckets: **Terms** aggregation on IP addresses
4. Shows all unique visitor IPs

### Identify Suspicious Activity
Look for:
- High request rates from single IP
- Requests to non-existent paths (404s)
- Blocked requests in security logs
- Unusual user-agents (bots, scrapers)

### Create Alerts (Optional)
Set up Kibana alerts for:
- More than 100 requests/minute from single IP
- Multiple blocked requests from same IP
- Requests to sensitive paths

## Troubleshooting

### Logs Not Appearing in Kibana

**Check 1: Verify log files exist**
```bash
ls -lh /var/log/mojo/nginx/
tail /var/log/mojo/nginx/api_access.log
```

**Check 2: Verify Filebeat is running**
```bash
docker ps | grep filebeat
docker logs filebeat --tail 50
```

**Check 3: Check Elasticsearch connection**
```bash
curl -u elastic:${ELK_PASSWORD} "http://localhost:9200/mojo-logs-*/_count"
```

**Check 4: Restart logging stack**
```bash
cd mojo-infra
./build.sh logging down
./build.sh logging up
```

### Empty Log Files

**Check 1: Generate traffic**
```bash
# Visit your website
curl https://yehuizhang.com/

# Check API
curl https://api.yehuizhang.com/status
```

**Check 2: Verify nginx is writing logs**
```bash
docker exec nginx-proxy ls -lh /var/log/nginx/
```

## Log Retention

### Current Setup
- Logs stored in `/var/log/mojo/nginx/`
- Elasticsearch indices: `mojo-logs-YYYY.MM.DD`
- No automatic cleanup configured

### Recommended: Add Log Rotation
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/mojo-nginx

# Add:
/var/log/mojo/nginx/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker exec nginx-proxy nginx -s reopen
    endscript
}
```

## Summary

✅ **FastAPI**: Logs all requests with IP, method, path, user-agent
✅ **nginx**: Logs all successful requests to api_access.log and web_access.log
✅ **Filebeat**: Collects all logs and sends to Elasticsearch
✅ **Kibana**: View and analyze all visitor data

You can now track every visitor's IP address and investigate suspicious activity!
