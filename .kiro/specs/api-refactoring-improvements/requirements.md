# API Refactoring & Improvements - Requirements

## 1. Overview

**Goal**: Evaluate the entire `/mojo-api/api` codebase to identify and fix violations of software development best practices, including DRY (Don't Repeat Yourself), SOLID principles, and architectural patterns.

**Scope**: Complete analysis of handlers, DAOs, services, routers, and utilities to ensure consistent, maintainable, and scalable code.

## 2. User Stories

### 2.1 As a developer, I want consistent error handling patterns
**Acceptance Criteria**:
- All handlers use standardized HTTPException patterns
- Error messages are descriptive and consistent
- Logging follows consistent patterns (ERROR, WARNING, INFO)
- No silent exception swallowing

### 2.2 As a developer, I want to eliminate code duplication
**Acceptance Criteria**:
- No repeated `build_context()` calls in the same class
- Common error handling extracted to reusable functions
- Repeated validation logic consolidated
- Similar handler methods share common base implementations

### 2.3 As a developer, I want consistent dependency injection
**Acceptance Criteria**:
- All handlers receive dependencies via constructor injection
- Factory functions follow consistent patterns
- No direct instantiation of DAOs in handlers
- Services properly injected into handlers

### 2.4 As a developer, I want optimized Redis operations
**Acceptance Criteria**:
- No N+1 query patterns
- Proper use of pipelines for batch operations
- Consistent key naming conventions
- Appropriate TTL strategies for all cached data

### 2.5 As a developer, I want proper async/await usage
**Acceptance Criteria**:
- Async used only for I/O-bound operations
- Sync used for CPU-bound calculations
- No blocking operations in async functions
- Proper error handling in concurrent operations

## 3. Identified Issues

### 3.1 Context Management Issues

**Issue**: Repeated `build_context()` calls
- `AuthHandler.get_current_user()` creates context inline
- `RssHandler.publish_feed()` creates context inline
- Router helper functions create context repeatedly

**Impact**: Unnecessary function calls, inconsistent pattern

**Priority**: Medium

### 3.2 Error Handling Inconsistencies

**Issue**: Inconsistent HTTPException patterns
- Some handlers check service initialization, others don't
- Error messages vary in format and detail
- Some methods log errors, others don't

**Impact**: Harder to debug, inconsistent API responses

**Priority**: High

### 3.3 Code Duplication

**Issue**: Repeated validation logic
- Service initialization checks repeated in multiple handler methods
- Similar error handling patterns duplicated
- Ticker validation logic repeated

**Impact**: Maintenance burden, potential for inconsistencies

**Priority**: High

### 3.4 Redis Pattern Violations

**Issue**: Potential N+1 queries
- `FinanceDAO.get_all_positions()` fetches positions one by one
- Could use pipeline for batch retrieval

**Impact**: Performance degradation with many positions

**Priority**: Medium

### 3.5 Missing Abstractions

**Issue**: No base handler class
- Common patterns (service checks, error handling) repeated
- No shared utilities for common operations

**Impact**: Code duplication, harder to maintain

**Priority**: Medium

### 3.6 Inline Imports

**Issue**: Import inside method
- `FinanceHandler._calculate_position_metrics()` imports `generate_option_ticker` inline

**Impact**: Slower execution, non-standard pattern

**Priority**: Low

### 3.7 Large Method Complexity

**Issue**: `FinanceHandler.get_dashboard()` is 150+ lines
- Multiple responsibilities (fetching, processing, categorizing)
- Hard to test individual pieces
- Difficult to understand flow

**Impact**: Maintainability, testability

**Priority**: High

### 3.8 Inconsistent Async Patterns

**Issue**: Mixed async/sync without clear rationale
- Some handlers are async, others sync
- Not always clear why async is used

**Impact**: Confusion, potential performance issues

**Priority**: Medium

## 4. Proposed Solutions

### 4.1 Context Management Refactoring

**Solution**: Store context in constructor for all classes

**Changes**:
- Move `build_context()` to `AuthHandler.__init__()`
- Move `build_context()` to `RssHandler.__init__()`
- Update router helpers to use stored context or accept as parameter

**Files Affected**:
- `api/handlers/auth_handler.py`
- `api/handlers/rss_handler.py`
- `api/routers/auth_router.py`

### 4.2 Standardize Error Handling

**Solution**: Create base handler class with common error handling

**Changes**:
- Create `BaseHandler` with service initialization checks
- Add common error handling methods
- Update all handlers to inherit from `BaseHandler`

**Files Affected**:
- `api/handlers/base_handler.py` (new)
- All handler files

### 4.3 Extract Common Validation Logic

**Solution**: Create validation utilities

**Changes**:
- Create `ValidationUtils` class
- Extract ticker validation
- Extract service initialization checks
- Extract common error responses

**Files Affected**:
- `api/lib/util/validation_util.py` (new)
- All handler files

### 4.4 Optimize Redis Operations

**Solution**: Use pipelines for batch operations

**Changes**:
- Update `FinanceDAO.get_all_positions()` to use pipeline
- Add batch retrieval methods where needed
- Document pipeline usage patterns

**Files Affected**:
- `api/dao/finance_dao.py`

### 4.5 Refactor Large Methods

**Solution**: Break down `get_dashboard()` into smaller methods

**Changes**:
- Extract position processing logic
- Extract signal generation logic
- Extract position categorization logic
- Create helper methods for each responsibility

**Files Affected**:
- `api/handlers/finance_handler.py`

### 4.6 Fix Import Organization

**Solution**: Move all imports to top of file

**Changes**:
- Move `generate_option_ticker` import to top
- Check for other inline imports

**Files Affected**:
- `api/handlers/finance_handler.py`

### 4.7 Document Async Usage

**Solution**: Add docstring comments explaining async choices

**Changes**:
- Document why methods are async
- Add comments for I/O-bound vs CPU-bound operations
- Update steering files with examples

**Files Affected**:
- All handler and service files with async methods

## 5. Implementation Plan

### Phase 1: Quick Wins (Low Risk, High Impact)
1. Fix inline imports
2. Standardize context management
3. Add missing docstrings

### Phase 2: Error Handling (Medium Risk, High Impact)
1. Create `BaseHandler` class
2. Update all handlers to inherit
3. Standardize error responses

### Phase 3: Code Deduplication (Medium Risk, Medium Impact)
1. Extract validation utilities
2. Create common helper methods
3. Refactor repeated patterns

### Phase 4: Performance Optimization (Low Risk, Medium Impact)
1. Optimize Redis operations
2. Add pipeline usage
3. Review caching strategies

### Phase 5: Refactoring (High Risk, High Impact)
1. Break down large methods
2. Improve method organization
3. Add comprehensive tests

## 6. Success Criteria

### 6.1 Code Quality Metrics
- No methods longer than 50 lines
- No repeated code blocks (DRY violations)
- All classes follow single responsibility principle
- Consistent error handling across all handlers

### 6.2 Performance Metrics
- No N+1 query patterns
- Batch operations use pipelines
- Cache hit rates documented and monitored

### 6.3 Maintainability Metrics
- All public methods have docstrings
- Complex logic has inline comments
- Consistent patterns across similar components

### 6.4 Test Coverage
- 80%+ coverage for handlers
- 70%+ coverage for DAOs
- 80%+ coverage for services

## 7. Non-Goals

- Rewriting working functionality
- Changing external API contracts
- Modifying database schema
- Changing Redis key structures (unless necessary)

## 8. Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Write tests before refactoring
- Refactor incrementally
- Test thoroughly after each change

### Risk 2: Performance Regression
**Mitigation**:
- Benchmark before and after
- Monitor production metrics
- Have rollback plan

### Risk 3: Scope Creep
**Mitigation**:
- Stick to identified issues
- Prioritize high-impact changes
- Document future improvements separately

## 9. Dependencies

- All existing tests must pass
- No breaking changes to API contracts
- Redis connection must remain stable
- External API integrations must continue working

## 10. Timeline Estimate

- Phase 1: 2-3 hours
- Phase 2: 4-6 hours
- Phase 3: 6-8 hours
- Phase 4: 3-4 hours
- Phase 5: 8-10 hours

**Total**: 23-31 hours of development time

## 11. Review Checklist

Before considering this complete:
- [ ] All identified issues addressed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Steering files reflect new patterns
- [ ] Code review completed
- [ ] Performance benchmarks acceptable
