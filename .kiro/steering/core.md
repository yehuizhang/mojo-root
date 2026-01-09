# Core Architecture & Conventions

## Service Architecture
- **mojo-api**: Application services (FastAPI, Chronos bot, Scheduler)
- **mojo-infra**: Infrastructure services (nginx, SSL, ELK, Redis)
- **mojo-shared**: Common utilities and models

## Service Communication
- nginx (mojo-infra) → FastAPI (mojo-api) via `mojo_app` Docker network
- nginx upstream: `fastapi-app:8000` and `nextjs-app:3000`
- Redis: Central caching and session management
- Services communicate over shared Docker networks

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

## Configuration Management
- Environment Variables: Runtime configuration
- AppContext: Shared configuration object  
- Stage-based: DEV/PROD separation
- Docker Compose overrides for environments

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

## Critical Conventions

### Docker Commands
- Use `docker compose` (V2), never `docker-compose`
- Build script commands use spaces: `ssl setup`, not `ssl-setup`

### Service Independence
- SSL commands only manage SSL services
- Infrastructure services start independently
- Application services depend on infrastructure being ready

### Common Issue: 502 Bad Gateway
- Problem: nginx keeps stale connections after container restart
- Solution: Configure upstream retry: `max_fails=3 fail_timeout=30s`

### File Structure
- Use snake_case for Python files
- Use kebab-case for Docker Compose files
- Prefix test files with `test_`

### bb Command Alias
- `bb` = `./build.sh` (defined in ~/.zshrc)
- `bb up` = production mode with rebuild
- `bb dev` = development mode with logs
