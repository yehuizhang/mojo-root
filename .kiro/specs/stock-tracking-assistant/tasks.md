# Implementation Plan: Stock Tracking Assistant

## Overview

This plan implements a real-time stock tracking and options trading assistant system with three strategies (LEAPS, PMCC, Wheel). The implementation follows mojo-api patterns with Handler + DAO injection, integrates with Massive API (Polygon.io), and provides a mobile-friendly Next.js frontend.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Add `massive` Python package to mojo-api dependencies
  - Create directory structure for handlers, DAOs, factories, and services
  - Add MASSIVE_TOKEN to environment configuration
  - _Requirements: 20, 24_

- [x] 2. Implement data models
  - [x] 2.1 Create Pydantic models for stock data, signals, and positions
    - Define `StockData`, `MovingAverages`, `Greeks`, `OptionContract` models
    - Define signal models: `CSPSignal`, `CoveredCallSignal`, `LEAPSSignal`, `PMCCSignal`
    - Define position models: `PositionCreate`, `Position`, `PositionMetrics`
    - Define dashboard models: `StrategyData`, `StockDashboardData`, `DashboardResponse`
    - _Requirements: 1, 2, 5, 6, 7, 8, 9_

- [x] 3. Implement Massive API client
  - [x] 3.1 Create MassiveAPIClient wrapper
    - Initialize RESTClient with API token from environment
    - Implement `get_daily_bars()` for OHLCV data
    - Implement `get_options_chain_snapshot()` for options data
    - Implement `get_option_contract_snapshot()` for single contract
    - Add retry logic with exponential backoff (3 retries, 1s/2s/4s delays)
    - _Requirements: 1, 2, 24_

- [x] 4. Implement FinanceDAO
  - [x] 4.1 Create FinanceDAO with Redis operations
    - Implement watchlist methods: `get_watchlist()`, `add_to_watchlist()`, `remove_from_watchlist()`, `ticker_in_watchlist()`
    - Implement position methods: `get_all_positions()`, `get_positions_for_ticker()`, `save_position()`, `update_position()`, `delete_position()`
    - Implement cache methods: `get_cached_stock_data()`, `cache_stock_data()`, `get_cached_options_data()`, `cache_options_data()`
    - Use Redis keys: `finance:watchlist`, `finance:position:{id}`, `finance:positions:index`, `finance:cache:stock:{ticker}`, `finance:cache:options:{ticker}`
    - _Requirements: 9, 10, 21_

- [x] 5. Implement technical analysis service
  - [x] 5.1 Create TechnicalAnalysisService
    - Implement `calculate_moving_averages()` for 20/50/200 DMA
    - Implement `calculate_rsi()` for 14-day RSI
    - Implement `calculate_volatility()` for 20-day historical volatility
    - Implement `calculate_atr()` for Average True Range
    - Implement `identify_support_resistance()` for support/resistance levels
    - Implement `identify_swing_points()` for swing high/low
    - _Requirements: 1, 4_

- [x] 6. Implement market data service
  - [x] 6.1 Create MarketDataService
    - Implement `get_stock_data()` - fetch OHLCV, calculate indicators, check cache
    - Implement `get_options_chain()` - fetch options with Greeks, calculate IV metrics
    - Implement `get_current_price()` - get latest price for position valuation
    - Implement `validate_ticker()` - verify ticker exists in Massive API
    - Implement `get_earnings_date()` - fetch next earnings date
    - Integrate with FinanceDAO for caching (5 min for stock, 15 min for options)
    - _Requirements: 1, 2, 3_

- [x] 7. Implement signal generator service
  - [x] 7.1 Create SignalGeneratorService for CSP signals
    - Check conditions: price 5-15% below swing high, RSI 40-55, IV percentile >50, no earnings in 7-10 days
    - Assign score: Green (4 conditions), Yellow (2-3), Red (0-1)
    - Find recommended put strikes with delta 0.20-0.30, DTE 21-45
    - Calculate premium, break-even, return on capital
    - _Requirements: 5_
  
  - [x] 7.2 Create SignalGeneratorService for covered call signals
    - Check conditions: price > 20 DMA, RSI >60, near resistance, IV percentile >40, no earnings in 7-10 days
    - Assign score: Green (5 conditions), Yellow (3-4), Red (0-2)
    - Find recommended call strikes with delta 0.20-0.30, DTE 14-30, above cost basis
    - Calculate premium, effective sale price, annualized return
    - _Requirements: 6_
  
  - [x] 7.3 Create SignalGeneratorService for LEAPS signals
    - Check conditions: price 10-25% below 52w high, IV percentile <50, price > 200 DMA, 50 DMA > 200 DMA
    - Assign score: Green (4 conditions), Yellow (2-3), Red (0-1)
    - Find recommended LEAPS calls with delta 0.70-0.85, DTE 18-30 months
    - Calculate cost, break-even, leverage ratio, extrinsic value
    - _Requirements: 7_
  
  - [x] 7.4 Create SignalGeneratorService for PMCC signals
    - Check if LEAPS position exists, calculate days to expiration and extrinsic value
    - Check short call conditions: price > 20 DMA, RSI >60, IV percentile >40
    - Assign score: Green (3 conditions), Yellow (2), Red (0-1)
    - Find recommended short calls with delta 0.20-0.30, DTE 14-45, strike above LEAPS strike
    - Flag LEAPS for rolling if <90 days to expiration
    - _Requirements: 8_
  
  - [x] 7.5 Implement `generate_all_signals()` orchestration method
    - Call all signal generation methods
    - Return combined signals object
    - _Requirements: 5, 6, 7, 8_

- [x] 8. Implement FinanceHandler
  - [x] 8.1 Create FinanceHandler with business logic
    - Implement `get_dashboard()` - fetch watchlist, get data for each ticker, generate signals, get positions
    - Implement `get_watchlist()` - return ticker list
    - Implement `add_ticker()` - validate ticker, check duplicates, add to watchlist
    - Implement `remove_ticker()` - remove from watchlist and clear cache
    - Implement `get_positions()` - return all positions
    - Implement `add_position()` - validate, auto-add to watchlist, save, calculate metrics
    - Implement `update_position()` - update existing position
    - Implement `delete_position()` - remove position
    - Implement `_calculate_position_metrics()` helper for P&L calculations
    - _Requirements: 10, 11, 12, 13_

- [x] 9. Implement dependency injection factories
  - [x] 9.1 Create dao_factory.py
    - Implement `get_redis_client()` factory
    - Implement `get_finance_dao()` factory with Redis injection
    - _Requirements: Architecture_
  
  - [x] 9.2 Create handler_factory.py
    - Implement `get_market_data_service()` factory
    - Implement `get_signal_generator_service()` factory
    - Implement `get_finance_handler()` factory with all dependencies injected
    - _Requirements: Architecture_

- [x] 10. Implement API routers
  - [x] 10.1 Create public finance router
    - Create `api/routers/finance_router.py` with prefix `/finance`
    - Implement GET `/dashboard` endpoint
    - Implement GET `/watchlist` endpoint
    - Implement POST `/watchlist` endpoint
    - Implement DELETE `/watchlist/{ticker}` endpoint
    - All endpoints use `Depends(get_finance_handler)`
    - _Requirements: 11, 12_
  
  - [x] 10.2 Create protected finance router
    - Create `api/routers/internal/finance_router.py`
    - Implement GET `/portfolio/positions` endpoint
    - Implement POST `/portfolio/positions` endpoint
    - Implement PUT `/portfolio/positions/{id}` endpoint
    - Implement DELETE `/portfolio/positions/{id}` endpoint
    - All endpoints use `Depends(get_finance_handler)` and require auth
    - _Requirements: 13_

- [x] 11. Initialize default watchlist
  - [x] 11.1 Create initialization script or startup hook
    - Check if `finance:watchlist` exists in Redis
    - If empty, add GOOGL and NVDA as default tickers
    - _Requirements: 9_

- [x] 12. Implement error handling
  - [x] 12.1 Add error handling to handlers
    - Wrap Massive API calls with try/except, return cached data on failure
    - Handle validation errors with 400 responses
    - Handle not found errors with 404 responses
    - Log all errors with context using AppContext logger
    - _Requirements: 21_

- [x] 13. Test backend implementation
  - [x] 13.1 Write unit tests for technical analysis
    - Test RSI calculation
    - Test moving average calculation
    - Test support/resistance identification
    - _Requirements: 4_
  
  - [x] 13.2 Write unit tests for signal generation
    - Test CSP signal scoring logic
    - Test covered call signal scoring logic
    - Test LEAPS signal scoring logic
    - Test PMCC signal scoring logic
    - _Requirements: 5, 6, 7, 8_
  
  - [x] 13.3 Write unit tests for DAO operations
    - Test watchlist CRUD operations
    - Test position CRUD operations
    - Test cache operations
    - _Requirements: 9, 10_
  
  - [x] 13.4 Write integration tests
    - Test complete dashboard flow with mocked Massive API
    - Test position lifecycle (create, update, delete)
    - Test watchlist management flow
    - _Requirements: 11, 12, 13_

- [x] 14. Implement Next.js frontend page
  - [x] 14.1 Create dashboard page component
    - Create `app/zyh/finance/page.tsx`
    - Fetch dashboard data from `/finance/dashboard`
    - Render DashboardHeader with auto-refresh controls
    - Render StockSection for each ticker in watchlist
    - Handle loading and error states
    - _Requirements: 14_

- [x] 15. Implement dashboard header component
  - [x] 15.1 Create DashboardHeader component
    - Add "Auto Refresh" toggle button (off by default)
    - Add refresh period dropdown (5s, 15s, 30s, 1m, 5m, 10m, 30m)
    - Add "Add Ticker" button
    - Implement auto-refresh logic with setInterval
    - _Requirements: 14, 15_

- [x] 16. Implement stock section component
  - [x] 16.1 Create StockSection component
    - Display stock header with ticker, price, daily change, trend badge
    - Display earnings countdown and IV percentile badge
    - Display position summary if exists
    - Render three strategy subsections (LEAPS, PMCC, Wheel)
    - Add remove ticker button in header
    - _Requirements: 14_

- [x] 17. Implement strategy subsection components
  - [x] 17.1 Create LEAPSSubsection component
    - Show "No Position" badge if no LEAPS
    - Show signal score with color-coded indicator
    - Show reasoning bullets
    - Show recommended strikes table if Green/Yellow
    - Show position details if LEAPS exists (strike, expiration, P&L, delta, extrinsic value)
    - Show warning badge if <90 days to expiration
    - _Requirements: 16_
  
  - [x] 17.2 Create PMCCSubsection component
    - Show "Requires LEAPS Position" if no LEAPS
    - Show "LEAPS Established - Ready for Short Calls" if LEAPS but no short call
    - Show short call signal score and reasoning
    - Show recommended short call strikes table
    - Show active short call position details if exists
    - Show warning if short call strike <= LEAPS strike
    - _Requirements: 17_
  
  - [x] 17.3 Create WheelSubsection component
    - Show "No Stock Position - CSP Entry Phase" if no stock
    - Show CSP signal score, reasoning, and recommended strikes
    - Show stock position details if exists
    - Show covered call signal score, reasoning, and recommended strikes
    - Show active covered call position details if exists
    - _Requirements: 18_

- [x] 18. Implement shared UI components
  - [x] 18.1 Create SignalCard component
    - Display signal score badge (Green/Yellow/Red) with appropriate colors
    - Display reasoning bullets
    - _Requirements: 16, 17, 18_
  
  - [x] 18.2 Create OptionsTable component
    - Display table with columns: Strike, Exp, DTE, Premium, Delta, Additional metrics
    - Make rows clickable to show more details
    - _Requirements: 16, 17, 18_
  
  - [x] 18.3 Create PositionForm component
    - Show "Stock or Option?" radio buttons
    - Show appropriate input fields based on selection
    - Validate inputs before submission
    - Call POST `/portfolio/positions` on submit
    - _Requirements: 19_

- [x] 19. Implement watchlist management UI
  - [x] 19.1 Add ticker modal/form
    - Show modal when "Add Ticker" clicked
    - Input field for ticker symbol
    - Call POST `/finance/watchlist` on submit
    - Refresh dashboard on success
    - Show error message on failure
    - _Requirements: 15_
  
  - [x] 19.2 Remove ticker functionality
    - Add remove button (X) in stock section header
    - Show confirmation dialog
    - Call DELETE `/finance/watchlist/{ticker}` on confirm
    - Remove section from UI on success
    - _Requirements: 15_

- [x] 20. Implement mobile responsive design
  - [x] 20.1 Add responsive styles
    - Use Tailwind breakpoints for mobile (390px width)
    - Stack components vertically on mobile
    - Use touch-friendly button sizes (min 44px)
    - Collapse tables to show top 3 strikes with "View All" button
    - _Requirements: 14_

- [x] 21. Add API client functions
  - [x] 21.1 Create stock-tracking.ts API client
    - Implement `fetchDashboard()` function
    - Implement `getWatchlist()` function
    - Implement `addTicker()` function
    - Implement `removeTicker()` function
    - Implement `getPositions()` function
    - Implement `addPosition()` function
    - Implement `updatePosition()` function
    - Implement `deletePosition()` function
    - Add error handling and retry logic
    - _Requirements: 11, 12, 13_

- [x] 22. Test frontend implementation
  - [x] 22.1 Write component tests
    - Test StockSection rendering
    - Test SignalCard with different scores
    - Test OptionsTable display
    - Test PositionForm validation
    - Test auto-refresh functionality
    - _Requirements: 14, 15, 16, 17, 18, 19_

- [x] 23. Integration and deployment
  - [x] 23.1 Configure environment variables
    - Add MASSIVE_TOKEN to mojo-api/.env
    - Verify Redis connection settings
    - _Requirements: 20_
  
  - [x] 23.2 Test end-to-end flow
    - Start Redis infrastructure
    - Start mojo-api backend
    - Start mojo-next frontend
    - Test complete user flow: add ticker, view signals, add position
    - Verify auto-refresh works
    - Test on mobile device (iPhone 15)
    - _Requirements: All_
  
  - [x] 23.3 Deploy to production
    - Run `bb up` in mojo-api
    - Build and start mojo-next
    - Verify `/zyh/finance` page loads
    - Verify API endpoints respond correctly
    - _Requirements: All_

- [x] 24. Implement position recommendation service
  - [x] 24.1 Create PositionRecommendationService
    - Implement `generate_position_recommendation()` - main entry point that routes to specific evaluators
    - Implement `evaluate_leaps_recommendation()` - check delta ≥0.70, DTE ≥6-9 months, IV not elevated, thesis intact
    - Implement `evaluate_short_call_recommendation()` - check profit ≥60%, DTE, price vs strike, IV conditions
    - Implement `evaluate_short_put_recommendation()` - check profit ≥60%, price vs strike, willingness to own
    - Implement `calculate_roll_parameters()` - find optimal new strike and expiration based on roll type
    - _Requirements: 24_
  
  - [x] 24.2 Add position recommendation models
    - Create `RecommendationAction` enum (MAINTAIN, CLOSE, ROLL)
    - Create `RollParameters` model with new_strike, new_expiration, expected_credit, roll_type
    - Create `PositionRecommendation` model with action, reasoning, priority, roll_parameters
    - Update `StrategyData` model to include recommendation fields for each position type
    - _Requirements: 24_
  
  - [x] 24.3 Implement LEAPS recommendation logic
    - Check maintain conditions: delta ≥0.70, DTE ≥180 days, IV not extremely elevated
    - Check close conditions: DTE ≤90 days, delta <0.60, IV collapse, thesis break
    - Check roll conditions: DTE 120-180 days, delta <0.65
    - Generate roll parameters: same strike, later expiration (extend by 12-18 months)
    - Return recommendation with action, reasoning bullets, and roll parameters if applicable
    - _Requirements: 24.1, 24.2, 24.3_
  
  - [x] 24.4 Implement short call recommendation logic
    - Check close conditions: profit ≥60%, DTE <21, IV collapse, strong upward move
    - Check maintain conditions: 30-45 DTE, delta 0.20-0.30, IV elevated, range-bound price
    - Determine roll type based on price action: down & out (below strike), out (approaching), up & out (breakout)
    - Generate roll parameters: calculate new strike, new expiration (30-60 days out), expected credit
    - Validate PMCC structure: ensure short call strike > LEAPS strike
    - _Requirements: 24.4, 24.5, 24.6, 24.7, 24.8, 24.16_
  
  - [x] 24.5 Implement short put recommendation logic
    - Check close conditions: profit ≥60%, IV crush, earnings within 7 days
    - Check maintain conditions: 30-45 DTE, delta 0.20-0.30, happy to own shares, IV elevated
    - Determine roll type: down or close (above strike), out (near strike), down & out (dropping)
    - Generate roll parameters: calculate new strike, new expiration, maintain net credit
    - _Requirements: 24.9, 24.10, 24.11, 24.12, 24.13_
  
  - [x] 24.6 Implement system-level recommendation rules
    - Check earnings proximity: recommend closing/widening short options if earnings within 7 days
    - Check IV regime: recommend selling more shorts if IV >70, reducing shorts if IV <30
    - Check profit threshold: recommend closing at 60% profit for all short options
    - Prioritize recommendations: close > roll > maintain
    - _Requirements: 24.14, 24.17, 24.18, 24.19, 24.20_

- [x] 25. Integrate recommendations into dashboard
  - [x] 25.1 Update FinanceHandler to generate recommendations
    - Call `position_recommendation_service.generate_position_recommendation()` for each position
    - Include recommendations in dashboard response alongside positions
    - Handle cases where recommendation cannot be generated (missing data)
    - _Requirements: 24_
  
  - [x] 25.2 Update API response models
    - Add recommendation fields to `StrategyData` model
    - Ensure recommendations are serialized correctly in dashboard response
    - _Requirements: 24_

- [x] 26. Implement recommendation UI components
  - [x] 26.1 Create RecommendationCard component
    - Display action badge (MAINTAIN=green, CLOSE=yellow, ROLL=blue)
    - Display reasoning bullets
    - Show priority indicator (urgent/moderate/low)
    - Add timestamp of recommendation
    - _Requirements: 25.1, 25.2_
  
  - [x] 26.2 Add roll parameters display
    - Show current position details (strike, expiration, DTE)
    - Show suggested rolled position (new strike, new expiration, new DTE)
    - Display expected credit/debit
    - Show roll type label (e.g., "Roll Down & Out")
    - Add comparison view: current vs suggested
    - _Requirements: 25.3, 25.4, 25.6_
  
  - [x] 26.3 Add action buttons to recommendations
    - Add "Close Position" button for CLOSE recommendations
    - Add "Roll Position" button for ROLL recommendations
    - Add "Keep Position" button for MAINTAIN recommendations (informational)
    - Wire buttons to appropriate actions
    - _Requirements: 25.3, 25.4_
  
  - [x] 26.4 Implement roll position workflow
    - When "Roll Position" clicked, open position form
    - Pre-fill form with current position details
    - Highlight suggested changes (new strike, new expiration)
    - Show expected credit/debit calculation
    - Allow user to adjust suggested parameters
    - Submit as new position (system will handle closing old position)
    - _Requirements: 25.5, 25.7_
  
  - [x] 26.5 Add recommendation tooltips and help text
    - Add hover tooltips explaining each reasoning bullet
    - Show detailed thresholds (e.g., "Delta: 0.65 (threshold: 0.70)")
    - Add help icon with explanation of recommendation system
    - Display recommendation change notifications
    - _Requirements: 25.8, 25.9, 25.10_

- [x] 27. Test position recommendation system
  - [x] 27.1 Write unit tests for recommendation logic
    - Test LEAPS recommendation with various delta/DTE combinations
    - Test short call recommendation with different profit levels and price movements
    - Test short put recommendation with different scenarios
    - Test roll parameter calculations
    - Test priority assignment
    - _Requirements: 24_
  
  - [x] 27.2 Write integration tests
    - Test complete dashboard flow with positions and recommendations
    - Test recommendation updates when market data changes
    - Test roll workflow end-to-end
    - _Requirements: 24, 25_
  
  - [x] 27.3 Write frontend component tests
    - Test RecommendationCard rendering with different actions
    - Test roll parameters display
    - Test action button interactions
    - Test tooltip functionality
    - _Requirements: 25_

## Notes

- Follow mojo-api Handler + DAO injection pattern throughout
- Use `build_context()` for logging in all services
- Keep routers thin - all logic in handlers
- Cache aggressively (5 min for stock data, 15 min for options)
- Positions and watchlist persist indefinitely (no TTL)
- All frontend components should handle loading and error states gracefully
- Mobile-first design with responsive breakpoints
- Position recommendations should be calculated in real-time based on current market data
- Recommendations should be clear, actionable, and include specific parameters for rolls
