# Requirements Document: Stock Tracking Assistant

## Introduction

The Stock Tracking Assistant is a real-time system that helps users track stock and options positions for any ticker, with initial focus on GOOGL and NVDA. The system identifies optimal timing for three options trading strategies: LEAPS (long-term growth), PMCC (Poor Man's Covered Call for leveraged income), and the Wheel strategy (cash-secured puts and covered calls). Users maintain a watchlist of tickers they want to track and can add/remove tickers as needed. The system integrates with mojo-api (FastAPI backend) and mojo-next (Next.js frontend), fetching real-time data from Massive API (Polygon.io) with Redis caching. No persistent database storage is used - all data is fetched on-demand and cached temporarily.

## Glossary

- **System**: The Stock Tracking Assistant application
- **User**: A trader who holds or wants to trade GOOGL and NVDA stocks and options
- **Ticker**: A stock symbol (e.g., GOOGL, NVDA, AAPL)
- **Watchlist**: A list of tickers that the user wants to track
- **OHLCV**: Open, High, Low, Close, Volume price data
- **DMA**: Daily Moving Average
- **ATR**: Average True Range (volatility measure)
- **RSI**: Relative Strength Index (momentum indicator)
- **IV**: Implied Volatility
- **IV_Rank**: Current IV relative to 52-week IV range (0-100)
- **IV_Percentile**: Percentage of days in past year where IV was lower than current
- **DTE**: Days To Expiration
- **Greeks**: Options risk metrics (delta, gamma, theta, vega)
- **CSP**: Cash-Secured Put
- **LEAPS**: Long-term Equity Anticipation Securities (options with 1+ year expiration)
- **PMCC**: Poor Man's Covered Call (buying deep ITM LEAPS and selling short-term calls against it)
- **Wheel_Strategy**: Selling CSPs to acquire stock, then selling covered calls for income
- **Signal_Score**: A rating indicating trade opportunity quality (Red/Yellow/Green)
- **Cost_Basis**: User's average purchase price per share
- **Massive_API**: External API service (Polygon.io) providing stock and options data via RESTClient
- **Backend**: The mojo-api FastAPI service
- **Frontend**: The mojo-next Next.js application
- **Redis_Cache**: Redis database for caching real-time market data

## Requirements

### Requirement 1: Real-Time Market Data Fetching

**User Story:** As a user, I want the system to fetch real-time market data for GOOGL and NVDA on demand, so that I have current information for making trading decisions.

#### Acceptance Criteria

1. WHEN API endpoint is called, THE System SHALL fetch current and historical daily aggregate bars for requested ticker using RESTClient.get_aggs()
2. WHEN aggregate bars are fetched, THE System SHALL extract open, high, low, close, volume, and vwap from response
3. WHEN daily data is fetched, THE System SHALL calculate 52-week high and low values from past 252 trading days
4. WHEN daily data is fetched, THE System SHALL calculate returns for 1D, 1W, 1M, 3M, 6M, and 1Y periods
5. WHEN daily data is fetched, THE System SHALL calculate 20-day, 50-day, and 200-day moving averages
6. WHEN daily data is fetched, THE System SHALL calculate 20-day historical volatility using standard deviation of returns
7. WHEN daily data is fetched, THE System SHALL calculate 14-day RSI (Relative Strength Index)
8. WHEN daily data is fetched, THE System SHALL calculate Average True Range (ATR) using high-low-close data
9. WHEN market data is calculated, THE System SHALL cache results in Redis_Cache with 5-minute expiration
10. WHEN cached data exists and is less than 5 minutes old, THE System SHALL return cached data without fetching from Massive_API

### Requirement 2: Options Chain Data Fetching

**User Story:** As a user, I want the system to fetch current options chain data including Greeks and IV metrics, so that I can evaluate potential options trades.

#### Acceptance Criteria

1. WHEN API endpoint is called, THE System SHALL fetch options chain snapshot for requested ticker using RESTClient.get_snapshot_option_chain()
2. WHEN fetching options chains, THE System SHALL retrieve all available expirations and filter for 7, 14, 21, 30, 45, and 60+ DTE
3. WHEN options data is fetched, THE System SHALL extract delta, gamma, theta, and vega from greeks attribute for each contract
4. WHEN options data is fetched, THE System SHALL extract implied_volatility for each contract
5. WHEN options data is fetched, THE System SHALL calculate at-the-money (ATM) implied volatility from contracts nearest to current price
6. WHEN options data is fetched, THE System SHALL calculate IV_Rank as (current_IV - 52week_low_IV) / (52week_high_IV - 52week_low_IV) * 100
7. WHEN options data is fetched, THE System SHALL calculate IV_Percentile as percentage of days in past year where IV was lower than current
8. WHEN options data is received, THE System SHALL cache the data in Redis_Cache with 15-minute expiration
9. WHEN extracting contract details, THE System SHALL parse strike_price, expiration_date, contract_type, and last_quote from response
10. WHEN cached options data exists and is less than 15 minutes old, THE System SHALL return cached data

### Requirement 3: Earnings Calendar Tracking

**User Story:** As a user, I want the system to track upcoming earnings dates, so that I can avoid opening positions too close to earnings announcements.

#### Acceptance Criteria

1. WHEN fetching stock data, THE System SHALL retrieve the next earnings date for the ticker from Massive_API
2. WHEN an earnings date is fetched, THE System SHALL calculate and return days until earnings
3. WHEN earnings are within 10 days, THE System SHALL set an earnings_proximity flag to true
4. WHEN earnings_proximity flag is true, THE System SHALL include warning in signal responses
5. WHEN earnings date is not available, THE System SHALL log warning and continue without earnings data

### Requirement 4: Technical Analysis Calculations

**User Story:** As a user, I want the system to identify support and resistance levels and track swing highs and lows, so that I can make informed decisions about strike selection.

#### Acceptance Criteria

1. WHEN daily data is processed, THE System SHALL identify support levels using local minima from past 60 days
2. WHEN daily data is processed, THE System SHALL identify resistance levels using local maxima from past 60 days
3. WHEN daily data is processed, THE System SHALL identify the most recent swing high (highest high in past 20 days)
4. WHEN daily data is processed, THE System SHALL identify the most recent swing low (lowest low in past 20 days)
5. WHEN price breaks above a resistance level by more than 2%, THE System SHALL update resistance levels
6. WHEN price breaks below a support level by more than 2%, THE System SHALL update support levels

### Requirement 5: Cash-Secured Put Signal Generation

**User Story:** As a user, I want the system to identify good opportunities to sell cash-secured puts for Wheel strategy entry, so that I can acquire stock at favorable prices.

#### Acceptance Criteria

1. WHEN generating CSP signals, THE System SHALL detect if current price is 5-15% below recent swing high
2. WHEN generating CSP signals, THE System SHALL calculate RSI and check if it is between 40 and 55
3. WHEN generating CSP signals, THE System SHALL verify IV_Percentile is greater than 50
4. WHEN generating CSP signals, THE System SHALL verify earnings are not within 7-10 days
5. WHEN all CSP conditions are met, THE System SHALL assign a Signal_Score of Green
6. WHEN 2-3 CSP conditions are met, THE System SHALL assign a Signal_Score of Yellow
7. WHEN fewer than 2 CSP conditions are met, THE System SHALL assign a Signal_Score of Red
8. WHEN CSP signal is Green or Yellow, THE System SHALL suggest put strikes with delta between 0.20 and 0.30
9. WHEN CSP signal is Green or Yellow, THE System SHALL suggest expirations between 21 and 45 DTE
10. WHEN suggesting strikes, THE System SHALL include premium amount, break-even price, and return on capital

### Requirement 6: Covered Call Signal Generation

**User Story:** As a user, I want the system to identify good opportunities to sell covered calls for Wheel strategy income, so that I can generate returns from my stock positions.

#### Acceptance Criteria

1. WHEN generating covered call signals, THE System SHALL detect if current price is above 20-day moving average
2. WHEN generating covered call signals, THE System SHALL calculate RSI and check if it is greater than 60
3. WHEN generating covered call signals, THE System SHALL check if current price is within 3% of a resistance level
4. WHEN generating covered call signals, THE System SHALL verify IV_Percentile is greater than 40
5. WHEN generating covered call signals, THE System SHALL verify earnings are not within 7-10 days
6. WHEN all covered call conditions are met, THE System SHALL assign a Signal_Score of Green
7. WHEN 3-4 covered call conditions are met, THE System SHALL assign a Signal_Score of Yellow
8. WHEN fewer than 3 covered call conditions are met, THE System SHALL assign a Signal_Score of Red
9. WHEN User has existing positions, THE System SHALL only suggest strikes above User's Cost_Basis
10. WHEN covered call signal is Green or Yellow, THE System SHALL suggest call strikes with delta between 0.20 and 0.30
11. WHEN covered call signal is Green or Yellow, THE System SHALL suggest expirations between 14 and 30 DTE
12. WHEN suggesting strikes, THE System SHALL include premium amount, effective sale price, and annualized return

### Requirement 7: LEAPS Purchase Signal Generation

**User Story:** As a user, I want the system to identify good opportunities to buy LEAPS, so that I can establish long-term bullish positions or set up PMCC strategies at favorable entry points.

#### Acceptance Criteria

1. WHEN generating LEAPS signals, THE System SHALL detect if current price is 10-25% below 52-week high
2. WHEN generating LEAPS signals, THE System SHALL verify IV_Percentile is below 50 or within 5 days post-earnings
3. WHEN generating LEAPS signals, THE System SHALL verify current price is above 200-day moving average
4. WHEN generating LEAPS signals, THE System SHALL verify 50-day moving average is above 200-day moving average
5. WHEN all LEAPS conditions are met, THE System SHALL assign a Signal_Score of Green
6. WHEN 2-3 LEAPS conditions are met, THE System SHALL assign a Signal_Score of Yellow
7. WHEN fewer than 2 LEAPS conditions are met, THE System SHALL assign a Signal_Score of Red
8. WHEN LEAPS signal is Green or Yellow, THE System SHALL suggest call strikes with delta between 0.70 and 0.85
9. WHEN LEAPS signal is Green or Yellow, THE System SHALL suggest expirations between 18 and 30 months
10. WHEN suggesting LEAPS, THE System SHALL include cost, break-even price, leverage ratio, and extrinsic value

### Requirement 8: PMCC Signal Generation

**User Story:** As a user, I want the system to identify good opportunities to establish or manage PMCC positions, so that I can generate leveraged income with defined risk.

#### Acceptance Criteria

1. WHEN User has no LEAPS position, THE System SHALL display LEAPS purchase signals as entry opportunity for PMCC
2. WHEN User has existing LEAPS position, THE System SHALL calculate days to expiration and remaining extrinsic value
3. WHEN User has existing LEAPS position, THE System SHALL detect if current price is above 20-day moving average for selling short calls
4. WHEN User has existing LEAPS position, THE System SHALL calculate RSI and check if it is greater than 60
5. WHEN User has existing LEAPS position, THE System SHALL verify IV_Percentile is greater than 40
6. WHEN all short call conditions are met, THE System SHALL assign a Signal_Score of Green for selling calls
7. WHEN 2 short call conditions are met, THE System SHALL assign a Signal_Score of Yellow for selling calls
8. WHEN fewer than 2 short call conditions are met, THE System SHALL assign a Signal_Score of Red for selling calls
9. WHEN suggesting short calls for PMCC, THE System SHALL only suggest strikes above LEAPS strike price
10. WHEN suggesting short calls for PMCC, THE System SHALL suggest strikes with delta between 0.20 and 0.30
11. WHEN suggesting short calls for PMCC, THE System SHALL suggest expirations between 14 and 45 DTE
12. WHEN LEAPS position has less than 90 days to expiration, THE System SHALL flag it for rolling consideration

### Requirement 9: Watchlist Management

**User Story:** As a user, I want to manage a watchlist of tickers I care about, so that the system tracks and displays data for my selected stocks.

#### Acceptance Criteria

1. WHEN System initializes for first time, THE System SHALL create default watchlist with GOOGL and NVDA in Redis_Cache
2. WHEN User adds a ticker to watchlist, THE System SHALL validate ticker exists in Massive_API before adding
3. WHEN User adds a ticker to watchlist, THE System SHALL store it in Redis_Cache with key "watchlist:tickers"
4. WHEN User removes a ticker from watchlist, THE System SHALL remove it from Redis_Cache
5. WHEN User requests watchlist, THE System SHALL return all tickers in the watchlist
6. WHEN watchlist is empty, THE System SHALL return empty array
7. WHEN watchlist data is stored, THE System SHALL set Redis expiration to never expire (persistent watchlist)
8. WHEN ticker is removed from watchlist, THE System SHALL also remove any cached market data for that ticker

### Requirement 10: Position Tracking

**User Story:** As a user, I want to track my current stock and options positions with transaction details, so that the system can provide personalized recommendations based on my holdings.

#### Acceptance Criteria

1. WHEN User adds a stock position, THE System SHALL store ticker, transaction_date, quantity, and purchase_price in Redis_Cache
2. WHEN User adds an options position, THE System SHALL store ticker, option_type, strike, expiration, transaction_date, quantity, and premium in Redis_Cache
3. WHEN User updates a position, THE System SHALL validate the new data and update the cached record
4. WHEN User deletes a position, THE System SHALL remove the record from Redis_Cache
5. WHEN User has existing stock positions, THE System SHALL calculate current market value using latest price and unrealized gain/loss
6. WHEN User has existing options positions, THE System SHALL fetch current option price, calculate current value, days to expiration, and profit/loss
7. WHEN position data is stored, THE System SHALL set Redis expiration to 90 days to prevent stale data
8. WHEN calculating position metrics, THE System SHALL use cached market data if available and less than 5 minutes old
9. WHEN User adds position for ticker not in watchlist, THE System SHALL automatically add ticker to watchlist

### Requirement 11: Dashboard Data API

**User Story:** As a developer, I want a REST API endpoint that provides comprehensive dashboard data for all watchlist tickers, so that the frontend can display strategy-specific sections.

#### Acceptance Criteria

1. WHEN GET /api/dashboard is called, THE Backend SHALL retrieve watchlist from Redis_Cache
2. WHEN GET /api/dashboard is called, THE Backend SHALL return data for all tickers in the watchlist
3. WHEN GET /api/dashboard is called, THE Backend SHALL include current price, daily change, earnings countdown, and IV_Percentile for each ticker
3. WHEN GET /api/dashboard is called, THE Backend SHALL include current positions for each ticker if they exist in Redis_Cache
4. WHEN GET /api/dashboard is called, THE Backend SHALL include LEAPS strategy data with signals and recommended contracts for each ticker
5. WHEN GET /api/dashboard is called, THE Backend SHALL include PMCC strategy data with signals and recommended short calls for each ticker
6. WHEN GET /api/dashboard is called, THE Backend SHALL include Wheel strategy data with CSP and covered call signals for each ticker
7. WHEN User has positions for a strategy, THE Backend SHALL include position metrics and management recommendations
8. WHEN User has no positions for a strategy, THE Backend SHALL include entry timing signals and recommendations
9. WHEN GET /api/dashboard is called, THE Backend SHALL return cached data if available and less than 5 minutes old
10. WHEN cached data is expired or missing, THE Backend SHALL fetch fresh data from Massive_API and update cache

### Requirement 12: Watchlist Management API

**User Story:** As a developer, I want REST API endpoints to manage the watchlist, so that the frontend can add/remove tickers.

#### Acceptance Criteria

1. WHEN GET /api/watchlist is called, THE Backend SHALL return all tickers in the watchlist from Redis_Cache
2. WHEN POST /api/watchlist is called with valid ticker, THE Backend SHALL validate ticker exists in Massive_API
3. WHEN POST /api/watchlist is called with valid ticker, THE Backend SHALL add ticker to watchlist in Redis_Cache
4. WHEN POST /api/watchlist is called with invalid ticker, THE Backend SHALL return 400 error with message "Ticker not found"
5. WHEN POST /api/watchlist is called with ticker already in watchlist, THE Backend SHALL return 409 error with message "Ticker already in watchlist"
6. WHEN DELETE /api/watchlist/{ticker} is called, THE Backend SHALL remove ticker from watchlist in Redis_Cache
7. WHEN DELETE /api/watchlist/{ticker} is called for ticker not in watchlist, THE Backend SHALL return 404 error
8. WHEN watchlist endpoints are called, THE Backend SHALL allow access without authentication token

### Requirement 13: Portfolio Positions API

**User Story:** As a developer, I want REST API endpoints to manage user positions with transaction details, so that the frontend can store and retrieve portfolio holdings.

#### Acceptance Criteria

1. WHEN GET /api/portfolio/positions is called, THE Backend SHALL return all User's stock and options positions from Redis_Cache
2. WHEN GET /api/portfolio/positions is called, THE Backend SHALL include current market value and unrealized P&L for each position
3. WHEN POST /api/portfolio/positions is called with position_type="stock", THE Backend SHALL expect: ticker, transaction_date, quantity, purchase_price
4. WHEN POST /api/portfolio/positions is called with position_type="option", THE Backend SHALL expect: ticker, option_type, strike, expiration, transaction_date, quantity, premium
5. WHEN POST /api/portfolio/positions is called with valid data, THE Backend SHALL create a new position record in Redis_Cache with generated ID
6. WHEN POST /api/portfolio/positions is called with invalid data, THE Backend SHALL return 400 error with validation details
7. WHEN PUT /api/portfolio/positions/{id} is called with valid data, THE Backend SHALL update the existing position in Redis_Cache
8. WHEN DELETE /api/portfolio/positions/{id} is called, THE Backend SHALL remove the position from Redis_Cache
9. WHEN POST /api/portfolio/positions is called, THE Backend SHALL validate that ticker is either GOOGL or NVDA
10. WHEN storing position data, THE Backend SHALL set Redis expiration to 90 days to prevent stale data
11. WHEN portfolio endpoints are called, THE Backend SHALL require authentication token

### Requirement 14: Dashboard UI Structure

**User Story:** As a user, I want to see a dashboard at /zyh/finance with separate sections for each watchlist stock and strategy, so that I can quickly assess all trading opportunities.

#### Acceptance Criteria

1. WHEN User navigates to /zyh/finance page, THE Frontend SHALL display sections for all tickers in the watchlist
2. WHEN displaying each stock section, THE Frontend SHALL show a header with ticker, current price, daily change percentage, and trend badge
3. WHEN displaying each stock section, THE Frontend SHALL show earnings countdown and IV_Percentile badge in the header
4. WHEN User has positions for a stock, THE Frontend SHALL display position summary in the stock header
5. WHEN displaying each stock section, THE Frontend SHALL show three strategy subsections: LEAPS, PMCC, and Wheel
6. WHEN page loads, THE Frontend SHALL display an "Auto Refresh" toggle button in off state at the top
7. WHEN page loads, THE Frontend SHALL display a refresh period dropdown with options: 5s, 15s, 30s, 1m, 5m, 10m, 30m
8. WHEN page loads, THE Frontend SHALL display "Add Ticker" button at the top to manage watchlist
9. WHEN Auto Refresh toggle is turned on, THE Frontend SHALL refresh data at the selected interval
10. WHEN Auto Refresh toggle is turned off, THE Frontend SHALL stop automatic data refresh
11. WHEN page is viewed on iPhone 15, THE Frontend SHALL display responsive layout optimized for mobile screen width (390px)
12. WHEN page is viewed on mobile, THE Frontend SHALL use touch-friendly button sizes (minimum 44px) and spacing

### Requirement 15: Watchlist Management UI

**User Story:** As a user, I want to add and remove tickers from my watchlist, so that I can track the stocks I care about.

#### Acceptance Criteria

1. WHEN User clicks "Add Ticker" button, THE Frontend SHALL display a modal or inline form with ticker input field
2. WHEN User enters ticker symbol and submits, THE Frontend SHALL call POST /api/watchlist with the ticker
3. WHEN ticker is successfully added, THE Frontend SHALL refresh the dashboard to show the new ticker section
4. WHEN ticker add fails, THE Frontend SHALL display error message from API response
5. WHEN displaying each stock section header, THE Frontend SHALL show a small "Remove" or "X" button
6. WHEN User clicks remove button, THE Frontend SHALL show confirmation dialog "Remove {TICKER} from watchlist?"
7. WHEN User confirms removal, THE Frontend SHALL call DELETE /api/watchlist/{ticker}
8. WHEN ticker is successfully removed, THE Frontend SHALL remove that stock section from the dashboard
9. WHEN watchlist becomes empty, THE Frontend SHALL display message "No tickers in watchlist. Click 'Add Ticker' to get started."
10. WHEN User tries to remove last ticker, THE Frontend SHALL allow it (no minimum watchlist size)

### Requirement 16: LEAPS Strategy Subsection UI

**User Story:** As a user, I want to see LEAPS strategy information for each stock, so that I can decide when to enter or manage LEAPS positions.

#### Acceptance Criteria

1. WHEN User has no LEAPS position for the stock, THE Frontend SHALL display "No Position" badge
2. WHEN User has no LEAPS position, THE Frontend SHALL show Signal_Score with color-coded indicator (Green/Yellow/Red)
3. WHEN User has no LEAPS position, THE Frontend SHALL show 3-5 reasoning bullets for the signal
4. WHEN User has no LEAPS position and signal is Green or Yellow, THE Frontend SHALL show table with 3-5 recommended LEAPS contracts
5. WHEN displaying recommended LEAPS, THE Frontend SHALL show strike, expiration, cost, delta, break-even, and leverage ratio
6. WHEN User has LEAPS position, THE Frontend SHALL display position details: strike, expiration, quantity, cost basis
7. WHEN User has LEAPS position, THE Frontend SHALL display current value, unrealized P&L percentage, and days to expiration
8. WHEN User has LEAPS position, THE Frontend SHALL display current delta and remaining extrinsic value
9. WHEN LEAPS position has less than 90 days to expiration, THE Frontend SHALL display a warning badge "Consider Rolling"
10. WHEN User clicks on a recommended LEAPS contract, THE Frontend SHALL highlight it and show additional Greeks

### Requirement 17: PMCC Strategy Subsection UI

**User Story:** As a user, I want to see PMCC strategy information for each stock, so that I can manage my leveraged income strategy.

#### Acceptance Criteria

1. WHEN User has no LEAPS position for the stock, THE Frontend SHALL display "Requires LEAPS Position" message
2. WHEN User has no LEAPS position, THE Frontend SHALL show link/button to scroll to LEAPS subsection
3. WHEN User has LEAPS position but no short call, THE Frontend SHALL display "LEAPS Established - Ready for Short Calls" badge
4. WHEN User has LEAPS position but no short call, THE Frontend SHALL show Signal_Score for selling short calls
5. WHEN User has LEAPS position but no short call, THE Frontend SHALL show 3-5 reasoning bullets for short call timing
6. WHEN short call signal is Green or Yellow, THE Frontend SHALL show table with 3-5 recommended short call strikes
7. WHEN displaying recommended short calls, THE Frontend SHALL show strike, expiration, premium, DTE, delta, and annualized return
8. WHEN User has active short call position, THE Frontend SHALL display short call details: strike, expiration, premium received
9. WHEN User has active short call position, THE Frontend SHALL display current value, P&L, days to expiration, and management recommendation
10. WHEN short call strike is at or below LEAPS strike, THE Frontend SHALL display error warning "Invalid PMCC Structure"

### Requirement 18: Wheel Strategy Subsection UI

**User Story:** As a user, I want to see Wheel strategy information for each stock, so that I can execute cash-secured puts and covered calls.

#### Acceptance Criteria

1. WHEN User has no stock position, THE Frontend SHALL display "No Stock Position - CSP Entry Phase" badge
2. WHEN User has no stock position, THE Frontend SHALL show CSP Signal_Score with color-coded indicator
3. WHEN User has no stock position, THE Frontend SHALL show 3-5 reasoning bullets for CSP timing
4. WHEN CSP signal is Green or Yellow, THE Frontend SHALL show table with 3-5 recommended put strikes
5. WHEN displaying recommended CSPs, THE Frontend SHALL show strike, expiration, premium, DTE, delta, break-even, and ROC (return on capital)
6. WHEN User has stock position, THE Frontend SHALL display position details: quantity, cost basis, current value, unrealized P&L percentage
7. WHEN User has stock position, THE Frontend SHALL show covered call Signal_Score with color-coded indicator
8. WHEN User has stock position, THE Frontend SHALL show 3-5 reasoning bullets for covered call timing
9. WHEN covered call signal is Green or Yellow, THE Frontend SHALL show table with 3-5 recommended call strikes
10. WHEN displaying recommended covered calls, THE Frontend SHALL show strike, expiration, premium, DTE, delta, effective sale price, and annualized return
11. WHEN User has active covered call position, THE Frontend SHALL display call details: strike, expiration, premium received, current value, P&L
12. WHEN User has active covered call position, THE Frontend SHALL display management recommendation (hold/roll/close)

### Requirement 19: Position Management UI

**User Story:** As a user, I want to add, edit, and delete my positions by entering transaction details, so that I can keep my portfolio up to date.

#### Acceptance Criteria

1. WHEN displaying any strategy subsection, THE Frontend SHALL show "Add Position" button if no position exists
2. WHEN User clicks "Add Position" button, THE Frontend SHALL display inline form asking "Stock or Option?"
3. WHEN User selects "Stock", THE Frontend SHALL show input fields for: ticker (dropdown: GOOGL/NVDA), transaction date, quantity, purchase price
4. WHEN User selects "Option", THE Frontend SHALL show input fields for: ticker (dropdown: GOOGL/NVDA), option type (call/put), strike, expiration date, transaction date, quantity, premium paid/received
5. WHEN User submits position form with valid data, THE Frontend SHALL call POST /api/portfolio/positions with transaction details
6. WHEN User submits position form with invalid data, THE Frontend SHALL display validation errors inline
7. WHEN displaying existing position, THE Frontend SHALL show "Edit" and "Delete" buttons
8. WHEN User clicks "Edit" button, THE Frontend SHALL display inline form pre-filled with current transaction values
9. WHEN User clicks "Delete" button, THE Frontend SHALL show confirmation dialog "Delete this position?" before calling DELETE endpoint
10. WHEN position is successfully added/updated/deleted, THE Frontend SHALL refresh the strategy subsection to show updated data

### Requirement 20: Massive API Integration

**User Story:** As a developer, I want a service layer that integrates with Massive API (Polygon.io), so that the system can fetch stock and options data from the external provider.

#### Acceptance Criteria

1. WHEN System initializes, THE System SHALL create RESTClient instance with MASSIVE_TOKEN from environment
2. WHEN fetching daily stock bars, THE System SHALL call client.get_aggs() with ticker, timespan="day", and date range
3. WHEN fetching options chain snapshot, THE System SHALL call client.get_snapshot_option_chain() with underlying ticker
4. WHEN fetching single option contract snapshot, THE System SHALL call client.get_snapshot_option() with underlying ticker and option ticker
5. WHEN Massive_API returns data, THE System SHALL parse response attributes including greeks, implied_volatility, and day metrics
6. WHEN Massive_API returns error response, THE System SHALL log the error and raise appropriate exception
7. WHEN Massive_API request times out, THE System SHALL retry up to 3 times with exponential backoff (1s, 2s, 4s)
8. WHEN all retries fail, THE System SHALL raise exception and return cached data if available
9. WHEN Massive_API rate limit is reached, THE System SHALL wait for specified delay and retry
10. WHEN generating option tickers, THE System SHALL use generate_option_ticker() utility with symbol, expiration, option_type, and strike

### Requirement 21: Error Handling and Logging

**User Story:** As a system administrator, I want comprehensive error handling and logging, so that I can troubleshoot issues and ensure system reliability.

#### Acceptance Criteria

1. WHEN any API endpoint encounters an error, THE Backend SHALL return appropriate HTTP status code and error message
2. WHEN Massive_API request fails, THE System SHALL log the error with request details and response status using AppContext logger
3. WHEN Redis operation fails, THE System SHALL log the error with operation type and affected data
4. WHEN calculation produces invalid result, THE System SHALL log a warning and use fallback value
5. WHEN User submits invalid data, THE Backend SHALL return 400 error with specific validation messages
6. WHEN requested resource is not found, THE Backend SHALL return 404 error with descriptive message
7. WHEN internal server error occurs, THE Backend SHALL return 500 error and log full stack trace
8. WHEN logging errors, THE System SHALL include timestamp, severity level, component name, and context data

### Requirement 22: API Authentication and Authorization

**User Story:** As a system administrator, I want dashboard endpoints to be publicly accessible while portfolio endpoints require authentication, so that the finance dashboard can be viewed easily but positions are protected.

#### Acceptance Criteria

1. WHEN /api/dashboard endpoint is called, THE Backend SHALL allow access without authentication token
2. WHEN /api/portfolio/positions endpoint is called with GET method, THE Backend SHALL require authentication token
3. WHEN /api/portfolio/positions endpoint is called with POST/PUT/DELETE methods, THE Backend SHALL require authentication token
4. WHEN portfolio endpoint is called without authentication token, THE Backend SHALL return 401 error
5. WHEN portfolio endpoint is called with valid token, THE Backend SHALL extract User identity from token
6. WHEN portfolio endpoint is called with invalid token, THE Backend SHALL return 401 error with descriptive message

### Requirement 23: Configuration Management

**User Story:** As a system administrator, I want all configuration to be managed through environment variables, so that the system can be deployed across different environments without code changes.

#### Acceptance Criteria

1. WHEN System starts, THE Backend SHALL load MASSIVE_TOKEN from environment variables
2. WHEN System starts, THE Backend SHALL load Redis connection details from environment variables
3. WHEN System starts, THE Backend SHALL load JWT secret key from environment variables (for portfolio auth)
4. WHEN required environment variable is missing, THE System SHALL log error and fail to start
5. WHEN environment variable has invalid format, THE System SHALL log error and fail to start
6. WHEN STAGE environment variable is set to DEV, THE System SHALL use development-specific settings
7. WHEN STAGE environment variable is set to PROD, THE System SHALL use production-specific settings

### Requirement 24: Position Management Recommendations

**User Story:** As a user, I want specific recommendations for each of my positions on whether to maintain, close, or roll forward, so that I can make informed decisions about position management.

#### Acceptance Criteria

1. WHEN User has a LEAPS position, THE System SHALL evaluate maintain conditions: delta ≥0.70, ≥6-9 months to expiration, IV not extremely elevated, thesis intact
2. WHEN User has a LEAPS position, THE System SHALL evaluate close conditions: ≤3-4 months to expiration, delta <0.60, major thesis break, IV collapse after hype event
3. WHEN User has a LEAPS position with 6 months remaining or delta <0.65, THE System SHALL recommend rolling to later expiration
4. WHEN User has a short call position, THE System SHALL evaluate maintain conditions: 30-45 DTE, delta 0.20-0.30, IV rank above baseline, underlying range-bound or grinding up slowly
5. WHEN User has a short call position, THE System SHALL evaluate close conditions: 50-70% of max profit reached, IV collapse, within 21 DTE, strong upward trend
6. WHEN User has a short call position with price staying below strike, THE System SHALL recommend rolling down & out for more premium
7. WHEN User has a short call position with price approaching strike fast, THE System SHALL recommend rolling out in time at same strike
8. WHEN User has a short call position with strong bullish breakout, THE System SHALL recommend rolling up & out to higher strike
9. WHEN User has a short put position, THE System SHALL evaluate maintain conditions: 30-45 DTE, delta 0.20-0.30, happy to own shares at strike, IV elevated
10. WHEN User has a short put position, THE System SHALL evaluate close conditions: 50-70% max profit reached, IV crush, before earnings
11. WHEN User has a short put position with stock staying above strike, THE System SHALL recommend rolling down or closing to lock gains
12. WHEN User has a short put position with price near strike and neutral outlook, THE System SHALL recommend rolling out at same strike for more premium
13. WHEN User has a short put position with price dropping hard, THE System SHALL recommend rolling down & out while maintaining net credit
14. WHEN generating position recommendations, THE System SHALL include action (maintain/close/roll), reasoning bullets, and specific roll parameters if applicable
15. WHEN generating roll recommendations, THE System SHALL specify new strike, new expiration, and expected credit/debit
16. WHEN User has PMCC with short call strike at or below LEAPS strike, THE System SHALL flag as invalid structure and recommend adjustment
17. WHEN earnings are within 7 days and User has short options, THE System SHALL recommend closing or widening positions
18. WHEN IV percentile is high (>70), THE System SHALL recommend selling more short options
19. WHEN IV percentile is low (<30), THE System SHALL recommend reducing short options and letting LEAPS work
20. WHEN position has reached 60% profit, THE System SHALL recommend closing early to lock gains

### Requirement 25: Position Recommendation UI

**User Story:** As a user, I want to see position management recommendations displayed prominently for each position, so that I can quickly understand what action to take.

#### Acceptance Criteria

1. WHEN User has a position, THE Frontend SHALL display a recommendation card with action badge (MAINTAIN/CLOSE/ROLL)
2. WHEN recommendation is MAINTAIN, THE Frontend SHALL display green badge and reasoning bullets
3. WHEN recommendation is CLOSE, THE Frontend SHALL display yellow badge, reasoning bullets, and "Close Position" button
4. WHEN recommendation is ROLL, THE Frontend SHALL display blue badge, reasoning bullets, and roll parameters (new strike, new expiration, credit/debit)
5. WHEN recommendation is ROLL, THE Frontend SHALL display "Roll Position" button that pre-fills position form with suggested parameters
6. WHEN displaying roll recommendation, THE Frontend SHALL show comparison: current position vs suggested rolled position
7. WHEN User clicks "Roll Position", THE Frontend SHALL open position form with current position pre-filled and suggested changes highlighted
8. WHEN position has multiple recommendation factors, THE Frontend SHALL prioritize most urgent recommendation (close > roll > maintain)
9. WHEN position recommendation changes, THE Frontend SHALL highlight the change with animation or badge
10. WHEN User hovers over recommendation reasoning, THE Frontend SHALL show tooltip with detailed explanation and thresholds
