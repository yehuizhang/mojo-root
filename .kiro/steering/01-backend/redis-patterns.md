---
inclusion: fileMatch
fileMatchPattern: '**/*.py'
---
# Redis Patterns and Best Practices

## Redis Key Naming Conventions

Use hierarchical key naming with colons as separators:

```
{domain}:{entity}:{identifier}
{domain}:{entity}:{sub-entity}:{identifier}
```

### Examples

```python
# User data
auth:username:john_doe          # User object by username
auth:user:uuid-123              # User object by ID (if needed)

# Group data
auth:group:admins               # Group object
auth:groups                     # Set of all group names

# Invitations
auth:invitation:ABC123          # Invitation object
auth:inviter:user123            # Set of invitation codes by inviter

# Finance data
finance:watchlist               # Set of ticker symbols
finance:position:uuid-456       # Position object
finance:positions:index         # Set of all position IDs
finance:cache:stock:AAPL        # Cached stock data
finance:cache:options:AAPL      # Cached options data
```

## Key Patterns

### Pattern 1: Simple Key-Value

Store single object by unique identifier:

```python
# Store
key = f"auth:username:{username}"
self.redis.client.set(key, user.to_json())

# Retrieve
user_json = self.redis.client.get(key)
user = UserModel.from_json(user_json) if user_json else None
```

**Use when:**
- Single object lookup by unique key
- No need for secondary indexes

### Pattern 2: Set for Index

Use Redis sets to maintain indexes:

```python
# Add to index
self.redis.client.sadd("finance:watchlist", ticker)

# Get all items
tickers = self.redis.client.smembers("finance:watchlist")

# Check membership
exists = self.redis.client.sismember("finance:watchlist", ticker)

# Remove from index
self.redis.client.srem("finance:watchlist", ticker)
```

**Use when:**
- Need to list all items
- Need to check membership quickly
- Order doesn't matter

### Pattern 3: Object + Index

Store objects individually and maintain an index:

```python
# Create
position_id = str(uuid.uuid4())
position_key = f"finance:position:{position_id}"

# Store object
self.redis.client.set(position_key, json.dumps(position_data))

# Add to index
self.redis.client.sadd("finance:positions:index", position_id)

# Retrieve all
position_ids = self.redis.client.smembers("finance:positions:index")
positions = []
for pos_id in position_ids:
    data = self.redis.client.get(f"finance:position:{pos_id}")
    if data:
        positions.append(json.loads(data))
```

**Use when:**
- Need to store multiple objects
- Need to list all objects
- Objects are too large for a single key

### Pattern 4: Secondary Index

Maintain multiple indexes for different lookup patterns:

```python
# Store invitation
invitation_key = f"auth:invitation:{code}"
inviter_key = f"auth:inviter:{inviter_id}"

self.redis.client.set(invitation_key, invitation.to_json())
self.redis.client.sadd(inviter_key, code)  # Secondary index

# Lookup by code
invitation = self.redis.client.get(f"auth:invitation:{code}")

# Lookup by inviter
codes = self.redis.client.smembers(f"auth:inviter:{inviter_id}")
```

**Use when:**
- Need multiple ways to query data
- Different access patterns

### Pattern 5: Cache with TTL

Store temporary data with expiration:

```python
# Cache with TTL
ttl_seconds = 300  # 5 minutes
self.redis.client.setex(
    f"finance:cache:stock:{ticker}",
    ttl_seconds,
    json.dumps(stock_data)
)

# Retrieve cached data
cached = self.redis.client.get(f"finance:cache:stock:{ticker}")
if cached:
    return json.loads(cached)
```

**Use when:**
- Data is expensive to fetch
- Data changes infrequently
- Stale data is acceptable

## TTL Strategies

### Fixed TTL

```python
# Short-lived cache (5 minutes)
self.redis.client.setex(key, 300, data)

# Medium-lived cache (1 hour)
self.redis.client.setex(key, 3600, data)

# Long-lived cache (24 hours)
self.redis.client.setex(key, 86400, data)
```

### Dynamic TTL

```python
from api.lib.util.market_hours import get_cache_ttl

# TTL based on market hours
ttl = get_cache_ttl()  # 10 min during market, 1 hour after
self.redis.client.setex(key, ttl, data)
```

### Smart TTL Based on Data

```python
# Cache until event date
if earnings_date:
    days_until = (earnings_date - date.today()).days
    ttl = min(days_until, 60) * 86400  # Max 60 days
    ttl = max(ttl, 3600)  # Min 1 hour
    self.redis.client.setex(key, ttl, data)
```

### No Expiration

```python
# Persistent data (user positions, watchlist)
self.redis.client.set(key, data)  # No TTL
```

**Use when:**
- User-created data
- Data should persist until explicitly deleted

## Atomic Operations

### Pipeline for Multiple Operations

```python
# Use pipeline for atomicity
pipe = self.redis.client.pipeline()
pipe.set(group_key, group.to_json())
pipe.sadd(group_list_key, group.name)
results = pipe.execute()
```

**Use when:**
- Multiple related operations
- Need atomicity (all or nothing)
- Reduce network round trips

### Transaction Example

```python
# Delete with cleanup
pipe = self.redis.client.pipeline()
pipe.delete(f"auth:group:{name}")
pipe.srem("auth:groups", name)
results = pipe.execute()

return results[0] > 0  # Check if delete succeeded
```

## Data Serialization

### JSON Serialization

```python
import json
from datetime import date, datetime

# Serialize with date handling
def serialize_position(position: dict) -> str:
    # Convert dates to ISO strings
    if "transaction_date" in position and position["transaction_date"]:
        position["transaction_date"] = position["transaction_date"].isoformat()
    if "expiration" in position and position["expiration"]:
        position["expiration"] = position["expiration"].isoformat()
    
    return json.dumps(position)

# Deserialize with date handling
def deserialize_position(data: str) -> dict:
    position = json.loads(data)
    
    # Convert ISO strings back to dates
    if "transaction_date" in position and position["transaction_date"]:
        position["transaction_date"] = date.fromisoformat(
            position["transaction_date"]
        )
    if "expiration" in position and position["expiration"]:
        position["expiration"] = date.fromisoformat(
            position["expiration"]
        )
    
    return position
```

### Pydantic Model Serialization

```python
# Using Pydantic models
class UserModel(BaseModel):
    username: str
    created_at: datetime
    
    def to_json(self) -> str:
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, data: str) -> "UserModel":
        return cls.model_validate_json(data)

# Usage
user_json = user.to_json()
self.redis.client.set(key, user_json)

user_json = self.redis.client.get(key)
user = UserModel.from_json(user_json)
```

## Error Handling in DAOs

### Standard DAO Error Pattern

```python
class BaseDAO(ABC):
    def _log_error(self, operation: str, error: Exception) -> None:
        """Log DAO errors with context."""
        logger.error(f"DAO operation failed - {operation}: {error}")

class UserDAO(BaseDAO):
    def get_user(self, username: str) -> Optional[UserModel]:
        try:
            key = f"auth:username:{username}"
            user_json = self.redis.client.get(key)
            return UserModel.from_json(user_json) if user_json else None
        except Exception as e:
            self._log_error(f"get_user {username}", e)
            return None
```

**Rules:**
- Catch exceptions in DAO methods
- Log with context using `_log_error`
- Return `None`, `False`, or empty collections on error
- Let handlers decide how to respond

## Cache Patterns

### Cache-Aside Pattern

```python
async def get_stock_data(self, ticker: str, force_refresh: bool = False):
    # Check cache first
    if not force_refresh:
        cached = self.finance_dao.get_cached_stock_data(ticker)
        if cached:
            self.ctx.logger.info(f"Cache hit for {ticker}")
            return StockData(**cached)
    
    # Cache miss - fetch from source
    self.ctx.logger.info(f"Cache miss for {ticker}, fetching fresh data")
    data = await self.fetch_from_api(ticker)
    
    # Update cache
    ttl = get_cache_ttl()
    self.finance_dao.cache_stock_data(ticker, data.model_dump(), ttl=ttl)
    
    return data
```

### Write-Through Pattern

```python
def save_position(self, position: PositionCreate) -> dict:
    # Generate ID
    position_id = str(uuid.uuid4())
    
    # Write to Redis
    position_data = {
        "id": position_id,
        **position.model_dump(),
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # Store object
    self.redis.client.set(
        f"finance:position:{position_id}",
        json.dumps(position_data)
    )
    
    # Update index
    self.redis.client.sadd("finance:positions:index", position_id)
    
    return position_data
```

## Performance Optimization

### Batch Operations

```python
# BAD - N+1 queries
positions = []
for pos_id in position_ids:
    data = self.redis.client.get(f"finance:position:{pos_id}")
    positions.append(json.loads(data))

# GOOD - Pipeline
pipe = self.redis.client.pipeline()
for pos_id in position_ids:
    pipe.get(f"finance:position:{pos_id}")
results = pipe.execute()

positions = [json.loads(data) for data in results if data]
```

### Avoid Scanning Large Sets

```python
# BAD - KEYS command (blocks Redis)
keys = self.redis.client.keys("finance:position:*")

# GOOD - Maintain index
position_ids = self.redis.client.smembers("finance:positions:index")
```

## Common Anti-Patterns

### ❌ Using KEYS in Production

```python
# BAD - blocks Redis server
all_keys = self.redis.client.keys("*")

# GOOD - use index sets
all_ids = self.redis.client.smembers("entity:index")
```

### ❌ Not Setting TTL on Cache

```python
# BAD - cache grows forever
self.redis.client.set(f"cache:{key}", data)

# GOOD - set appropriate TTL
self.redis.client.setex(f"cache:{key}", ttl, data)
```

### ❌ Storing Large Objects Without Compression

```python
# BAD - storing huge JSON
self.redis.client.set(key, json.dumps(huge_object))

# GOOD - compress if needed
import gzip
compressed = gzip.compress(json.dumps(huge_object).encode())
self.redis.client.set(key, compressed)
```

### ❌ Not Cleaning Up Related Keys

```python
# BAD - orphaned index entries
self.redis.client.delete(f"finance:position:{pos_id}")
# Index still contains pos_id

# GOOD - clean up all related keys
self.redis.client.delete(f"finance:position:{pos_id}")
self.redis.client.srem("finance:positions:index", pos_id)
```

## Redis Client Singleton

The `RedisClient` class uses singleton pattern:

```python
class RedisClient:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not RedisClient._initialized:
            self._initialize()
            RedisClient._initialized = True
```

**Implications:**
- All DAOs share the same Redis connection
- Connection is created once on first use
- Thread-safe for FastAPI async operations
- No need to pass Redis client between DAOs
