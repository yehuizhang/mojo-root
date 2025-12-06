# Implementation Plan

- [x] 
    1. Create RSS data models and validation

    - Create `api/models/rss_models.py` with RSSItem, RSSItemCreate, and RSSChannel models
    - Implement Pydantic validation for RSS item creation
    - Add GUID generation logic for RSS items
    - _Requirements: 3.1, 3.2, 3.3, 5.4_

- [x] 
    2. Implement RSS service layer

    - [x] 2.1 Create `api/services/rss_service.py` with RSSService class

        - Implement token-to-user lookup using Redis
        - Implement user-to-categories lookup using Redis
        - Add RSS item storage using individual keys with UUID v7 pattern: `rss:category:{category}:{uuid_v7}`
        - Implement 14-day TTL on individual item keys
        - _Requirements: 2.1, 2.2, 5.1, 5.2_

    - [x] 2.2 Implement RSS XML generation

        - Create RSS 2.0 compliant XML generation method
        - Add proper XML escaping and formatting
        - Include required RSS channel metadata
        - _Requirements: 3.1, 3.2, 3.3_

    - [x] 2.3 Implement content retrieval with UUID v7 sorting
        - Add category content retrieval using Redis SCAN with pattern matching
        - Implement UUID v7-based chronological sorting (newest first)
        - Use batch MGET for efficient item retrieval
        - Handle empty categories and corrupted items gracefully
        - _Requirements: 1.4, 4.1, 4.2, 4.3, 4.4_

- [x] 
    3. Create RSS router and endpoints

    - [x] 3.1 Create `api/routers/rss_router.py` with GET /rss endpoint

        - Implement token parameter validation
        - Add RSS service integration
        - Return proper RSS XML response with correct Content-Type
        - _Requirements: 1.1, 1.2, 1.3, 3.4_

    - [x] 3.2 Implement POST /internal/rss/item endpoint

        - Add RSS item creation endpoint
        - Validate incoming RSS item data using RSSItemCreate model
        - Generate UUID v7 GUID and store items using individual Redis keys
        - Set 14-day TTL on each item key for automatic cleanup
        - _Requirements: 5.1, 5.2, 5.3_

    - [x] 3.3 Add error handling and HTTP responses
        - Implement 401 for invalid tokens
        - Implement 404 for missing tokens
        - Add proper error response formatting
        - _Requirements: 1.2, 6.2_

- [x] 
    4. Integrate RSS router with main application

    - Add RSS router to main FastAPI application
    - Ensure middleware integration (CORS, logging, process time)
    - Test endpoint accessibility and response headers
    - _Requirements: 6.3, 6.4_

- [ ]\* 5. Create comprehensive test suite
- [ ]\* 5.1 Write unit tests for RSS service methods

- Test token-to-user lookup functionality
- Test RSS XML generation and validation
- Test UUID v7 sorting and pattern matching logic
- Test individual key storage and retrieval
- _Requirements: 2.1, 2.2, 3.1, 4.4_

- [ ]\* 5.2 Write integration tests for RSS endpoints

- Test GET /rss endpoint with valid and invalid tokens
- Test POST /internal/rss/item endpoint functionality
- Test Redis individual key storage and UUID v7 sorting
- Test TTL behavior and automatic item expiration
- _Requirements: 1.1, 1.2, 5.1, 5.2_

- [ ] 5.3 Write API validation tests

- Test RSS XML structure compliance
- Test Content-Type header correctness
- Test error response formats
- _Requirements: 3.1, 3.4, 6.2_

- [ ] 
    6. Add Redis data management utilities

    - [ ] 6.1 Create utility functions for token management

        - Add function to create token-to-user mappings
        - Add function to manage user category subscriptions
        - Include Redis key pattern documentation
        - _Requirements: 2.1, 2.2, 6.1_

    - [ ] 6.2 Implement RSS item utilities and debugging tools
        - Add function to list items by category using pattern matching
        - Add utility to inspect Redis keys and item counts per category
        - Include debugging utilities for UUID v7 sorting verification
        - Note: No manual cleanup needed - Redis TTL handles expiration automatically
        - _Requirements: 5.2, 5.5_
