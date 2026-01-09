# SSL/HTTPS Troubleshooting Guide

## Critical Issues and Solutions

### Docker Compose V2 Syntax
- **Issue**: Used deprecated `docker-compose` command
- **Solution**: Always use `docker compose` (V2 syntax)

### Build Script Commands  
- **Issue**: Used hyphens in commands (`ssl-setup`)
- **Solution**: Use spaces (`ssl setup`)

### Service Architecture
- **Issue**: SSL scripts tried to manage application services
- **Solution**: SSL commands only manage SSL services
- **Architecture**: Infrastructure → Application → SSL layers

### Docker Volume Mount Timing
- **Issue**: Created directories after container startup
- **Solution**: Create directory structure BEFORE `docker compose up`
- **Root Cause**: Volume mounts happen at container startup

### File Permissions
- **Issue**: Certbot creates root-owned files
- **Solution**: Use `sudo test` and Docker commands for access

### Nginx Configuration (v1.29-alpine)
- **Problems**: 
  - `listen 443 ssl http2;` (deprecated)
  - `ssl_prefer_server_ciphers off;` (invalid)
  - `limit_req off;` (invalid syntax)
- **Solutions**:
  - Use `listen 443 ssl;` + `http2 on;`
  - Remove invalid directives
  - Include `/etc/nginx/mime.types`

### Configuration Management
- **Issue**: Embedded configs in scripts
- **Solution**: Use dedicated config files
- **Benefits**: Version control, easier debugging

### Let's Encrypt Challenge Access
- **Issue**: 403 Forbidden on challenge files
- **Solutions**:
  - Use `alias` directive for challenge directory
  - Create directories before nginx startup
  - Use `^~` modifier for priority matching

### Certificate Verification
- **Issue**: Scripts reported failure incorrectly
- **Solution**: Add proper wait time and error detection

### Modern Security Practices
- TLS 1.2/1.3 only
- Modern cipher suites
- Security headers (HSTS, X-Frame-Options)
- Permissions-Policy for modern browsers

## Domain Configuration
- Primary: `zyh-home-internal-ip-address-4112.yehuizhang.com`
- Contact: `yehuizhang@outlook.com`
- Provider: Let's Encrypt (90-day validity)
- Auto-renewal: Every 12 hours

## Troubleshooting Commands
```bash
# Check SSL status
./build.sh ssl status

# Test nginx config
docker compose -f docker-compose.ssl.yml exec nginx nginx -t

# Check certificates
sudo ls -la certbot/conf/live/zyh-home-internal-ip-address-4112.yehuizhang.com/

# Test HTTPS
curl -I https://zyh-home-internal-ip-address-4112.yehuizhang.com/status

# Monitor services
docker compose -f docker-compose.ssl.yml logs -f
```
