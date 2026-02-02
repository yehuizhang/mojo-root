# Backend Development Patterns

FastAPI, Redis, and Python patterns for backend development.

**These files are conditionally active** - they're included when working with Python/FastAPI files.

## Files

- **fastapi-basics.md** - Dependency injection, error handling, context management, Handler+DAO pattern
- **fastapi-async.md** - Async/await patterns, concurrent operations, testing async code
- **redis-patterns.md** - Redis key naming, caching strategies, data serialization
- **testing.md** - Testing patterns with pytest, mocking, fixtures

## When to Reference

These files are automatically included when working with:
- Python files (`**/*.py`)
- FastAPI handlers, routers, DAOs
- Service layer implementations
- Test files

## Activation

Add this frontmatter to activate for Python files:
```yaml
---
inclusion: fileMatch
fileMatchPattern: '**/*.py'
---
```
