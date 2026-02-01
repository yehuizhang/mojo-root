---
inclusion: always
---
<!------------------------------------------------------------------------------------
   Add rules to this file or a short description and have Kiro refine them for you.
   
   Learn about inclusion modes: https://kiro.dev/docs/steering/#inclusion-modes
-------------------------------------------------------------------------------------> 

# Mojo API Codebase Patterns

## Architecture Pattern: Handler + DAO Injection

When creating or refactoring API endpoints in mojo-api:

1. **Handlers** live in `/api/handlers/` - contain business logic
2. **DAOs** live in `/api/dao/` - contain data access logic
3. **Routers** live in `/api/routers/` - thin layer, delegate to handlers
4. **Factories** wire dependencies:
   - `dao_factory.py` - creates DAO instances
   - `handler_factory.py` - creates handlers with injected DAOs via `Depends()`

## Handler Pattern

```python
class SomeHandler:
    def __init__(self, some_dao: SomeDAO):
        self.some_dao = some_dao  # Injected, not instantiated
```

## Factory Pattern

```python
def get_some_handler(
    some_dao=Depends(get_some_dao)
) -> SomeHandler:
    return SomeHandler(some_dao)
```

## Router Pattern

```python
@router.post("/endpoint")
async def endpoint(
    handler=Depends(get_some_handler),
) -> ResponseModel:
    return handler.do_something()
```

## Common Mistakes to Avoid

- Don't instantiate repositories/DAOs directly in handlers - use injection
- Don't put business logic in routers - keep them thin
- Don't access `handler.some_dao` from routers - add helper methods to handler instead

## Model Change Checklist

When modifying a model (e.g., `UserModel`), check ALL related models:
- **Response models** (e.g., `UserResponse`) - often mirror the main model
- **Request models** - may reference the changed type
- **Related handlers** - may need import updates
- **DAOs** - if field affects storage/retrieval

Example: Changing `UserModel.invited_by` from `InvitationData` to `str` requires updating `UserResponse.invited_by` too.

## Redis Key Simplification

Prefer single-key storage over index patterns when possible:
- Instead of: `auth:user:<id>` + `auth:username:<username>` → `<id>`
- Use: `auth:username:<username>` → full object (keep id in object)

This reduces complexity and eliminates two-step lookups.
