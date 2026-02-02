# Requirements Document: Options Chain Strike Price Filtering

## Introduction

The Options Chain Strike Price Filtering feature optimizes the options chain data fetching by filtering strikes to only those near the current market price. Currently, the system fetches all available strikes for each expiration date, resulting in 200-500+ contracts per ticker. By filtering to strikes within a configurable percentage range of the current price, we can reduce data volume by 60-80% while maintaining all necessary data for signal generation and position tracking. This optimization reduces API costs, improves response times, and decreases cache storage requirements without sacrificing functionality.

## Glossary

- **Strike_Price**: The price at which an option can be exercised
- **Current_Price**: The current market price of the underlying stock
- **Strike_Range**: The percentage range above and below current price to include strikes (e.g., ±20%)
- **Short_Term_Range**: Strike filtering range for 0-60 day options (default: ±20%)
- **Medium_Term_Range**: Strike filtering range for 60 days - 12 months options (default: ±25%)
- **Long_Term_Range**: Strike filtering range for 12-30 months options (default: ±30%)
- **Massive_API**: External API service (Polygon.io) providing options data
- **Options_Chain**: Collection of all option contracts for a given underlying stock
- **DTE**: Days To Expiration
- **ATM**: At-The-Money (strike price near current stock price)
- **OTM**: Out-of-The-Money (strike price unfavorable for exercise)
- **ITM**: In-The-Money (strike price favorable for exercise)

## Requirements

### Requirement 1: Strike Price Range Calculation

**User Story:** As a system, I want to calculate strike price ranges based on current stock price and time to expiration, so that I can filter options chains to relevant strikes only.

#### Acceptance Criteria

1. WHEN fetching options chain, THE System SHALL first fetch current stock price for the ticker
2. WHEN current price is fetched, THE System SHALL calculate lower strike bound as current_price * (1 - strike_range_percentage)
3. WHEN current price is fetched, THE System SHALL calculate upper strike bound as current_price * (1 + strike_range_percentage)
4. WHEN calculating strike bounds for short-term options (0-60 DTE), THE System SHALL use SHORT_TERM_STRIKE_RANGE percentage from environment
5. WHEN calculating strike bounds for medium-term options (60 days - 12 months), THE System SHALL use MEDIUM_TERM_STRIKE_RANGE percentage from environment
6. WHEN calculating strike bounds for long-term options (12-30 months), THE System SHALL use LONG_TERM_STRIKE_RANGE percentage from environment
7. WHEN strike range percentage is not configured, THE System SHALL use default values: 20% short-term, 25% medium-term, 30% long-term
8. WHEN strike bounds are calculated, THE System SHALL log the values for debugging: "Filtering strikes for {ticker}: ${lower_bound} to ${upper_bound} ({range_pct}% range)"
9. WHEN current price is $100 and range is 20%, THE System SHALL calculate bounds as $80 to $120
10. WHEN strike bounds are calculated, THE System SHALL round to nearest strike increment (typically $5 or $10) to align with available strikes

### Requirement 2: Massive API Strike Filtering

**User Story:** As a developer, I want to pass strike price filters to the Massive API, so that the API returns only relevant contracts and reduces data transfer.

#### Acceptance Criteria

1. WHEN calling Massive API for options chain, THE System SHALL include strike_price.gte parameter with lower strike bound
2. WHEN calling Massive API for options chain, THE System SHALL include strike_price.lte parameter with upper strike bound
3. WHEN strike_price.gte parameter is provided, THE Massive API SHALL return only contracts with strike >= lower bound
4. WHEN strike_price.lte parameter is provided, THE Massive API SHALL return only contracts with strike <= upper bound
5. WHEN both strike parameters are provided, THE Massive API SHALL return only contracts within the range
6. WHEN strike filtering is applied, THE System SHALL log: "Fetching {term} options with strike filter: ${lower} to ${upper}"
7. WHEN Massive API response is received, THE System SHALL log contract count: "Received {count} contracts (filtered from estimated {original_count})"
8. WHEN strike filtering reduces contracts by more than 50%, THE System SHALL log: "Strike filtering reduced data by {percentage}%"
9. WHEN Massive API does not support strike filtering, THE System SHALL fall back to fetching all strikes and filter client-side
10. WHEN client-side filtering is used, THE System SHALL log warning: "API does not support strike filtering, filtering {count} contracts client-side"

### Requirement 3: Environment Configuration

**User Story:** As a system administrator, I want to configure strike price range percentages via environment variables, so that I can tune the filtering without code changes.

#### Acceptance Criteria

1. WHEN System initializes, THE System SHALL read SHORT_TERM_STRIKE_RANGE from environment (default: 0.20)
2. WHEN System initializes, THE System SHALL read MEDIUM_TERM_STRIKE_RANGE from environment (default: 0.25)
3. WHEN System initializes, THE System SHALL read LONG_TERM_STRIKE_RANGE from environment (default: 0.30)
4. WHEN environment variable is not set, THE System SHALL use default value and log: "Using default strike range: {percentage}% for {term}"
5. WHEN environment variable is set, THE System SHALL validate it is between 0.05 and 1.0 (5% to 100%)
6. WHEN environment variable is invalid, THE System SHALL log error and use default value
7. WHEN environment variable is valid, THE System SHALL log: "Configured strike range: {percentage}% for {term}"
8. WHEN strike range is set to 1.0 (100%), THE System SHALL effectively disable filtering for that term
9. WHEN strike range is set to 0.05 (5%), THE System SHALL use very tight filtering for that term
10. WHEN environment variables are changed, THE System SHALL apply new values on next options chain fetch (no restart required)

### Requirement 4: Backward Compatibility

**User Story:** As a developer, I want the strike filtering to be backward compatible with existing code, so that the change does not break current functionality.

#### Acceptance Criteria

1. WHEN get_options_chain() is called without force_refresh, THE System SHALL check cache first as before
2. WHEN cached options data exists and is valid, THE System SHALL return cached data without applying new filters
3. WHEN fetching fresh options data, THE System SHALL apply strike filtering to all three time ranges (short/medium/long)
4. WHEN combining filtered chains, THE System SHALL maintain the same data structure as before (List[OptionContract])
5. WHEN processing filtered contracts, THE System SHALL extract the same fields as before (strike, expiration, greeks, etc.)
6. WHEN caching filtered options data, THE System SHALL use the same cache key and TTL as before
7. WHEN signal generation uses options chain, THE System SHALL work with filtered data without modification
8. WHEN position tracking uses options chain, THE System SHALL continue to use individual contract snapshots (not affected by filtering)
9. WHEN existing tests run, THE System SHALL pass all tests with filtered data
10. WHEN strike filtering is disabled (range=1.0), THE System SHALL behave identically to current implementation

### Requirement 5: Data Completeness Validation

**User Story:** As a system, I want to validate that strike filtering does not exclude necessary contracts, so that signal generation and position tracking remain accurate.

#### Acceptance Criteria

1. WHEN filtering short-term options, THE System SHALL ensure ATM strikes (within 5% of current price) are always included
2. WHEN filtering medium-term options, THE System SHALL ensure strikes covering existing positions are included
3. WHEN filtering long-term options, THE System SHALL ensure LEAPS entry strikes (delta 0.70-0.85) are included
4. WHEN User has existing option position outside filtered range, THE System SHALL log warning: "Position strike ${strike} outside filtered range for {ticker}"
5. WHEN position strike is outside range, THE System SHALL still fetch individual contract snapshot for that position
6. WHEN signal generation requires strikes outside range, THE System SHALL log info: "Signal may be limited by strike filtering"
7. WHEN filtered chain contains fewer than 10 contracts per expiration, THE System SHALL log warning: "Few contracts after filtering, consider widening range"
8. WHEN filtered chain contains zero contracts for an expiration, THE System SHALL log error: "No contracts after filtering for {expiration}, range may be too tight"
9. WHEN validating filtered data, THE System SHALL verify at least one call and one put exist for each expiration
10. WHEN validation fails, THE System SHALL fall back to unfiltered fetch and log error: "Strike filtering validation failed, fetching all strikes"

### Requirement 6: Performance Monitoring

**User Story:** As a system administrator, I want to monitor the performance impact of strike filtering, so that I can verify the optimization is effective.

#### Acceptance Criteria

1. WHEN fetching options chain with filtering, THE System SHALL log start time before API call
2. WHEN options chain response is received, THE System SHALL log end time and calculate duration
3. WHEN options chain is processed, THE System SHALL log: "Options chain fetch completed in {duration}ms, {count} contracts"
4. WHEN comparing to previous unfiltered fetch, THE System SHALL log estimated reduction: "Estimated {percentage}% reduction in data volume"
5. WHEN caching filtered data, THE System SHALL log cache size: "Cached {size}KB for {ticker} options chain"
6. WHEN cache size is significantly smaller than before, THE System SHALL log: "Cache size reduced by {percentage}% with strike filtering"
7. WHEN API call duration is faster than historical average, THE System SHALL log: "API response {percentage}% faster with filtering"
8. WHEN processing time is measured, THE System SHALL include time for: API call, parsing, filtering (if client-side), and caching
9. WHEN performance metrics are collected, THE System SHALL store them in Redis with key "metrics:options_chain:{ticker}" for 24 hours
10. WHEN performance degrades (slower than before), THE System SHALL log warning: "Strike filtering may not be improving performance"

### Requirement 7: Testing and Validation

**User Story:** As a developer, I want comprehensive tests for strike filtering, so that I can ensure the feature works correctly across different scenarios.

#### Acceptance Criteria

1. WHEN running unit tests, THE System SHALL test strike range calculation with various current prices and percentages
2. WHEN running unit tests, THE System SHALL test that strike bounds are correctly passed to Massive API
3. WHEN running unit tests, THE System SHALL test that filtered contracts are within expected range
4. WHEN running unit tests, THE System SHALL test that ATM strikes are always included regardless of range
5. WHEN running unit tests, THE System SHALL test that environment variable parsing handles valid and invalid values
6. WHEN running unit tests, THE System SHALL test that default values are used when env vars are not set
7. WHEN running integration tests, THE System SHALL verify that signal generation works with filtered data
8. WHEN running integration tests, THE System SHALL verify that position tracking is not affected by filtering
9. WHEN running integration tests, THE System SHALL verify that cache behavior is unchanged
10. WHEN running integration tests, THE System SHALL verify that dashboard API returns correct data with filtering enabled

### Requirement 8: Documentation and Logging

**User Story:** As a developer, I want clear documentation and logging for strike filtering, so that I can understand and troubleshoot the feature.

#### Acceptance Criteria

1. WHEN strike filtering is enabled, THE System SHALL log at INFO level: "Strike filtering enabled: short={short}%, medium={medium}%, long={long}%"
2. WHEN calculating strike bounds, THE System SHALL log at DEBUG level: "Strike bounds for {ticker}: ${lower} to ${upper} (current=${current}, range={pct}%)"
3. WHEN API call includes strike filters, THE System SHALL log at INFO level: "Fetching {term} options with strike filter: ${lower} to ${upper}"
4. WHEN filtered response is received, THE System SHALL log at INFO level: "Received {count} contracts after strike filtering"
5. WHEN filtering reduces data significantly, THE System SHALL log at INFO level: "Strike filtering reduced data by {pct}% ({original} → {filtered} contracts)"
6. WHEN validation detects issues, THE System SHALL log at WARNING level with specific issue description
7. WHEN falling back to unfiltered fetch, THE System SHALL log at ERROR level with reason for fallback
8. WHEN environment variables are read, THE System SHALL log at INFO level: "Configured strike ranges: short={short}%, medium={medium}%, long={long}%"
9. WHEN using default values, THE System SHALL log at INFO level: "Using default strike ranges (not configured in environment)"
10. WHEN strike filtering is disabled (range=1.0), THE System SHALL log at INFO level: "Strike filtering disabled for {term} options (range=100%)"

### Requirement 9: Gradual Rollout Strategy

**User Story:** As a system administrator, I want to enable strike filtering gradually, so that I can monitor impact and roll back if needed.

#### Acceptance Criteria

1. WHEN ENABLE_STRIKE_FILTERING environment variable is set to "false", THE System SHALL skip strike filtering entirely
2. WHEN ENABLE_STRIKE_FILTERING is set to "true", THE System SHALL apply strike filtering to all options chain fetches
3. WHEN ENABLE_STRIKE_FILTERING is not set, THE System SHALL default to "true" (filtering enabled)
4. WHEN strike filtering is disabled via env var, THE System SHALL log: "Strike filtering disabled by configuration"
5. WHEN strike filtering is enabled via env var, THE System SHALL log: "Strike filtering enabled by configuration"
6. WHEN testing in development, THE System SHALL allow disabling filtering without code changes
7. WHEN deploying to production, THE System SHALL enable filtering by default
8. WHEN monitoring shows issues, THE System SHALL allow quick rollback by setting ENABLE_STRIKE_FILTERING=false
9. WHEN rolling back, THE System SHALL clear cached filtered data to force fresh unfiltered fetch
10. WHEN re-enabling after rollback, THE System SHALL log: "Strike filtering re-enabled, clearing stale cache"

### Requirement 10: Impact on Existing Features

**User Story:** As a user, I want strike filtering to be transparent, so that my trading signals and position tracking remain accurate.

#### Acceptance Criteria

1. WHEN viewing CSP signals, THE System SHALL show same recommendations as before (strikes within filtered range)
2. WHEN viewing Covered Call signals, THE System SHALL show same recommendations as before (strikes within filtered range)
3. WHEN viewing LEAPS signals, THE System SHALL show same recommendations as before (strikes within filtered range)
4. WHEN viewing PMCC signals, THE System SHALL show same recommendations as before (strikes within filtered range)
5. WHEN tracking option positions, THE System SHALL use individual contract snapshots (not affected by filtering)
6. WHEN calculating position metrics, THE System SHALL fetch accurate prices using individual snapshots
7. WHEN position strike is outside filtered range, THE System SHALL still display accurate position data
8. WHEN dashboard loads, THE System SHALL show same data structure and format as before
9. WHEN auto-refresh is enabled, THE System SHALL apply filtering on each refresh without user noticing
10. WHEN comparing filtered vs unfiltered signals, THE System SHALL produce identical recommendations for strikes within range

## Non-Functional Requirements

### Performance
- Options chain fetch time should be reduced by 30-50% with strike filtering
- Cache storage should be reduced by 60-80% with strike filtering
- API response time should improve by 20-40% with strike filtering

### Reliability
- Strike filtering should not cause any API errors or failures
- Fallback to unfiltered fetch should work seamlessly if filtering fails
- Cached data should remain valid and consistent with filtering enabled

### Maintainability
- Strike range percentages should be configurable without code changes
- Logging should provide clear visibility into filtering behavior
- Tests should cover all filtering scenarios and edge cases

### Scalability
- Strike filtering should work efficiently for any number of tickers in watchlist
- Performance improvements should scale linearly with number of tickers
- Cache reduction should allow tracking more tickers without storage issues
