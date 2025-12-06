# Architecture Guide

## System Overview

### Microservices Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ API Service │    │   Chronos   │    │  Scheduler  │
│  (FastAPI)  │    │ (Telegram)  │    │ (Background)│
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                   ┌──────▼──────┐
                   │    Redis    │
                   │  (Caching)  │
                   └─────────────┘
```

### Service Communication

- **Redis**: Central caching and session management
- **Docker Network**: Inter-service communication via `mojo_net` bridge
- **Shared Library**: Common utilities, models, and integrations
- **Environment Variables**: Configuration management across services

## Core Design Patterns

### Shared Library Pattern

```
shared/
├── auth/          # Authentication utilities
├── model/         # Common data structures
├── persistence/   # Database abstractions
├── external/      # Third-party integrations
└── util/          # Reusable utilities
```

**Benefits**:

- Code reuse across services
- Consistent data models
- Centralized business logic
- Unified external service integrations

### Factory Pattern

#### AppContext Factory

```python
@lru_cache(maxsize=5)
def build_context():
    app_name = os.getenv("APP_NAME", AppName.TEST)
    stage = os.getenv("STAGE", "DEV").upper()
    logger = _create_logger(app_name, stage)
    return AppContext(stage, logger)
```

#### Service Factories

- **Redis Client**: Environment-based connection factory
- **External Services**: AWS, Google APIs, weather service factories
- **Bot Components**: Command handlers and middleware factories

### Repository Pattern

#### Data Access Abstraction

```python
class RedisClient:
    def __init__(self):
        ctx = build_context()
        # Connection logic abstracted
    
    def get_user(self, user_id: str) -> Optional[User]:
        # Data access abstracted
```

#### External Service Abstraction

```python
class WeatherService:
    def get_current_weather(self, location: str) -> WeatherData:
        # External API abstracted
```

## Service Architecture

### API Service (FastAPI)

#### Middleware Stack

```python
# Request flow through middleware
Request → CORS → Process Time → Auth → Route Handler → Response
```

#### Key Components

- **Routers**: Feature-based route organization
- **Dependencies**: Dependency injection for auth and context
- **Middleware**: Cross-cutting concerns (CORS, timing, auth)
- **Exception Handlers**: Centralized error handling

#### Authentication Flow

```
Client Request → Bearer Token → JWT Validation → User Context → Protected Route
```

### Chronos Service (Telegram Bot)

#### Bot Architecture

```python
# Bot component structure
Application → Handlers → Commands → Shared Logic → External APIs
```

#### Key Features

- **Multi-language Support**: Translation files and language detection
- **User Management**: Invitation codes and permission scopes
- **Command Processing**: Structured command handling with help system
- **Session Management**: Redis-backed user sessions

### Scheduler Service

#### Task Management

```python
# APScheduler integration
Scheduler → Job Queue → Background Tasks → External APIs → Logging
```

#### Capabilities

- **Periodic Jobs**: Cron-like scheduling
- **Gmail Integration**: Email processing automation
- **DNS Updates**: Dynamic DNS management
- **Health Monitoring**: Service status checks

## Data Flow Patterns

### Request Processing

```
1. Client Request → Service Endpoint
2. Authentication/Validation → Shared Auth Module
3. Business Logic → Shared Library
4. Data Access → Redis/External APIs
5. Response → Client
```

### Event Processing

```
1. External Event → Service Handler
2. Event Processing → Shared Logic
3. State Updates → Redis
4. Notifications → Telegram/Logging
```

### Background Processing

```
1. Scheduled Trigger → Scheduler Service
2. Task Execution → Shared Library
3. External API Calls → Service Integrations
4. Result Logging → ELK Stack
```

## Configuration Management

### Environment-Based Configuration

```python
class Stage(Enum):
    DEV = "DEV"
    PROD = "PROD"

class AppName(Enum):
    API = "api"
    CHRONOS = "chronos"
    SCHEDULER = "scheduler"
```

### Configuration Hierarchy

1. **Environment Variables**: Runtime configuration
2. **AppContext**: Shared configuration object
3. **Service-Specific**: Individual service settings
4. **External Configs**: API keys and credentials

## Security Architecture

### Authentication Strategy

- **API Service**: Bearer token authentication
- **Telegram Bot**: Invitation code verification
- **Internal Services**: Shared context authentication

### Security Layers

```
1. Network Isolation (Docker networks)
2. Authentication (Tokens/Invitation codes)
3. Authorization (User scopes/permissions)
4. Input Validation (Pydantic models)
5. Secure Storage (Environment variables)
```

### Data Protection

- **Credentials**: Environment variables only
- **Sessions**: Redis with expiration
- **Logs**: Structured logging without sensitive data
- **Network**: Internal Docker network communication

## Logging Architecture

### ELK Stack Integration

```
Application Logs → File System → Filebeat → Elasticsearch → Kibana
```

### Logging Strategy

- **Structured Logging**: JSON format with consistent fields
- **Service Identification**: App name and environment tagging
- **Log Levels**: Environment-appropriate verbosity
- **Centralized Collection**: ELK stack for aggregation and analysis

### Log Flow

```python
# Application logging
ctx = build_context()
ctx.logger.info("Request processed", extra={
    "user_id": user.id,
    "endpoint": "/api/status",
    "duration_ms": 150
})
```

## Deployment Architecture

### Container Strategy

```
docker-compose.app.yml      # Base services
docker-compose.app.prod.yml # Production overrides
docker-compose.infra.yml    # Infrastructure services
```

### Environment Separation

- **Development**: Local volumes, debug logging, hot reload
- **Production**: Persistent volumes, structured logging, health checks

### Service Dependencies

```yaml
# Dependency chain
Infrastructure (Redis, ELK) → Application Services → Health Checks
```

## Scalability Considerations

### Horizontal Scaling

- **Stateless Services**: API and Scheduler can be replicated
- **Shared State**: Redis for session and cache management
- **Load Balancing**: Docker Compose service scaling

### Performance Optimization

- **Redis Caching**: Fast data access and session management
- **Async Operations**: Non-blocking I/O with FastAPI and aiohttp
- **Connection Pooling**: Efficient database and external API connections

### Resource Management

```yaml
# Production resource limits
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## Error Handling Strategy

### Exception Hierarchy

```python
# Custom exception types in shared module
class MojoException(Exception): pass
class AuthenticationError(MojoException): pass
class ExternalServiceError(MojoException): pass
```

### Error Recovery

- **Graceful Degradation**: Fallback behaviors for external service failures
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breaker**: Prevent cascade failures
- **Health Checks**: Proactive service monitoring

## Monitoring and Observability

### Health Check Strategy

```python
# Service health endpoints
@app.get("/status")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": get_version()
    }
```

### Metrics Collection

- **Application Metrics**: Request counts, response times, error rates
- **Infrastructure Metrics**: Container resource usage, network traffic
- **Business Metrics**: User activity, feature usage, external API calls

### Alerting Strategy

- **Service Health**: Container and application status monitoring
- **Error Rates**: Threshold-based alerting for error spikes
- **Resource Usage**: Memory and CPU utilization alerts
- **External Dependencies**: Third-party service availability monitoring

This architecture provides a robust foundation for building scalable, maintainable, and observable microservices with
comprehensive logging and monitoring capabilities.