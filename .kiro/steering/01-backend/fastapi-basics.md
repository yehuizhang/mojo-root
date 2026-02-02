---
inclusion: fileMatch
fileMatchPattern: '**/*.py'
---
# FastAPI Basics: DI, Error Handling, Context & Patterns

## Handler + DAO Architecture Pattern

### Overview

The mojo-api uses FastAPI's dependency injection system with factory functions to wire together:
- **DAOs** (Data Access Objects) - Redis operations
- **Services** - Business logic and external API calls
- **Handlers** - Orchestration and HTTP response handling
- **Routers** - HTTP endpoint definitions

### Architecture Layers

```
Router (HTTP) → Handler (Business Logic) → DAO (Data Access)
                     ↓
                 Services (External APIs, Calculations)
```

### File Organization

1. **Handlers** live in `/api/handlers/` - contain business logic
2. **DAOs** live in `/api/dao/` - contain data access logic
3. **Routers** live in `/api/routers/` - thin layer, delegate to handlers
4. **Factories** wire dependencies:
   - `dao_factory.py` - creates DAO instances
   - `handler_factory.py` - creates handlers with injected DAOs via `Depends()`

## Dependency Injection Pattern

### DAO Factories

Located in `api/dao/dao_factory.py`:

```python
def get_user_dao() -> UserDAO:
    """Factory function for UserDAO dependency injection."""
    return UserDAO()

def get_finance_dao() -> FinanceDAO:
    """Factory function for FinanceDAO dependency injection."""
    return FinanceDAO()
```

**Rules:**
- One factory function per DAO
- Returns new instance (DAOs are lightweight)
- No parameters needed (DAOs create their own Redis client)

### Service Factories

Located in `api/handlers/handler_factory.py`:

```python
def get_market_data_service(
    finance_dao=Depends(get_finance_dao)
) -> MarketDataService:
    """Factory function for MarketDataService dependency injection."""
    return MarketDataService(finance_dao=finance_dao)

def get_signal_generator_service() -> SignalGeneratorService:
    """Factory function for SignalGeneratorService dependency injection."""
    return SignalGeneratorService()
```

**Rules:**
- Inject dependencies using `Depends()`
- Services that need DAOs receive them via injection
- Services without dependencies can be created directly

### Handler Factories

Located in `api/handlers/handler_factory.py`:

```python
def get_finance_handler(
    finance_dao=Depends(get_finance_dao),
    market_data_service=Depends(get_market_data_service),
    signal_generator_service=Depends(get_signal_generator_service),
) -> FinanceHandler:
    """Factory function for FinanceHandler with dependencies."""
    return FinanceHandler(
        finance_dao=finance_dao,
        market_data_service=market_data_service,
        signal_generator_service=signal_generator_service,
    )
```

**Rules:**
- Inject all dependencies using `Depends()`
- Pass dependencies to handler constructor
- Use explicit parameter names for clarity

### Handler Pattern

Handlers receive dependencies via constructor injection:

```python
class FinanceHandler:
    def __init__(
        self,
        finance_dao: Optional[FinanceDAO] = None,
        market_data_service: Optional[MarketDataService] = None,
    ):
        """Initialize handler with injected dependencies."""
        self.ctx = build_context()  # Initialize once
        self.finance_dao = finance_dao
        self.market_data_service = market_data_service
```

**Rules:**
- Store dependencies as instance variables
- Use `Optional` type hints for flexibility
- Initialize context in constructor
- Don't create dependencies directly (except context)

### Router Pattern

Routers inject handlers using `Depends()`:

```python
@router.get("/dashboard")
async def get_dashboard(
    force_refresh: bool = Query(False),
    handler: FinanceHandler = Depends(get_finance_handler),
) -> DashboardResponse:
    """Get complete dashboard data."""
    return await handler.get_dashboard(force_refresh=force_refresh)
```

**Rules:**
- Keep routers thin - delegate to handlers
- Inject handler using `Depends(get_handler_factory)`
- Extract request parameters (query, path, body)
- Pass parameters to handler methods
- Return handler response directly

## Context Management

### AppContext Pattern

The `build_context()` function creates a singleton application context that provides:
- Logger instance
- Stage information (DEV/PROD)
- Environment-specific configuration

### When to Use build_context()

**✅ Use in class constructors (once per instance):**

```python
class SomeHandler:
    def __init__(self, dao: SomeDAO):
        self.ctx = build_context()  # Store as instance variable
        self.dao = dao
    
    def some_method(self):
        self.ctx.logger.info("Using stored context")
```

**❌ Don't call repeatedly in methods:**

```python
# BAD - creates context on every call
def some_method(self):
    ctx = build_context()  # Wasteful
    ctx.logger.info("Message")

# GOOD - use stored context
def some_method(self):
    self.ctx.logger.info("Message")
```

### Logger Usage

```python
# INFO - Normal operations
self.ctx.logger.info("User logged in successfully")
self.ctx.logger.info(f"Cached data for {ticker}")

# WARNING - Unexpected but handled
self.ctx.logger.warning(f"User {username} not found, using default")

# ERROR - Operation failures
self.ctx.logger.error(f"Failed to save position: {error}")
```

### Stage-Based Behavior

```python
# Check if production
if self.ctx.is_prod():
    use_production_api()
else:
    use_mock_data()
```

## Error Handling

### Standard HTTP Status Codes

- **400 Bad Request**: Invalid input, validation failures
- **401 Unauthorized**: Authentication failures
- **403 Forbidden**: Authorization failures
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Resource already exists or state conflict
- **500 Internal Server Error**: Unexpected server errors

### Error Handling Template

```python
from fastapi import HTTPException, status

# Validation Error
if not valid_input:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Specific validation error message"
    )

# Not Found Error
if not resource:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Resource {resource_id} not found"
    )

# Conflict Error
if resource_exists:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Resource {resource_id} already exists"
    )

# Internal Server Error
try:
    # operation
except Exception as e:
    self.ctx.logger.error(f"Operation failed: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to perform operation: {str(e)}"
    )
```

### DAO Error Handling

DAOs should:
1. Log errors using `self._log_error(operation, error)`
2. Return `None`, `False`, or empty collections on failure
3. Let handlers decide how to respond to failures

```python
# In DAO
def get_resource(self, resource_id: str) -> Optional[Resource]:
    try:
        data = self.redis.client.get(f"resource:{resource_id}")
        return Resource.from_json(data) if data else None
    except Exception as e:
        self._log_error(f"get_resource {resource_id}", e)
        return None

# In Handler
resource = self.dao.get_resource(resource_id)
if not resource:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Resource {resource_id} not found"
    )
```

### Graceful Degradation

```python
# Try primary source, fall back to secondary
try:
    data = await self.primary_service.get_data(key)
except Exception as e:
    self.ctx.logger.warning(f"Primary service failed: {e}, using fallback")
    data = await self.fallback_service.get_data(key)
```

## Common Patterns & Conventions

### Model Change Checklist

When modifying a model (e.g., `UserModel`), check ALL related models:
- **Response models** (e.g., `UserResponse`) - often mirror the main model
- **Request models** - may reference the changed type
- **Related handlers** - may need import updates
- **DAOs** - if field affects storage/retrieval

### Position Quantity Convention

For stock/option positions, use **signed quantities** to indicate long/short:
- **Positive quantity** = Long position (bought)
- **Negative quantity** = Short position (sold)

This simplifies P&L calculations:
```python
# Works for both long and short positions
current_value = current_price * quantity * multiplier
cost = entry_price * quantity * multiplier
unrealized_pnl = current_value - cost
```

## Common Mistakes to Avoid

### ❌ Creating Dependencies Directly

```python
# BAD - creates tight coupling
class Handler:
    def __init__(self):
        self.dao = UserDAO()  # Hard to test

# GOOD - inject dependency
class Handler:
    def __init__(self, user_dao: UserDAO):
        self.dao = user_dao  # Easy to test
```

### ❌ Business Logic in Routers

```python
# BAD - router has business logic
@router.get("/users/{user_id}")
async def get_user(user_id: str, dao=Depends(get_user_dao)):
    user = dao.get_user(user_id)  # Business logic in router
    if not user:
        raise HTTPException(404)
    return user

# GOOD - delegate to handler
@router.get("/users/{user_id}")
async def get_user(user_id: str, handler=Depends(get_user_handler)):
    return handler.get_user(user_id)  # Handler has business logic
```

### ❌ Creating Context in Every Method

```python
# BAD
class Handler:
    def method1(self):
        ctx = build_context()  # Wasteful
        ctx.logger.info("Method 1")

# GOOD
class Handler:
    def __init__(self):
        self.ctx = build_context()  # Once
    
    def method1(self):
        self.ctx.logger.info("Method 1")
```

### ❌ Generic Error Messages

```python
# BAD
raise HTTPException(status_code=400, detail="Invalid input")

# GOOD
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail=f"Ticker {ticker} not found or invalid format"
)
```

## Feature Development Checklist

When adding new features:

- [ ] Create DAO in `api/dao/`
- [ ] Add DAO factory in `api/dao/dao_factory.py`
- [ ] Create handler in `api/handlers/`
- [ ] Add handler factory in `api/handlers/handler_factory.py`
- [ ] Inject dependencies using `Depends()`
- [ ] Create router in `api/routers/`
- [ ] Use handler factory in router
- [ ] Register router in `api/main.py`
- [ ] Write tests with mock dependencies
