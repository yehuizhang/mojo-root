# Requirements Document

## Introduction

This feature adds a new `/rss` endpoint to the FastAPI service that provides personalized RSS feeds based on user
categories. The endpoint will maintain an in-memory dictionary mapping users to their subscribed categories and return
RSS-formatted content for the past week. The endpoint requires token-based authentication consistent with the existing
API security model.

## Requirements

### Requirement 1

**User Story:** As an RSS token holder, I want to access a personalized RSS feed by providing my token, so that I can
consume content from my subscribed categories in a standard RSS format.

#### Acceptance Criteria

1. WHEN a request is made to `/rss` with a valid `token` parameter THEN the system SHALL return an RSS-formatted
   response
2. WHEN a request is made with an invalid or missing token THEN the system SHALL return a 401 Unauthorized error
3. WHEN a request is made with a valid token but the user has no categories THEN the system SHALL return an empty RSS
   feed with proper RSS structure
4. WHEN a request is made with valid parameters THEN the system SHALL return content from the past 14 days only

### Requirement 2

**User Story:** As a system administrator, I want to maintain user category subscriptions in Redis, so that I can
quickly serve personalized RSS content with data persistence across service restarts.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL use the existing Redis client to access user-category mappings
2. WHEN a user requests RSS content THEN the system SHALL lookup their categories from Redis storage
3. WHEN a user has no categories defined THEN the system SHALL return an empty but valid RSS feed
4. WHEN the system needs to modify user categories THEN it SHALL update the Redis storage
5. WHEN initially deployed THEN the system SHALL support three categories: "finance", "finance-cn", and "home"

### Requirement 3

**User Story:** As an API consumer, I want the RSS response to follow standard RSS 2.0 format, so that I can use any
standard RSS reader to consume the content.

#### Acceptance Criteria

1. WHEN an RSS feed is generated THEN it SHALL include proper RSS 2.0 XML structure with required elements
2. WHEN an RSS feed is generated THEN it SHALL include channel metadata (title, description, link, lastBuildDate)
3. WHEN RSS items are included THEN each item SHALL contain title, description, link, pubDate, and guid elements
4. WHEN the response is sent THEN it SHALL have Content-Type header set to "application/rss+xml"
5. WHEN RSS content is generated THEN it SHALL be valid XML that passes RSS 2.0 validation

### Requirement 4

**User Story:** As an authenticated user, I want to receive RSS content filtered by my subscribed categories, so that I
only see relevant content in my feed.

#### Acceptance Criteria

1. WHEN a user has subscribed categories THEN the RSS feed SHALL only include items matching those categories
2. WHEN a user has multiple categories THEN the RSS feed SHALL include items from all subscribed categories
3. WHEN generating RSS items THEN the system SHALL only include items published within the last 7 days
4. WHEN no content exists for the user's categories in the past week THEN the system SHALL return an empty RSS feed with
   proper structure

### Requirement 5

**User Story:** As a content manager, I want to add RSS items via an internal API endpoint, so that I can populate the
RSS feeds with fresh content that automatically expires.

#### Acceptance Criteria

1. WHEN a POST request is made to `/internal/rss/item` with valid RSS item data THEN the system SHALL store the item in
   Redis
2. WHEN an RSS item is stored THEN it SHALL automatically expire after 14 days
3. WHEN an RSS item is added THEN it SHALL be immediately available in relevant user RSS feeds
4. WHEN adding an item without a publication date THEN the system SHALL use the current timestamp
5. WHEN the system is category-agnostic THEN it SHALL accept any category name and serve content for categories that
   exist in Redis

### Requirement 6

**User Story:** As a developer, I want the RSS endpoint to use a custom token system, so that it can operate
independently of the main API authentication.

#### Acceptance Criteria

1. WHEN implementing token validation THEN the system SHALL use Redis to map tokens to user IDs
2. WHEN a token is not found in Redis THEN the system SHALL return a 404 Not Found error
3. WHEN the endpoint is added THEN it SHALL follow the same middleware patterns (CORS, logging, process time) as
   existing endpoints
4. WHEN authentication succeeds THEN the system SHALL log the request following existing logging patterns