# Stock Tracking Assistant

## Overview

The Stock Tracking Assistant is a real-time options trading analysis system that helps track positions and identify optimal timing for three strategies: LEAPS (long-term growth), PMCC (Poor Man's Covered Call), and the Wheel strategy (cash-secured puts and covered calls). The system integrates with mojo-api (FastAPI backend) and mojo-next (Next.js frontend), fetching real-time data from Massive API (Polygon.io) with Redis caching.

## Key Concepts

### Trading Strategies

1. **LEAPS (Long-term Equity Anticipation Securities)**
   - Long-term call options (18-30 months expiration)
   - Delta 0.70-0.85 for leveraged stock exposure
   - Entry when price is 10-25% below 52-week high and IV is low

2. **PMCC (Poor Man's Covered Call)**
   - Buy deep ITM LEAPS call (long position)
   - Sell short-term OTM calls against it (short position)
   - Generates income with defined risk and lower capital requirement than owning stock

3. **Wheel Strategy**
   - **Phase 1 - Cash-Secured Puts (CSP)**: Sell puts to acquire stock at discount
   - **Phase 2 - Covered Calls**: Once assigned stock, sell calls for income
   - Continuous income generation strategy

### Signal Scoring

- **🟢 GREEN**: Strong signal - all or most conditions met, favorable for trade
- **🟡 YELLOW**: Moderate signal - some conditions met, proceed with caution
- **🔴 RED**: Weak signal - unfavorable conditions, avoid trade

### Position Quantity Convention

- **Positive quantity** = Long position (bought)
- **Negative quantity** = Short position (sold)
- Simplifies P&L calculations: `unrealized_pnl = current_value - cost`

## Architecture

### Backend Structure (mojo-api)

```
api/
├── routers/
│   ├── finance_router.py              # Public endpoints (watchlist, dashboard)
│   └── internal/
│       └── finance_router.py          # Protected endpoints (positions)
├── handlers/
│   └── finance_handler.py             # Business logic orchestration
├── dao/
│   └── finance_dao.py                 # Redis data access
├── factories/
│   ├── dao_factory.py                 # DAO dependency injection
│   └── handler_factory.py             # Handler dependency injection
└── lib/
    └── stock_tracking/
        ├── massive_client.py          # Massive API wrapper
        ├── models/                    # Pydantic models
        │   ├── stock_models.py
        │   ├── position_models.py
        │   └── dashboard_models.py
        └── services/
            ├── market_data_service.py         # Fetch & cache market data
            ├── technical_analysis_service.py  # Calculate indicators
            └── signal_generator_service.py    # Generate trading signals
```

### Frontend Structure (mojo-next)

```
app/zyh/finance/
└── page.tsx                           # Main dashboard page

components/finance/
├── DashboardHeader.tsx                # Auto-refresh controls, add ticker
├── StockSection.tsx                   # Container for each ticker
├── AddPositionModal.tsx               # Add/edit position form
└── PositionCard.tsx                   # Display position details

lib/api/
└── stock-tracking.ts                  # API client functions
```

## Data Flow

### Dashboard Load

1. Frontend calls `GET /finance/dashboard`
2. Backend retrieves watchlist from Redis
3. For each ticker:
   - Check Redis cache (5 min for stock, 15 min for options)
   - If cache miss, fetch from Massive API
   - Calculate technical indicators
   - Generate trading signals
   - Retrieve user positions
   - Calculate position metrics
4. Return complete dashboard data

### Position Management

1. User adds position via modal (with defaults based on strategy)
2. Frontend calls `POST /finance/positions` with signed quantity
3. Backend validates ticker and saves to Redis (no expiration)
4. If ticker not in watchlist, automatically add it
5. Calculate current metrics using latest market data
6. Return position with metrics to frontend

## Redis Keys

```
finance:watchlist                      # Set of ticker symbols
finance:position:{id}                  # Individual position data
finance:positions:index                # Set of position IDs
finance:cache:stock:{ticker}           # Cached stock data (5 min TTL)
finance:cache:options:{ticker}         # Cached options data (15 min TTL)
finance:cache:option_price:{ticker}    # Cached option price (dynamic TTL)
finance:last_refresh                   # Last refresh timestamp
```

## API Endpoints

### Public Endpoints (No Auth)

- `GET /finance/dashboard` - Get complete dashboard data for all watchlist tickers
- `GET /finance/watchlist` - Get list of tickers in watchlist
- `POST /finance/watchlist` - Add ticker to watchlist
- `DELETE /finance/watchlist/{ticker}` - Remove ticker from watchlist

### Protected Endpoints (Auth Required)

- `GET /finance/positions` - Get all user positions
- `POST /finance/positions` - Add new position
- `PUT /finance/positions/{id}` - Update existing position
- `DELETE /finance/positions/{id}` - Delete position

## Signal Generation Logic

### Cash-Secured Puts (CSP)

**Conditions:**
1. Price 5-15% below recent swing high
2. RSI between 40-55
3. IV Percentile > 50
4. No earnings within 7-10 days

**Scoring:**
- 🟢 GREEN: 4 conditions met
- 🟡 YELLOW: 2-3 conditions met
- 🔴 RED: 0-1 conditions met

**Recommendations:**
- Put strikes with delta 0.20-0.30
- DTE 21-45 days
- Include premium, break-even, ROC

### Covered Calls

**Conditions:**
1. Price above 20-day moving average
2. RSI > 60
3. Price within 3% of resistance level
4. IV Percentile > 40
5. No earnings within 7-10 days

**Scoring:**
- 🟢 GREEN: 5 conditions met
- 🟡 YELLOW: 3-4 conditions met
- 🔴 RED: 0-2 conditions met

**Recommendations:**
- Call strikes with delta 0.20-0.30
- DTE 14-30 days
- Only strikes above user's cost basis
- Include premium, effective sale price, annualized return

### LEAPS

**Conditions:**
1. Price 10-25% below 52-week high
2. IV Percentile < 50 (or within 5 days post-earnings)
3. Price above 200-day moving average
4. 50-day MA > 200-day MA (golden cross)

**Scoring:**
- 🟢 GREEN: 4 conditions met
- 🟡 YELLOW: 2-3 conditions met
- 🔴 RED: 0-1 conditions met

**Recommendations:**
- Call strikes with delta 0.70-0.85
- DTE 18-30 months
- Include cost, break-even, leverage ratio, extrinsic value

### PMCC (Poor Man's Covered Call)

**Prerequisites:**
- Must have existing LEAPS position

**Short Call Conditions:**
1. Price above 20-day moving average
2. RSI > 60
3. IV Percentile > 40

**Scoring:**
- 🟢 GREEN: 3 conditions met
- 🟡 YELLOW: 2 conditions met
- 🔴 RED: 0-1 conditions met

**Recommendations:**
- Call strikes with delta 0.20-0.30
- DTE 14-45 days
- Only strikes above LEAPS strike price
- Flag LEAPS for rolling if < 90 days to expiration

## UI Organization

### Dashboard Structure

```
┌─────────────────────────────────────────────────────────┐
│ Dashboard Header                                         │
│ - Auto Refresh toggle & period selector                 │
│ - Force Refresh button                                  │
│ - Last refresh timestamp                                │
│ - + Position button (defaults to Stock)                 │
├─────────────────────────────────────────────────────────┤
│ 📊 Stock Positions (if any)                             │
│ - Display all stock holdings                            │
│ - + Position button (defaults to Stock)                 │
├─────────────────────────────────────────────────────────┤
│ 📈 LEAPS Strategy                                       │
│ - Current long call positions (sorted by strike)        │
│ - + Position button (defaults to Call, Buy)             │
│ - Signal score & reasoning                              │
│ - Recommended strikes table                             │
├─────────────────────────────────────────────────────────┤
│ 🔻 Cash-Secured Puts                                    │
│ - Current short put positions (sorted by strike)        │
│ - + Position button (defaults to Put, Sell)             │
│ - Signal score & reasoning                              │
│ - Recommended strikes table                             │
├─────────────────────────────────────────────────────────┤
│ 🔺 Covered Calls                                        │
│ - Current short call positions (sorted by strike)       │
│ - + Position button (defaults to Call, Sell)            │
│ - Signal score & reasoning                              │
│ - Recommended strikes table                             │
└─────────────────────────────────────────────────────────┘
```

### Position Modal Defaults

- **Top-level button**: Stock type
- **Stock Positions section**: Stock type
- **LEAPS Strategy**: Option type = Call, Side = Buy (Long)
- **Cash-Secured Puts**: Option type = Put, Side = Sell (Short)
- **Covered Calls**: Option type = Call, Side = Sell (Short)

## Market Hours & Caching

### Dynamic TTL Based on Market Hours

- **During market hours** (9:30 AM - 4:00 PM ET, Mon-Fri): 10 minutes
- **Outside market hours**: 1 hour
- **If market opens in < 1 hour**: Time until market open

### Cache Keys & TTL

- Stock data: Dynamic TTL (10 min - 1 hour)
- Options data: Dynamic TTL (10 min - 1 hour)
- Individual option prices: Dynamic TTL
- Positions: No expiration (persist until deleted)
- Watchlist: No expiration (persist until removed)

## Common Patterns

### Adding a New Strategy

1. Create signal model in `stock_models.py`
2. Add signal generation method in `signal_generator_service.py`
3. Update `StrategyData` model to include new signal
4. Add UI subsection component in frontend
5. Update `StockSection.tsx` to render new subsection

### Adding a New Technical Indicator

1. Add calculation method in `technical_analysis_service.py`
2. Update `StockData` model to include new indicator
3. Use indicator in signal generation logic
4. Display in UI if needed

### Modifying Position Model

When changing position models, update:
1. `PositionCreate` and `Position` models
2. `FinanceDAO` save/update methods
3. `FinanceHandler` position metrics calculation
4. Frontend `AddPositionModal` form fields
5. Frontend `PositionCard` display

## Testing Guidelines

### Backend Tests

- Unit tests for technical indicators (RSI, MA, volatility)
- Unit tests for signal generation logic
- Unit tests for DAO operations (watchlist, positions, cache)
- Integration tests for complete dashboard flow
- Mock Massive API responses for consistent testing

### Frontend Tests

- Component rendering tests
- Form validation tests
- API client error handling tests
- Auto-refresh functionality tests
- Mobile responsive layout tests

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**: nginx stale connections after container restart
   - Solution: Restart nginx or configure upstream retry

2. **Stale cache data**: Cache not expiring properly
   - Check Redis TTL values
   - Verify market hours detection logic

3. **Incorrect P&L calculations**: Position metrics wrong
   - Verify signed quantity (negative for short)
   - Check option price fetching (use `day.close` fallback)
   - Verify multiplier (100 for options)

4. **Missing positions**: Positions not showing in UI
   - Check position categorization logic (option_type, quantity sign)
   - Verify Redis keys and data structure

5. **Signal not generating**: No recommendations shown
   - Check if all required data is available
   - Verify condition thresholds
   - Check logs for calculation errors

## Development Workflow

### Local Development

```bash
# Start Redis
cd mojo-infra && ./build.sh redis up

# Start FastAPI locally (NOT in Docker)
cd mojo-api && bb dev

# Start Next.js
cd mojo-next && npm run dev
```

### Adding New Features

1. Update requirements and design docs in `.kiro/specs/stock-tracking-assistant/`
2. Implement backend changes following Handler + DAO pattern
3. Add tests for new functionality
4. Implement frontend changes
5. Test end-to-end flow
6. Update this steering file with new patterns

## References

- Spec files: `.kiro/specs/stock-tracking-assistant/`
- Massive API docs: https://polygon.io/docs
- Handler + DAO pattern: `.kiro/steering/mojo-api-patterns.md`
- Redis patterns: `.kiro/steering/mojo-api-patterns.md`
