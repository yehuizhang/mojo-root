# API Refactoring & Improvements - Implementation Tasks

## Overview

This task list implements the API refactoring improvements as specified in the requirements and design documents. Tasks are organized by phase for incremental, low-risk deployment.

## Phase 1: Foundation (No Breaking Changes)

### 1.1 Create BaseHandler Class
- [x] 1.1.1 Create `api/handlers/base_handler.py`
  - Implement `BaseHandler` class with `__init__()` that calls `build_context()`
  - Implement `_check_service_initialized()` method
  - Implement `_check_services_initialized()` method
  - Implement `_log_and_raise_error()` method
  - Add comprehensive docstrings

- [x] 1.1.2 Write unit tests for BaseHandler
  - Test `_check_service_initialized()` with valid service
  - Test `_check_service_initialized()` with None service
  - Test `_check_services_initialized()` with all valid services
  - Test `_check_services_initialized()` with some None services
  - Test `_log_and_raise_error()` logs and raises correctly
  - Verify HTTPException status codes and messages

### 1.2 Create ValidationUtils Class
- [x] 1.2.1 Create `api/lib/util/validation_util.py`
  - Implement `ValidationUtils` class
  - Implement `validate_ticker_format()` static method
  - Implement `validate_required_field()` static method
  - Implement `validate_positive_number()` static method
  - Add comprehensive docstrings

- [x] 1.2.2 Write unit tests for ValidationUtils
  - Test `validate_ticker_format()` with valid tickers (lowercase, uppercase, mixed)
  - Test `validate_ticker_format()` with invalid tickers (empty, too long, numbers)
  - Test `validate_required_field()` with valid values
  - Test `validate_required_field()` with None and empty strings
  - Test `validate_positive_number()` with positive numbers
  - Test `validate_positive_number()` with zero and negative numbers

### 1.3 Update Import Organization
- [x] 1.3.1 Fix inline imports in FinanceHandler
  - Move `generate_option_ticker` import to top of file
  - Organize imports: stdlib, third-party, local
  - Run linter to verify import order

## Phase 2: Handler Migration (One at a Time)

### 2.1 Migrate AuthHandler
- [x] 2.1.1 Update AuthHandler to extend BaseHandler
  - Change class definition to inherit from BaseHandler
  - Update `__init__()` to call `super().__init__()`
  - Remove inline `build_context()` calls in methods
  - Use `self.ctx` throughout the class
  - Update `get_current_user()` to use `self.ctx`

- [x] 2.1.2 Test AuthHandler migration
  - Run existing unit tests
  - Run integration tests
  - Verify no regressions
  - Check logs for proper context usage

### 2.2 Migrate FinanceHandler
- [x] 2.2.1 Update FinanceHandler to extend BaseHandler
  - Change class definition to inherit from BaseHandler
  - Update `__init__()` to call `super().__init__()`
  - Use `self.ctx` throughout the class

- [x] 2.2.2 Add service initialization checks
  - Add `_check_services_initialized()` calls in `get_dashboard()`
  - Add `_check_services_initialized()` calls in `add_ticker()`
  - Add `_check_services_initialized()` calls in `add_position()`
  - Add checks in other public methods as needed

- [x] 2.2.3 Update error handling
  - Replace manual error handling with `_log_and_raise_error()`
  - Ensure consistent error messages
  - Verify HTTPException status codes

- [x] 2.2.4 Add ticker validation
  - Import `ValidationUtils` at top of file
  - Use `ValidationUtils.validate_ticker_format()` in `add_ticker()`
  - Use validation in other methods that accept ticker input

- [x] 2.2.5 Test FinanceHandler migration
  - Run existing unit tests
  - Run integration tests
  - Verify no regressions
  - Test error handling paths

### 2.3 Migrate RssHandler
- [x] 2.3.1 Update RssHandler to extend BaseHandler
  - Change class definition to inherit from BaseHandler
  - Update `__init__()` to call `super().__init__()`
  - Remove inline `build_context()` calls in `publish_feed()`
  - Use `self.ctx` throughout the class

- [x] 2.3.2 Test RssHandler migration
  - Run existing unit tests
  - Run integration tests
  - Verify no regressions

### 2.4 Migrate Remaining Handlers
- [x] 2.4.1 Update GroupHandler to extend BaseHandler
  - Follow same pattern as AuthHandler
  - Test thoroughly

- [x] 2.4.2 Update InvitationHandler to extend BaseHandler
  - Follow same pattern as AuthHandler
  - Test thoroughly

- [x] 2.4.3 Update AlertHandler to extend BaseHandler
  - Follow same pattern as AuthHandler
  - Test thoroughly

- [x] 2.4.4 Update RecreationHandler to extend BaseHandler
  - Follow same pattern as AuthHandler
  - Test thoroughly

## Phase 3: Method Refactoring

### 3.1 Refactor FinanceHandler.get_dashboard()
- [x] 3.1.1 Extract `_process_ticker_for_dashboard()` method
  - Create new private method
  - Move ticker processing logic from `get_dashboard()`
  - Add docstring with parameters and return type
  - Handle exceptions within method

- [x] 3.1.2 Extract `_categorize_positions()` method
  - Create new private method
  - Move position categorization logic
  - Add docstring
  - Return dictionary with categorized positions

- [x] 3.1.3 Extract `_generate_position_recommendation()` method
  - Create new private method
  - Move recommendation generation logic
  - Add docstring
  - Handle None service gracefully

- [x] 3.1.4 Extract `_generate_signals()` method
  - Create new private method
  - Move signal generation logic
  - Add docstring
  - Return dictionary of signals

- [x] 3.1.5 Update `get_dashboard()` to use helper methods
  - Replace inline logic with method calls
  - Simplify main method to orchestration only
  - Verify method is under 50 lines

- [x] 3.1.6 Write unit tests for helper methods
  - Test `_process_ticker_for_dashboard()` with valid data
  - Test `_process_ticker_for_dashboard()` with errors
  - Test `_categorize_positions()` with different position types
  - Test `_generate_position_recommendation()` with and without service
  - Test `_generate_signals()` with different market conditions

- [ ] 3.1.7 Run integration tests
  - Verify `get_dashboard()` still works end-to-end
  - Test with multiple tickers
  - Test with various position combinations
  - Verify performance is acceptable

## Phase 4: DAO Optimization

### 4.1 Optimize FinanceDAO.get_all_positions()
- [ ] 4.1.1 Implement pipeline-based retrieval
  - Update method to use `pipeline()`
  - Batch all GET operations
  - Execute pipeline once
  - Process results

- [ ] 4.1.2 Add batch delete method
  - Create `delete_positions_batch()` method
  - Use pipeline for atomic deletion
  - Remove from index atomically
  - Add docstring

- [ ] 4.1.3 Write unit tests for optimized methods
  - Test `get_all_positions()` with empty index
  - Test `get_all_positions()` with multiple positions
  - Test `get_all_positions()` with missing positions
  - Test `delete_positions_batch()` with valid IDs
  - Test `delete_positions_batch()` with empty list
  - Mock pipeline operations

- [ ] 4.1.4 Benchmark performance
  - Create benchmark script
  - Test with 10, 50, 100, 500 positions
  - Compare old vs new implementation
  - Document results

- [ ] 4.1.5 Update handler to use batch operations
  - Update any code that deletes multiple positions
  - Use `delete_positions_batch()` where applicable

## Phase 5: Documentation & Cleanup

### 5.1 Update Steering Files
- [ ] 5.1.1 Update `api-dependency-injection.md`
  - Add BaseHandler pattern example
  - Update handler creation examples
  - Add section on extending BaseHandler

- [ ] 5.1.2 Update `api-error-handling.md`
  - Add BaseHandler error handling examples
  - Document `_log_and_raise_error()` usage
  - Add ValidationUtils examples

- [ ] 5.1.3 Update `api-context-management.md`
  - Add BaseHandler context management example
  - Update anti-patterns section
  - Add migration guide

### 5.2 Update Code Documentation
- [ ] 5.2.1 Add/update docstrings
  - Verify all public methods have docstrings
  - Verify all classes have docstrings
  - Add inline comments for complex logic

- [ ] 5.2.2 Update README files
  - Document new utilities
  - Update architecture section
  - Add migration guide for future handlers

### 5.3 Code Review & Cleanup
- [ ] 5.3.1 Run linters
  - Run black formatter
  - Run flake8
  - Fix any issues

- [ ] 5.3.2 Run tests
  - Run full test suite
  - Verify 80%+ coverage for handlers
  - Verify 70%+ coverage for DAOs

- [ ] 5.3.3 Code review checklist
  - No methods > 50 lines
  - No repeated code blocks
  - All handlers extend BaseHandler
  - Consistent error handling
  - All imports at top of files
  - All public methods documented
<!-- 
## Phase 6: Deployment & Monitoring

### 6.1 Pre-Deployment
- [ ] 6.1.1 Run full test suite
  - All unit tests pass
  - All integration tests pass
  - Coverage meets targets

- [ ] 6.1.2 Manual testing
  - Test dashboard with multiple tickers
  - Test adding/removing positions
  - Test error scenarios
  - Test with empty watchlist

- [ ] 6.1.3 Performance testing
  - Benchmark dashboard generation
  - Benchmark position retrieval
  - Verify improvements

### 6.2 Deployment
- [ ] 6.2.1 Deploy to staging
  - Deploy changes
  - Run smoke tests
  - Monitor logs

- [ ] 6.2.2 Deploy to production
  - Deploy during low-traffic period
  - Monitor error rates
  - Monitor response times
  - Monitor cache hit rates

### 6.3 Post-Deployment
- [ ] 6.3.1 Monitor metrics
  - Dashboard generation time < 2 seconds
  - Position retrieval time < 10ms for 100 positions
  - Error rate < 1%
  - Cache hit rate > 80%

- [ ] 6.3.2 Verify functionality
  - Test all endpoints
  - Verify no regressions
  - Check logs for errors

- [ ] 6.3.3 Document results
  - Record performance improvements
  - Document any issues encountered
  - Update runbook if needed -->

## Rollback Plan

If issues arise during deployment:

1. **Immediate Actions**
   - [ ] Revert to previous version
   - [ ] Verify service stability
   - [ ] Check error logs

2. **Investigation**
   - [ ] Identify root cause
   - [ ] Review metrics and logs
   - [ ] Determine fix strategy

3. **Resolution**
   - [ ] Fix issues in development
   - [ ] Test thoroughly
   - [ ] Redeploy incrementally

## Success Criteria

- [ ] All tasks completed
- [ ] All tests passing
- [ ] Code coverage targets met (80% handlers, 70% DAOs)
- [ ] No methods > 50 lines
- [ ] No repeated code blocks
- [ ] All handlers extend BaseHandler
- [ ] Consistent error handling across all handlers
- [ ] Performance improvements verified
- [ ] Documentation updated
- [ ] Steering files updated
- [ ] Production deployment successful
- [ ] No regressions in functionality
- [ ] Metrics within acceptable ranges

## Notes

- Each phase should be completed and tested before moving to the next
- Handler migrations should be done one at a time with thorough testing
- Performance benchmarks should be run before and after DAO optimization
- All changes should maintain backward compatibility
- Rollback plan should be ready before production deployment
