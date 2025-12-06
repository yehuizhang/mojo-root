# Design Document

## Overview

The RSS endpoint feature adds a new `/rss` route to the FastAPI service that provides personalized RSS feeds. The system
uses Redis for persistent storage of user-category mappings and integrates with the existing bearer token authentication
system. The endpoint returns standard RSS 2.0 XML format with content filtered by user categories and limited to the
past 7 days.

## Architecture

### High-Level Flow

```
Client Request → Token Lookup → Category Lookup → Content Generation → RSS Response
     ↓              ↓              ↓                 ↓               ↓
  /rss?token=X   Redis Query    Redis Query      RSS Builder    XML Response
                 token→user     user→categories   (14-day filter) Content-Type: 
                                                                  application/rss+xml
```

### Integration Points

- **Authentication**: Custom token-based system using Redis for token-to-user mapping
- **Storage**: Uses existing `RedisClient` from `shared.persistence.redis_client`
- **Routing**: New router module following existing patterns in `api/routers/`
- **Content Management**: Internal API for adding RSS items with automatic expiration
- **Logging**: Integrates with existing request logging middleware

## Components and Interfaces

### 1. RSS Router (`api/routers/rss_router.py`)

```python
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response

rss_router = APIRouter()


@rss_router.get("/rss")
async def get_rss_feed(
        token: str = Query(..., description="RSS access token")
) -> Response:
    """Generate personalized RSS feed for token holder"""


@rss_router.post("/internal/rss/item")
async def add_rss_item(
        item: RSSItemCreate
) -> dict:
    """Add RSS item to Redis with automatic 2-week expiration"""
```

### 2. RSS Service (`api/services/rss_service.py`)

```python
class RSSService:
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client

    async def get_user_by_token(self, token: str) -> Optional[str]:
        """Retrieve user ID from RSS token"""

    async def get_user_categories(self, user: str) -> List[str]:
        """Retrieve user's subscribed categories from Redis"""

    async def get_category_content(self, categories: List[str], limit: int = 50) -> List[RSSItem]:
        """Fetch recent content for categories using UUID v7 sorting"""

    async def add_rss_item(self, item: RSSItemCreate) -> bool:
        """Add RSS item to Redis using individual key with UUID v7"""

    def generate_rss_xml(self, items: List[RSSItem], user: str) -> str:
        """Generate RSS 2.0 XML from content items"""
```

### 3. RSS Models (`api/models/rss_models.py`)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class RSSItemCreate(BaseModel):
    title: str
    description: str
    link: str
    category: str
    pub_date: Optional[datetime] = None  # Defaults to current time


class RSSItem(BaseModel):
    title: str
    description: str
    link: str
    pub_date: datetime
    guid: str
    category: str


class RSSChannel(BaseModel):
    title: str
    description: str
    link: str
    last_build_date: datetime
    items: List[RSSItem]
```

### 4. Content Management (Removed)

Content providers are no longer needed since all content will be added via the internal API endpoint. The system is now
category-agnostic and will serve any categories that exist in Redis.

## Data Models

### Redis Storage Schema

```
# Token to User mapping
Key Pattern: "rss:token:{token}"
Value: user_id string
TTL: No expiration (managed separately)

# User to Categories mapping  
Key Pattern: "rss:user:{user_id}:categories"
Value: JSON array of category strings
Example: ["finance", "home"]
TTL: No expiration (managed separately)

# RSS Items by Category (Individual Keys with UUID v7 Sorting)
Key Pattern: "rss:category:{category}:{uuid_v7_guid}"
Value: JSON serialized RSSItem object
TTL: 14 days (automatic cleanup)

# Benefits of this approach:
# - UUID v7 provides natural chronological sorting in key names
# - No separate index needed - SCAN with pattern matching
# - Clean TTL semantics - each item expires independently
# - No orphaned references or cleanup jobs required
```

### Redis Operations with UUID v7 Sorting

```python
# Adding items
async def add_rss_item(self, item: RSSItemCreate) -> bool:
    """Store RSS item using UUID v7 for natural chronological sorting."""
    rss_item = RSSItem.from_create(item)
    key = f"rss:category:{item.category}:{rss_item.guid}"

    await self.redis.setex(key, 14 * 24 * 3600, rss_item.json())
    return True


# Querying items for a category
async def get_category_items(self, category: str, limit: int = 50) -> List[RSSItem]:
    """Get recent items for category, sorted by UUID v7 chronologically."""
    pattern = f"rss:category:{category}:*"

    # Scan for all keys matching pattern
    keys = []
    async for key in self.redis.scan_iter(match=pattern, count=100):
        keys.append(key)

    if not keys:
        return []

    # Sort by UUID v7 part (newest first) - UUID v7 is chronologically sortable
    keys.sort(key=lambda k: k.split(':')[-1], reverse=True)

    # Batch fetch limited number of items
    limited_keys = keys[:limit]
    items_data = await self.redis.mget(limited_keys)

    # Parse and return items
    items = []
    for data in items_data:
        if data:
            try:
                items.append(RSSItem.parse_raw(data))
            except Exception:
                continue  # Skip corrupted items

    return items


# Multi-category feed for users
async def get_user_feed(self, user_id: str, limit: int = 50) -> List[RSSItem]:
    """Get combined feed across all user categories."""
    categories = await self.get_user_categories(user_id)

    all_items = []
    for category in categories:
        items = await self.get_category_items(category, limit * 2)  # Get extra for sorting
        all_items.extend(items)

    # Sort all items by UUID v7 (newest first) and limit
    all_items.sort(key=lambda x: x.guid, reverse=True)
    return all_items[:limit]
```

### RSS XML Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Personal RSS Feed - {user}</title>
        <description>Personalized content feed</description>
        <link>https://api.yehuizhang.com/rss?user={user}</link>
        <lastBuildDate>{current_datetime}</lastBuildDate>
        <item>
            <title>{item.title}</title>
            <description>{item.description}</description>
            <link>{item.link}</link>
            <pubDate>{item.pub_date}</pubDate>
            <guid>{item.guid}</guid>
        </item>
    </channel>
</rss>
```

## Error Handling

### Authentication Errors

```python
# 401 Unauthorized - Invalid/missing RSS token
{
    "detail": "Invalid RSS token",
    "status_code": 401
}

# 404 Not Found - Token not found in Redis
{
    "detail": "RSS token not found",
    "status_code": 404
}
```

### Validation Errors

```python
# 422 Unprocessable Entity - Missing user parameter
{
    "detail": [
        {
            "loc": ["query", "user"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

### Service Errors

```python
# 500 Internal Server Error - Redis connection issues
{
    "detail": "RSS service temporarily unavailable",
    "status_code": 500
}
```

### Empty Feed Handling

- Valid RSS structure returned even with no items
- Proper XML headers and channel metadata
- Empty `<item>` list in channel

## Testing Strategy

### Unit Tests

1. **RSS Service Tests**
    - User category retrieval from Redis
    - Content filtering by date range
    - RSS XML generation and validation

2. **Content Provider Tests**
    - Mock external API responses
    - Date filtering logic
    - Error handling for unavailable sources

3. **Model Tests**
    - RSS XML serialization
    - Pydantic model validation
    - Date handling and formatting

### Integration Tests

1. **End-to-End RSS Generation**
    - Full request flow with authentication
    - Redis integration with test data
    - XML response validation

2. **Authentication Integration**
    - Bearer token validation
    - Error response formats
    - Middleware integration

### API Tests

1. **Endpoint Testing**
    - Valid request/response cycles
    - Parameter validation
    - Content-Type header verification
    - RSS XML structure validation

## Implementation Phases

### Phase 1: Core Infrastructure

- RSS router with GET /rss endpoint
- Custom token authentication via Redis
- Redis client integration for token/user/category lookups
- Basic RSS XML generation

### Phase 2: Content Management

- POST /internal/rss/item endpoint
- RSS item storage in Redis with 2-week TTL
- Category-agnostic content retrieval
- Date filtering logic (14-day window)

### Phase 3: Enhancement

- RSS feed metadata optimization
- Performance monitoring
- Error handling improvements
- User/token management utilities

## Security Considerations

### Authentication

- Custom RSS token system independent of existing auth
- Token-to-user mapping stored in Redis
- Simple query parameter token validation

### Data Access

- User can only access their own categories
- No cross-user data leakage
- Redis keys scoped by user ID

### Input Validation

- User parameter sanitization
- Category name validation against allowed list
- XML output escaping for security

## Performance Considerations

### Caching Strategy

- Content cached in Redis with 7-day TTL
- User categories cached for quick lookup
- RSS XML generation cached per user/timestamp

### Optimization

- Async operations for external content fetching
- Batch Redis operations where possible
- Lazy loading of content providers

### Scalability

- Stateless design allows horizontal scaling
- Redis provides shared state across instances
- Content providers can be independently scaled