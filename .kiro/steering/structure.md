# Project Structure

## Top-Level Organization

```
mojo/
├── mojo-api/              # Application services repository
│   ├── api/               # FastAPI web service
│   ├── chronos/           # Telegram bot service  
│   ├── scheduler/         # Background task scheduler
│   ├── shared/            # Common utilities and models
│   └── resources/         # Static resources and secrets
├── mojo-infra/            # Infrastructure services repository
│   ├── nginx/             # Nginx reverse proxy configs and SSL scripts
│   ├── config/            # Infrastructure configurations (filebeat, etc.)
│   └── scripts/           # Infrastructure management scripts
└── mojo-cdk/              # AWS CDK infrastructure as code
```

## Service Modules

### API Service (`api/`)

- `main.py`: FastAPI application entry point
- `routers/`: API route handlers organized by feature
- `scheduler/`: APScheduler integration
- `test/`: API-specific tests
- `Dockerfile_fastapi`: Container definition

### Chronos Bot (`chronos/`)

- `run.py`: Bot application entry point
- `commands/`: Telegram command handlers
- `model/`: Bot-specific data models
- `util/`: Bot utilities (translation, etc.)
- `test/`: Bot-specific tests
- `Dockerfile_chronos`: Container definition

### Shared Library (`shared/`)

- `auth/`: Authentication and security utilities
- `model/`: Common data models
- `persistence/`: Database and Redis clients
- `external/`: Third-party service integrations
- `util/`: Common utilities (time, text, network, etc.)
- `test/`: Shared library tests

## Configuration Files

### Build & Dependencies

- `pyproject.toml`: Python project configuration and dependencies
- `requirements.txt`: Compiled dependencies (auto-generated)
- `build.sh`: Main build script with all commands
- `setup.cfg`: Additional Python tooling configuration

### Docker & Deployment

**mojo-api** (Application Services):
- `docker-compose.app.yml`: Base application services
- `docker-compose.app.dev.yml`: Development overrides
- `docker-compose.app.prod.yml`: Production overrides
- `Dockerfile_*`: Service-specific container definitions
- `.env`: Environment variables

**mojo-infra** (Infrastructure Services):
- `docker-compose.ssl.yml`: SSL/nginx services
- `docker-compose.logging.yml`: ELK stack services
- `docker-compose.redis.yml`: Database services (Redis)
- `config/filebeat.yml`: Log shipping configuration
- `.env`: Infrastructure environment variables

### Development Tools

- `.pre-commit-config.yaml`: Git hooks configuration
- `pytest.ini`: Test runner configuration
- `.gitignore`: Version control exclusions
- `.dockerignore`: Docker build exclusions

## Naming Conventions

### Files & Directories

- Use snake_case for Python files and directories
- Use kebab-case for Docker Compose files
- Prefix test files with `test_` or suffix with `_test.py`
- Use descriptive names for router modules (e.g., `auth_router.py`)

### Code Structure

- Each service has its own `__init__.py` and test directory
- Models are grouped by domain (auth, app, weather, etc.)
- External integrations are organized by service provider
- Utilities are categorized by function (time, text, network, etc.)

## Data & Logs

### Persistent Data (`/var/lib/mojo/`)

- `certbot/`: SSL certificates and Let's Encrypt data
  - `certbot/conf/`: Certificate files
  - `certbot/www/`: ACME challenge files
- `elasticsearch/`: Search index data
- `kibana/`: Kibana data
- `redis/`: Redis persistence (prod and dev)
- `filebeat/`: Filebeat registry data

### Logs (`/var/log/mojo/`)

- Application log files organized by service and date
- `nginx/`: Nginx access and error logs
- `elasticsearch/`: Elasticsearch logs
- `kibana/`: Kibana logs
- `redis/`: Redis logs
- `filebeat/`: Filebeat logs

### Resource Management (mojo-api)

- `resources/secrets/`: API credentials and tokens
- `resources/supporting/`: Static files and configurations

## Testing Structure

- Tests mirror the source structure
- Integration tests in dedicated `integration/` directory
- Each service has its own test directory with `__init__.py`
- Use pytest fixtures in `conftest.py` files
- Test paths configured in `pyproject.toml`