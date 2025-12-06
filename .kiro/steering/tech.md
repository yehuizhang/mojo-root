# Technology Stack

## Core Technologies

- **Python 3.13+**: Primary language for all services
- **FastAPI**: Web framework for REST API service
- **SQLAlchemy**: Database ORM
- **Redis**: Caching and session management
- **Docker & Docker Compose**: Containerization and orchestration
- **AWS CDK**: Infrastructure as Code (TypeScript)

## Logging & Monitoring Stack

- **Elasticsearch 9.1.5**: Search and analytics engine for log storage
- **Kibana 9.1.5**: Data visualization and exploration for logs
- **Filebeat 9.1.5**: Log shipping agent for centralized logging
- **ELK Stack**: Complete logging pipeline (Elasticsearch + Kibana + Filebeat)

## Key Libraries

- **python-telegram-bot**: Telegram bot framework
- **APScheduler**: Task scheduling
- **boto3**: AWS SDK
- **google-api-python-client**: Google APIs integration
- **pydantic**: Data validation
- **bcrypt & PyJWT**: Authentication and security
- **httpx & aiohttp**: HTTP clients

## Development Tools

- **pytest**: Testing framework with asyncio support
- **black**: Code formatting (line length: 88)
- **flake8**: Linting with bugbear and comprehensions plugins
- **pre-commit**: Git hooks for code quality
- **pip-audit**: Security vulnerability scanning
- **coverage**: Test coverage reporting

## Common Commands

### Development

```bash
# Start all services in development mode
./build.sh dev

# Run FastAPI locally (without Docker)
./build.sh dev-local

# Install dependencies
./build.sh install

# Update requirements from pyproject.toml
./build.sh update
```

### Production

```bash
# Start infrastructure (Redis)
./build.sh infra up

# Start all application services
./build.sh up

# Check service status
./build.sh ps
```

### Testing & Quality

```bash
# Run all tests
./build.sh test

# Run tests with coverage
./build.sh test-coverage

# Format code
./build.sh format

# Lint code
./build.sh lint

# Security audit
pip-audit
```

### Docker Management

```bash
# Build images
./build.sh build

# Clean up Docker resources
./build.sh clean

# Stop all services
./build.sh down
```

## Environment Configuration

- Use `.env` files for environment variables
- `STAGE` variable controls DEV/PROD behavior
- Separate Docker Compose files for different environments:
    - `docker-compose.app.yml`: Base application services
    - `docker-compose.app.dev.yml`: Development overrides
    - `docker-compose.app.prod.yml`: Production overrides (includes Filebeat)
    - `docker-compose.infra.yml`: Infrastructure services (Redis, Elasticsearch, Kibana)

## Logging Configuration

### Production Logging Pipeline

```bash
FastAPI App → Log Files → Filebeat → Elasticsearch → Kibana
```

### Key Environment Variables

```bash
# ELK Stack
ELK_ES_PORT=9200
ELK_K_PORT=5601
ELK_PASSWORD=secure_password
ELK_IMAGE_VERSION=9.1.5

# Application
STAGE=PROD  # Required for file logging
APP_NAME=api  # Must match valid AppName enum
```

### Log File Locations

- **Development**: `./_local/logs/` (local bind mount)
- **Production**: `/var/log/mojo/` (absolute path)
- **Format**: `{app_name}_{YYYY_MM_DD}.log`