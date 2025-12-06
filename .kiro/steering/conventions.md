# Development Conventions

This document outlines the coding and configuration conventions used in the Mojo project to ensure consistency across
all development work.

## Docker & Container Management

### Docker Compose Commands

- **Always use**: `docker compose` (Docker Compose V2 syntax)
- **Never use**: `docker-compose` (deprecated V1 syntax)

```bash
# ✅ Correct
docker compose -f docker-compose.ssl.yml up -d
docker compose -f docker-compose.app.yml logs -f

# ❌ Incorrect (deprecated)
docker-compose -f docker-compose.ssl.yml up -d
docker-compose -f docker-compose.app.yml logs -f
```

### Docker Image Versions

- Use specific version tags, not generic ones
- Keep images updated to latest stable versions
- Example: `nginx:1.29-alpine` instead of `nginx:latest`

## Build Script Commands

### Command Format

- **Use spaces** between command parts for readability
- **Never use hyphens** in multi-word commands

```bash
# ✅ Correct
./build.sh ssl setup
./build.sh ssl status
./build.sh ssl up
./build.sh infra up

# ❌ Incorrect
./build.sh ssl-setup
./build.sh ssl-status
./build.sh ssl-up
./build.sh infra-up
```

## Service Architecture

### Service Separation

The project uses a layered service architecture with clear separation across repositories:

**mojo-infra** (Infrastructure Layer):
1. **SSL Services** (`cd mojo-infra && ./build.sh ssl up`)
    - Nginx (reverse proxy)
    - Certbot (certificate management)

2. **Logging Services** (`cd mojo-infra && ./build.sh logging up`)
    - ELK Stack (Elasticsearch, Kibana, Filebeat)

3. **Database Services** (`cd mojo-infra && ./build.sh redis up`)
    - Redis (prod and dev instances)

**mojo-api** (Application Layer):
- **Application Services** (`cd mojo-api && ./build.sh up`)
    - FastAPI (main API service)
    - Chronos (Telegram bot)
    - Scheduler (background tasks)

### Service Independence

- SSL commands should only manage SSL services
- Each service layer can be started/stopped independently
- No cross-layer dependencies in build commands

## Domain & SSL Configuration

### Domain Information

- **Primary Domain**: `zyh-home-internal-ip-address-4112.yehuizhang.com`
- **Contact Email**: `yehuizhang@outlook.com`
- **SSL Provider**: Let's Encrypt with automatic renewal

### SSL Certificate Management

- Certificates stored in `/var/lib/mojo/certbot/conf/`
- Automatic renewal every 12 hours via Certbot
- Manual renewal available via `cd mojo-infra && ./build.sh ssl renew`
- SSL services managed from mojo-infra repository

## File Naming & Structure

### Configuration Files

- Use descriptive names: `docker-compose.ssl.yml`, `docker-compose.app.yml`
- Group related configurations in directories: `nginx/`, `scripts/`, `certbot/`
- Use `.yml` extension for Docker Compose files

### Script Files

**mojo-infra**:
- SSL scripts in `nginx/` directory: `setup-ssl.sh`, `ssl-status.sh`, `ssl-renew.sh`, `manage-allowlist.sh`
- Infrastructure scripts in `scripts/` directory: `setup-data-dirs.sh`

**mojo-api**:
- Application scripts in `scripts/` directory
- Make scripts executable: `chmod +x scripts/*.sh` or `chmod +x nginx/*.sh`

## Documentation Standards

### Command Examples

- Always show the correct modern syntax
- Include both individual commands and complete workflows
- Provide troubleshooting examples

### File References

- Use relative paths from project root
- Include file structure diagrams when helpful
- Keep documentation in sync with actual implementation

## Environment Configuration

### Environment Variables

- Store sensitive data in `.env` file
- Use descriptive variable names
- Document required variables in setup guides

### Stage Management

- `STAGE=DEV` for development
- `STAGE=PROD` for production
- Environment-specific Docker Compose overrides

## Error Handling & Troubleshooting

### Logging

- Use structured logging with consistent formats
- Include service identification in log entries
- Centralize logs via ELK stack in production

### Health Checks

- Implement health checks for all services
- Use appropriate timeouts and retry logic
- Monitor certificate expiry and renewal

## Code Quality

### Python Standards

- Use Black for code formatting (line length: 88)
- Use flake8 for linting
- Follow PEP 8 conventions
- Use type hints where appropriate

### Docker Standards

- Use multi-stage builds where beneficial
- Set resource limits in production
- Use health checks for service monitoring
- Keep images minimal and secure

These conventions ensure consistency, maintainability, and reliability across the entire Mojo platform.