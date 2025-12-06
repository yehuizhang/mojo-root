# SSL/HTTPS Setup Lessons Learned

This document captures critical lessons learned during the SSL/HTTPS setup process for the Mojo project.

## Key Challenges and Solutions

### 1. Docker Compose Command Syntax

**Issue**: Used deprecated `docker-compose` command
**Solution**: Always use `docker compose` (V2 syntax) for modern Docker installations
**Impact**: Prevents compatibility issues and follows current best practices

### 2. Build Script Command Format

**Issue**: Used hyphens in multi-word commands (`ssl-setup`, `ssl-status`)
**Solution**: Use spaces for better readability (`ssl setup`, `ssl status`)
**Impact**: More intuitive CLI interface consistent with modern tools

### 3. Service Architecture Separation

**Issue**: SSL scripts tried to manage application services
**Solution**: SSL commands should only manage SSL services, assume app services are running
**Architecture**:

- Infrastructure: `./build.sh infra up` (Redis, ELK)
- Application: `./build.sh up` (FastAPI, Chronos, scheduler)
- SSL: `./build.sh ssl *` (nginx, certbot only)

### 4. Docker Volume Mount Timing Issues

**Issue**: Created `.well-known/acme-challenge/` directory after nginx container started
**Solution**: Create directory structure BEFORE starting containers
**Root Cause**: Docker volume mounts happen at container startup, not runtime
**Fix**: Ensure all required directories exist before `docker compose up`

### 5. File Permissions with Let's Encrypt

**Issue**: Certificates created by certbot are owned by root with restrictive permissions
**Solution**: Use `sudo test` and Docker commands to check/access root-owned files
**Impact**: Scripts must handle root-owned certificate files gracefully

### 6. Nginx Configuration Compatibility

**Issue**: Several nginx directives incompatible with nginx 1.29-alpine
**Problems Found**:

- `listen 443 ssl http2;` (deprecated)
- `ssl_prefer_server_ciphers off;` (invalid parameter)
- `limit_req off;` (invalid syntax)
- Missing MIME types and basic HTTP configuration

**Solutions Applied**:

- Use `listen 443 ssl;` + `http2 on;` for HTTP/2
- Use `ssl_prefer_server_ciphers off;` (correct for TLS 1.3)
- Remove `limit_req off;` or use proper rate limiting zones
- Include `/etc/nginx/mime.types` and basic HTTP settings
- Add performance optimizations (gzip, keepalive, etc.)

### 7. Configuration Management Strategy

**Issue**: Embedded nginx configuration in setup script caused maintenance issues
**Solution**: Use dedicated configuration files instead of generating configs in scripts
**Benefits**:

- Single source of truth
- Version control friendly
- Easier debugging and modification
- Standard nginx file locations

### 8. Let's Encrypt Challenge Directory Access

**Issue**: 403 Forbidden errors when Let's Encrypt tried to access challenge files
**Root Causes**:

- Nginx couldn't access challenge directory due to volume mount timing
- Incorrect nginx location configuration (`root` vs `alias`)
  **Solutions**:
- Use `alias` directive for challenge directory
- Create directory structure before starting nginx
- Use `^~` modifier for priority matching
- Add proper `try_files` and content-type headers

### 9. Certificate Verification Logic

**Issue**: Setup script incorrectly reported failure even when certificates were obtained
**Solution**: Add proper wait time and better error detection
**Improvements**:

- Wait for certificate files to appear on filesystem
- Check container exit codes properly
- Provide detailed debugging information on failures

### 10. Modern Security Best Practices

**Implemented**:

- TLS 1.2/1.3 only
- Modern cipher suites optimized for performance
- Security headers (HSTS, X-Frame-Options, etc.)
- Removed deprecated headers (X-XSS-Protection)
- Added Permissions-Policy for modern browsers
- Disabled OCSP stapling for Let's Encrypt (not needed)

## Technical Architecture Decisions

### SSL Service Independence

- SSL services run independently of application services
- Nginx depends on FastAPI being available but doesn't manage it
- Clear separation of concerns between service layers

### Certificate Management

- Certificates stored in `./certbot/conf/` (host filesystem)
- Automatic renewal every 12 hours via certbot container
- Manual renewal available via `./build.sh ssl renew`
- Status checking handles root-owned files gracefully

### Network Architecture

```
Internet (Port 80/443) → Nginx → FastAPI (Port 8000)
                           ↓
                      Certbot (Certificate Management)
```

### Configuration Files Structure

```
nginx/
├── nginx-init.conf     # HTTP-only for initial certificate generation
└── nginx.conf          # Full HTTPS configuration

scripts/
├── setup-ssl.sh        # Complete SSL setup automation
├── ssl-status.sh       # Certificate status and monitoring
└── ssl-renew.sh        # Manual certificate renewal

docker-compose.ssl.yml  # SSL services (nginx + certbot)
```

## Best Practices Established

### 1. Pre-flight Checks

- Always verify application services are running before SSL setup
- Test challenge directory access before certificate generation
- Validate nginx configuration before applying changes

### 2. Error Handling

- Provide detailed debugging information on failures
- Use multiple fallback methods for checking certificate status
- Stop setup immediately if prerequisites aren't met

### 3. Security Configuration

- Use modern TLS settings appropriate for nginx version
- Implement proper rate limiting for different endpoint types
- Add comprehensive security headers
- Follow principle of least privilege for file permissions

### 4. Monitoring and Maintenance

- Automated certificate renewal with logging
- Health checks for all SSL services
- Easy status checking and manual intervention capabilities
- Clear documentation for troubleshooting

## Domain-Specific Considerations

### Domain Configuration

- Primary domain: `zyh-home-internal-ip-address-4112.yehuizhang.com`
- Contact email: `yehuizhang@outlook.com`
- Certificate provider: Let's Encrypt with 90-day validity
- Auto-renewal: Every 12 hours starting 30 days before expiry

### Port Requirements

- Port 80: Required for Let's Encrypt challenges and HTTP redirects
- Port 443: HTTPS traffic
- Both ports must remain open permanently for proper operation

## Troubleshooting Playbook

### Common Issues and Solutions

1. **403 on challenge directory**: Check volume mounts and directory permissions
2. **Nginx won't start**: Validate configuration syntax with `nginx -t`
3. **Certificate not found**: Check file permissions and use sudo/Docker for access
4. **HTTPS not working**: Verify nginx is listening on 443 and certificates are loaded
5. **Auto-renewal failing**: Check certbot logs and challenge directory access

### Debugging Commands

```bash
# Check SSL service status
./build.sh ssl status

# Test nginx configuration
docker compose -f docker-compose.ssl.yml exec nginx nginx -t

# Check certificate files
sudo ls -la certbot/conf/live/zyh-home-internal-ip-address-4112.yehuizhang.com/

# Test HTTPS connectivity
curl -I https://zyh-home-internal-ip-address-4112.yehuizhang.com/status

# Monitor SSL services
docker compose -f docker-compose.ssl.yml logs -f
```

### 11. Access Control Implementation

**Challenge**: Implementing HTTPS endpoint allowlist without breaking existing functionality
**Solution**: Gradual security approach with optional strict mode
**Key Decisions**:

- Keep all configuration in single nginx.conf file (avoid complexity)
- Default to permissive mode, allow enabling strict mode later
- Provide testing tools before enforcing restrictions
- Block HTTP traffic completely except Let's Encrypt challenges
  **Lesson**: Security changes should be gradual and well-tested, not immediately restrictive

## Future Improvements

### Potential Enhancements

1. **Certificate backup automation**: Regular backups of certificate files
2. **Monitoring integration**: Alerts for certificate expiry and renewal failures
3. **Multi-domain support**: Extend setup to handle multiple domains
4. **CDN integration**: Add CloudFlare or similar CDN configuration
5. **Advanced security**: Implement certificate pinning and additional security headers

### Maintenance Schedule

- **Daily**: Automated certificate renewal checks
- **Weekly**: SSL service health verification
- **Monthly**: Security configuration review
- **Quarterly**: Update nginx and certbot versions

This comprehensive setup provides a robust, secure, and maintainable HTTPS infrastructure for the Mojo platform.