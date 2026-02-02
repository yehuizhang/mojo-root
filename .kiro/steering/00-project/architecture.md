---
inclusion: always
---
# Project Architecture & Technology Stack

## Service Architecture

### Services
- **mojo-api**: Application services (FastAPI, Chronos bot, Scheduler)
- **mojo-infra**: Infrastructure services (nginx, SSL, ELK, Redis)
- **mojo-next**: Next.js frontend application
- **mojo-cdk**: AWS CDK infrastructure as code

### Service Communication
- nginx (mojo-infra) → FastAPI (mojo-api) via `mojo_app` Docker network
- nginx upstream: `fastapi-app:8000` and `nextjs-app:3000`
- Redis: Central caching and session management
- Services communicate over shared Docker networks

## Core Technologies

### Backend
- **Python 3.13+**: Primary language
- **FastAPI**: Web framework
- **Redis**: Caching and sessions
- **Docker Compose**: Orchestration
- **AWS CDK**: Infrastructure as Code

### Frontend
- **Next.js**: React framework
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Styling

### Infrastructure
- **ELK Stack (v9.1.5)**: Elasticsearch, Kibana, Filebeat
- **nginx**: Reverse proxy and SSL termination
- **Let's Encrypt**: SSL certificates with auto-renewal

### Key Libraries
- **python-telegram-bot**: Bot framework
- **APScheduler**: Task scheduling
- **boto3**: AWS SDK
- **google-api-python-client**: Google APIs
- **pydantic**: Data validation
- **bcrypt & PyJWT**: Authentication
- **httpx & aiohttp**: HTTP clients

### Development Tools
- **pytest**: Testing framework with asyncio support
- **black**: Code formatting (line length: 88)
- **flake8**: Linting with bugbear and comprehensions plugins
- **pre-commit**: Git hooks for code quality
- **pip-audit**: Security vulnerability scanning
- **coverage**: Test coverage reporting

## Key Design Patterns

### Shared Library Pattern
```
shared/
├── auth/          # Authentication utilities
├── model/         # Common data structures  
├── persistence/   # Database abstractions
├── external/      # Third-party integrations
└── util/          # Reusable utilities
```

### Factory Pattern
- AppContext Factory: `build_context()` with environment-based configuration
- Service Factories: Redis, AWS, Google APIs, weather services
- Bot Components: Command handlers and middleware

### Repository Pattern
- Data access abstraction via RedisClient
- External service abstraction (WeatherService, etc.)

### Handler + DAO Pattern (mojo-api)
- **Handlers** (`/api/handlers/`) - Business logic orchestration
- **DAOs** (`/api/dao/`) - Data access logic
- **Routers** (`/api/routers/`) - Thin HTTP layer
- **Factories** - Dependency injection wiring

## Configuration Management

### Environment Variables
- Runtime configuration via `.env` files
- `STAGE` variable controls DEV/PROD behavior
- Separate Docker Compose files for different environments:
  - `docker-compose.app.yml`: Base application services
  - `docker-compose.app.dev.yml`: Development overrides
  - `docker-compose.app.prod.yml`: Production overrides (includes Filebeat)
  - `docker-compose.infra.yml`: Infrastructure services (Redis, Elasticsearch, Kibana)

### AppContext
- Shared configuration object
- Stage-based: DEV/PROD separation
- Provides logger and environment info

### Logging Configuration

**Production Logging Pipeline:**
```
FastAPI App → Log Files → Filebeat → Elasticsearch → Kibana
```

**Key Environment Variables:**
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

**Log File Locations:**
- **Development**: `./_local/logs/` (local bind mount)
- **Production**: `/var/log/mojo/` (absolute path)
- **Format**: `{app_name}_{YYYY_MM_DD}.log`

## Security Architecture
- API Service: Bearer token authentication
- Telegram Bot: Invitation code verification
- Network isolation via Docker networks
- Credentials in environment variables only

## Domain Configuration
- Primary: `zyh-home-internal-ip-address-4112.yehuizhang.com`
- API: `api.yehuizhang.com`
- Website: `yehuizhang.com`
- SSL: Let's Encrypt with auto-renewal
- CloudFront Distribution: E27QEWNM1GENUR

## Critical Conventions

### Docker Commands
- Use `docker compose` (V2), never `docker-compose`
- Build script commands use spaces: `ssl setup`, not `ssl-setup`

### Service Independence
- SSL commands only manage SSL services
- Infrastructure services start independently
- Application services depend on infrastructure being ready

### File Structure
- Use snake_case for Python files
- Use kebab-case for Docker Compose files
- Prefix test files with `test_`

### bb Command Alias
- `bb` = `./build.sh` (defined in ~/.zshrc)
- `bb up` = production mode with rebuild
- `bb dev` = development mode with logs
