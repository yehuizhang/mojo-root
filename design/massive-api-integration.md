# Massive API (Polygon.io) Integration

## Overview

This document describes how the mojo-api system interacts with Massive API (Polygon.io) for real-time stock and options market data. It covers all API endpoints used, their use cases, caching strategies, and error handling patterns.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     mojo-api Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐            │
│  │ MarketDataService│────────▶│ MassiveAPIClient │            │
│  │                  │         │                  │            │
│  │ - get_stock_data │         │ - get_daily_bars │            │
│  │ - get_options    │         │ - get_options_   │            │
│  │ - get_option_    │         │   chain_snapshot │            │
│  │   price          │         │ - get_option_    │            │
│  │                  │         │   contract_      │            │
│  │                  │         │   snapshot       │            │
│  └────────┬─────────┘         └────────┬─────────┘            │
│           │                            │                       │
│           │                            │                       │
│           ▼                            ▼                       │
│  ┌──────────────────┐         ┌──────────────────┐            │
│  │   FinanceDAO     │         │   RESTClient     │            │
│  │                  │         │   (massive lib)  │            │
│  │ - Cache methods  │         │                  │            │
│  │ - Redis ops      │         └────────┬─────────┘            │
│  └────────┬─────────┘                  │                      │
│           │                            │                       │
└───────────┼────────────────────────────┼───────────────────────┘
            │                            │
            ▼                            ▼
    ┌──────────────┐           ┌──────────────────┐
    │    Redis     │           │  Polygon.io API  │
    │    Cache     │           │  (Massive API)   │
    └──────────────┘           └──────────────────┘
```

## API Endpoints Used

### 1. Get Daily Aggregate Bars (OHLCV Data)

**Massive API Method:** `client.get_aggs()`

**Purpose:** Fetch historical daily price data for technical analysis

**Use Cases:**
- Calculate moving averages (20/50/200 DMA)
- Identify 52-week high/low
- Calculate RSI, ATR, volatility
- Identify support/resistance levels
- Detect swing highs/lows

**Request Parameters:**
```python
client.get_aggs(
    ticker="GOOGL",           # Stock symbol
    multiplier=1,             # 1 day per bar
    timespan="day",           # Daily bars
    from_="2024-01-01",       # Start date (YYYY-MM-DD)
    to="2025-01-31"           # End date (YYYY-MM-DD)
)
```

**Response Structure:**
```python
[
    Agg(
        open=175.32,
        high=178.45,
        low=174.89,
        close=177.21,
        volume=12345678,
        vwap=176.54,
        timestamp=1706745600000,  # Unix timestamp in milliseconds
        transactions=45678
    ),
    # ... more bars
]
```

**Data Fetched:**
- **Short-term contracts**: 0-60 days expiration (typically 20-50 contracts)
- **Long-term contracts**: 12-30 months expiration, calls only (typically 10-20 contracts)
- **Total**: 30-70 contracts vs 200-500+ without filtering
- **Data reduction**: 70-80% less data transferred and processed

**Caching Strategy:**
```python
# Cache key: finance:cache:stock:{ticker}
# TTL: Dynamic based on market hours
#   - During market hours (9:30 AM - 4:00 PM ET): 10 minutes
#   - Outside market hours: 1 hour
#   - If market opens in < 1 hour: Time until market open

ttl = get_cache_ttl()  # Returns 600-3600 seconds
finance_dao.cache_stock_data(ticker, stock_data, ttl=ttl)
```

**Error Handling:**
- Retry up to 3 times with exponential backoff (1s, 2s, 4s)
- Log all failures with context
- Raise exception if all retries fail
- Return cached data if available on failure

---

### 2. Get Options Chain Snapshot

**Massive API Method:** `client.list_snapshot_options_chain()`

**Purpose:** Fetch option contracts with Greeks and pricing, filtered by expiration dates

**Use Cases:**
- Generate trading signals (LEAPS, CSP, Covered Calls, PMCC)
- Find recommended strikes based on delta
- Calculate IV percentile and IV rank
- Filter contracts by expiration (DTE)

**OPTIMIZATION:** Instead of fetching all contracts (200-500+), we make two targeted API calls:
1. **Short-term options** (0-60 days) - for CSP, Covered Calls, PMCC short calls
2. **Long-term options** (12-30 months) - for LEAPS (calls only)

This reduces data transfer by **70-80%** while getting all contracts needed for signal generation.

**Request Parameters:**
```python
# Short-term options (0-60 days, both calls and puts)
client.list_snapshot_options_chain(
    ticker="GOOGL",
    params={
        "expiration_date.gte": "2025-02-01",  # Today
        "expiration_date.lte": "2025-04-02"   # 60 days from now
    }
)

# Long-term options (12-30 months, calls only for LEAPS)
client.list_snapshot_options_chain(
    ticker="GOOGL",
    params={
        "expiration_date.gte": "2026-02-01",  # 12 months from now
        "expiration_date.lte": "2027-08-01",  # 30 months from now
        "contract_type": "call"
    }
)
```

**Response Structure:**
```python
# Returns a generator of OptionContractSnapshot objects
[
    OptionContractSnapshot(
        details=OptionDetails(
            contract_type="call",           # "call" or "put"
            exercise_style="american",
            expiration_date="2026-02-06",   # YYYY-MM-DD
            shares_per_contract=100,
            strike_price=190.0,
            ticker="O:GOOGL260206C00190000"
        ),
        day=DayData(
            change=0.5,
            change_percent=2.5,
            close=5.0,                      # Last traded price
            high=7.22,
            low=4.25,
            open=5.27,
            previous_close=4.5,
            volume=20184,
            vwap=5.43
        ),
        greeks=Greeks(
            delta=0.5243,
            gamma=0.0333,
            theta=-0.4423,
            vega=0.0943
        ),
        implied_volatility=0.5118,
        last_quote=LastQuote(
            ask=5.2,
            ask_size=100,
            bid=4.8,
            bid_size=150,
            last_updated=1706745600000000000  # Nanoseconds
        ),
        open_interest=70173,
        underlying_asset=UnderlyingAsset(
            ticker="GOOGL"
        )
    ),
    # ... hundreds more contracts
]
```

**Data Processing:**
1. Convert generator to list: `list(chain_generator)`
2. Filter by expiration dates (7, 14, 21, 30, 45, 60+ DTE)
3. Calculate mid price: `(bid + ask) / 2` or use `day.close` as fallback
4. Calculate days to expiration: `(expiration_date - today).days`
5. Extract Greeks: delta, gamma, theta, vega
6. Calculate ATM IV from contracts nearest to current price

**Caching Strategy:**
```python
# Cache key: finance:cache:options:{ticker}
# TTL: 24 hours (86400 seconds)

# OPTIMIZATION: Fetch filtered chains (short-term + long-term) twice per day
# - Short-term (0-60 days): Both calls and puts for CSP, Covered Calls, PMCC
# - Long-term (12-30 months): Calls only for LEAPS
# - Signal generation uses cached chain (Greeks don't change rapidly)
# - Position valuation uses individual contract API (real-time prices)
# - Reduces API calls by 90%+ and data transfer by 70-80%

ttl = 86400  # 24 hours

# Combine short-term and long-term contracts
all_contracts = short_term_contracts + long_term_contracts

# Convert date objects to strings before caching
contracts_dict = []
for opt in all_contracts:
    opt_dict = opt.model_dump()
    if isinstance(opt_dict["expiration"], date):
        opt_dict["expiration"] = opt_dict["expiration"].isoformat()
    contracts_dict.append(opt_dict)

finance_dao.cache_options_data(ticker, contracts_dict, ttl=ttl)
```

**Performance Note:**
With optimized filtering, we fetch only relevant contracts:
- **Short-term** (0-60 days): ~20-50 contracts for near-term strategies
- **Long-term** (12-30 months): ~10-20 contracts for LEAPS
- **Total**: ~30-70 contracts vs 200-500+ without filtering
- **Benefits**:
  1. 70-80% reduction in data transfer
  2. Faster API response times
  3. Lower Redis memory usage
  4. Faster processing and signal generation
  5. Still cache for 24 hours for cost efficiency
  6. Use individual contract API for position P&L (real-time accuracy)

**Error Handling:**
- Retry up to 3 times with exponential backoff
- Skip individual contracts that fail to parse
- Log warnings for skipped contracts
- Continue processing remaining contracts
- Return cached data if API call fails

---

### 3. Get Individual Option Contract Snapshot

**Massive API Method:** `client.get_snapshot_option()`

**Purpose:** Fetch current price and Greeks for a specific option contract

**Use Cases:**
- Calculate P&L for user positions
- Get accurate current price for position valuation
- Update position metrics in real-time

**Request Parameters:**
```python
client.get_snapshot_option(
    underlying="GOOGL",                    # Underlying stock symbol
    option_ticker="O:GOOGL260206C00190000" # Full option ticker
)
```

**Option Ticker Format:**
```
O:{SYMBOL}{YYMMDD}{C|P}{STRIKE_PADDED}

Examples:
- O:GOOGL260206C00190000  # GOOGL Feb 6, 2026 $190 Call
- O:NVDA250117P00130000   # NVDA Jan 17, 2025 $130 Put

Strike Price Padding:
- 8 digits total
- 5 digits before decimal, 3 after
- $190.00 → 00190000
- $130.50 → 00130500
```

**Response Structure:**
```python
OptionContractSnapshot(
    details=OptionDetails(
        contract_type="call",
        exercise_style="american",
        expiration_date="2026-02-06",
        shares_per_contract=100,
        strike_price=190.0,
        ticker="O:GOOGL260206C00190000"
    ),
    day=DayData(
        close=5.0,              # Most reliable price - last traded
        high=7.22,
        low=4.25,
        open=5.27,
        volume=20184,
        vwap=5.43
    ),
    greeks=Greeks(
        delta=0.5243,
        gamma=0.0333,
        theta=-0.4423,
        vega=0.0943
    ),
    implied_volatility=0.5118,
    last_quote=LastQuote(
        ask=5.2,
        bid=4.8,
        last_updated=1706745600000000000
    ),
    open_interest=70173
)
```

**Price Selection Logic:**
```python
# Priority order for getting current price:
1. If bid > 0 and ask > 0: use (bid + ask) / 2
2. Else if bid > 0: use bid
3. Else if ask > 0: use ask
4. Else if day.close > 0: use day.close  # Last traded price
5. Else: return 0.0 (no price available)
```

**Caching Strategy:**
```python
# Cache key: finance:cache:option_price:{option_ticker}
# TTL: Dynamic based on market hours

ttl = get_cache_ttl()  # Returns 600-3600 seconds
finance_dao.cache_option_price(option_ticker, price, ttl=ttl)
```

**Error Handling:**
- Retry up to 3 times with exponential backoff
- Log error if price fetch fails
- Return 0.0 if all attempts fail
- Use cached price if available
- Fall back to entry price for position valuation

---

### 4. Validate Ticker

**Massive API Method:** `client.get_aggs()` (indirect)

**Purpose:** Verify that a ticker symbol exists before adding to watchlist

**Use Cases:**
- Validate user input when adding ticker to watchlist
- Prevent invalid tickers from being stored
- Provide user feedback on invalid symbols

**Implementation:**
```python
def validate_ticker(ticker: str) -> bool:
    """Validate ticker by attempting to fetch recent data."""
    try:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        bars = self.get_daily_bars(ticker, from_date, to_date)
        return len(bars) > 0
    except Exception as e:
        logger.warning(f"Ticker validation failed for {ticker}: {e}")
        return False
```

**Caching Strategy:**
- No caching (validation is infrequent)
- Quick check with only 7 days of data

**Error Handling:**
- Catch all exceptions
- Return False on any error
- Log warning with ticker and error details

---

### 5. Get Earnings Date

**API Provider:** Financial Modeling Prep (FMP)

**Endpoint:** `https://financialmodelingprep.com/api/v3/historical/earning_calendar/{SYMBOL}`

**Purpose:** Fetch next upcoming earnings date for a ticker

**Use Cases:**
- Display earnings date in dashboard
- Calculate days until earnings
- Use in signal generation (avoid trades near earnings)

**Request Parameters:**
```python
params = {
    "limit": 1,  # Get only the most recent/upcoming earnings
    "apikey": FMP_API_KEY
}
```

**Response Structure:**
```json
[
  {
    "date": "2026-02-15",
    "symbol": "GOOGL",
    "eps": null,
    "epsEstimated": 1.85,
    "time": "amc",
    "revenue": null,
    "revenueEstimated": 89500000000,
    "fiscalDateEnding": "2025-12-31",
    "updatedFromDate": "2026-01-15"
  }
]
```

**Data Processing:**
1. Extract `date` field from first result
2. Parse date string (YYYY-MM-DD format)
3. Only return if date is in the future
4. Calculate days to earnings: `(earnings_date - today).days`

**Caching Strategy:**
```python
# Cache key: finance:cache:earnings:{ticker}
# TTL: 24 hours (86400 seconds)

# Earnings dates don't change frequently
ttl = 86400  # 24 hours
finance_dao.cache_earnings_date(ticker, earnings_date.isoformat(), ttl=ttl)
```

**Error Handling:**
- Retry up to 3 times with exponential backoff
- Log warning if FMP_API_KEY not configured
- Return None if no earnings data found
- Return None if earnings date is in the past
- Gracefully handle API failures

**Configuration:**
- Requires `FMP_API_KEY` environment variable
- Free tier available at https://financialmodelingprep.com
- Falls back gracefully if API key not configured

---

## Caching Architecture

### Cache Keys

```python
# Stock data cache
finance:cache:stock:{ticker}           # Full StockData object
# Example: finance:cache:stock:GOOGL

# Options chain cache
finance:cache:options:{ticker}         # List of OptionContract objects
# Example: finance:cache:options:GOOGL

# Individual option price cache
finance:cache:option_price:{option_ticker}  # Single price value
# Example: finance:cache:option_price:O:GOOGL260206C00190000

# Earnings date cache
finance:cache:earnings:{ticker}        # Earnings date (ISO format)
# Example: finance:cache:earnings:GOOGL

# Last refresh timestamp
finance:last_refresh                   # ISO timestamp string
```

### Dynamic TTL Strategy

```python
def get_cache_ttl() -> int:
    """Get cache TTL based on market hours.
    
    Returns:
        TTL in seconds:
        - 600 (10 min) during market hours
        - 3600 (1 hour) outside market hours
        - Time until market open if < 1 hour away
    """
    if is_market_hours():
        return 600  # 10 minutes during trading
    
    seconds_until_open = get_seconds_until_market_open()
    if seconds_until_open < 3600:
        return seconds_until_open  # Cache until market opens
    
    return 3600  # 1 hour outside market hours
```

### Market Hours Detection

```python
def is_market_hours() -> bool:
    """Check if US market is currently open.
    
    Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
    Excludes holidays (not implemented yet)
    """
    now_et = datetime.now(ZoneInfo("America/New_York"))
    
    # Check if weekend
    if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Check if within trading hours
    market_open = now_et.replace(hour=9, minute=30, second=0)
    market_close = now_et.replace(hour=16, minute=0, second=0)
    
    return market_open <= now_et <= market_close
```

### Cache Invalidation

**Automatic Expiration:**
- Stock data: Expires based on dynamic TTL
- Options data: Expires based on dynamic TTL
- Option prices: Expires based on dynamic TTL

**Manual Invalidation:**
- When ticker removed from watchlist: Delete all cache keys for that ticker
- Force refresh: Bypass cache check, fetch fresh data, update cache

**Cache Warming:**
- No pre-warming implemented
- Cache populated on-demand when data requested
- First request after expiration fetches from API

---

## Error Handling & Retry Logic

### Retry Strategy

```python
class MassiveAPIClient:
    def __init__(self):
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff in seconds
    
    def _retry_request(self, func, *args, **kwargs):
        """Execute request with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"API request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
        
        # All retries failed
        logger.error(f"API request failed after {self.max_retries} attempts")
        raise last_exception
```

### Error Scenarios

**1. Network Timeout:**
- Retry with exponential backoff
- Log each attempt
- Raise exception after 3 failures
- Return cached data if available

**2. Rate Limit Exceeded:**
- Massive API returns 429 status
- Wait for specified delay (from response headers)
- Retry request
- Consider implementing request throttling

**3. Invalid Ticker:**
- API returns 404 or empty data
- Log warning
- Return False for validation
- Raise HTTPException for user-facing endpoints

**4. Malformed Response:**
- Skip individual problematic records
- Log warning with details
- Continue processing remaining data
- Return partial results if possible

**5. API Service Down:**
- All retries fail
- Log error with full context
- Return cached data if available
- Raise HTTPException with 503 status

---

## Performance Considerations

### API Call Frequency

**Stock Data:**
- Called once per ticker per dashboard load
- Cached for 10 min (market hours) or 1 hour (off-hours)
- ~1-2 API calls per ticker per hour during trading

**Options Chain:**
- Called twice per ticker per dashboard load (short-term + long-term)
- Short-term cached for 24 hours: ~20-50 contracts
- Long-term cached for 24 hours: ~10-20 contracts
- Total: ~30-70 contracts vs 200-500+ without filtering
- ~2 API calls per ticker per day (24-hour cache)

**Individual Option Prices:**
- Called once per position per dashboard load
- Cached for 10 min (market hours) or 1 hour (off-hours)
- ~1 API call per position per hour during trading

### Optimization Strategies

**1. Filtered Fetching (IMPLEMENTED):**
- Fetch only short-term (0-60 days) and long-term (12-30 months) contracts
- Use expiration date filters in API calls
- Reduces data transfer by 70-80%
- Two targeted API calls vs one massive call

**2. Selective Refresh:**
- Only refresh expired cache entries
- Force refresh only when user explicitly requests
- Reduce unnecessary API calls

**3. Cache Warming:**
- Pre-fetch data for watchlist tickers during off-hours
- Ensure cache is warm when market opens
- Reduce latency for first request

**4. Data Compression:**
- Store only essential fields in cache
- Reduce Redis memory usage
- Faster serialization/deserialization

---

## Usage Examples

### Example 1: Fetch Stock Data with Caching

```python
# In MarketDataService
async def get_stock_data(self, ticker: str, force_refresh: bool = False) -> StockData:
    # Check cache first
    if not force_refresh:
        cached = self.finance_dao.get_cached_stock_data(ticker)
        if cached:
            return StockData(**cached)
    
    # Fetch from API
    bars = self.massive_client.get_daily_bars(ticker, from_date, to_date)
    
    # Process data
    stock_data = self._process_bars(bars)
    
    # Cache with dynamic TTL
    ttl = get_cache_ttl()
    self.finance_dao.cache_stock_data(ticker, stock_data.model_dump(), ttl=ttl)
    
    return stock_data
```

### Example 2: Fetch Options Chain with Optimized Filtering

```python
# In MarketDataService
async def get_options_chain(self, ticker: str, force_refresh: bool = False) -> List[OptionContract]:
    # Check cache
    if not force_refresh:
        cached = self.finance_dao.get_cached_options_data(ticker)
        if cached:
            return [OptionContract(**opt) for opt in cached]
    
    try:
        # Calculate date ranges
        today = date.today()
        
        # Short-term: 0-60 days (for CSP, Covered Calls, PMCC)
        short_term_start = today.isoformat()
        short_term_end = (today + timedelta(days=60)).isoformat()
        
        # Long-term: 12-30 months (for LEAPS)
        long_term_start = (today + timedelta(days=365)).isoformat()
        long_term_end = (today + timedelta(days=900)).isoformat()
        
        # Fetch short-term options (both calls and puts)
        short_term_generator = self.massive_client.get_options_chain_snapshot(
            ticker,
            expiration_date_gte=short_term_start,
            expiration_date_lte=short_term_end,
        )
        short_term_chain = list(short_term_generator)
        
        # Fetch long-term options (calls only for LEAPS)
        long_term_generator = self.massive_client.get_options_chain_snapshot(
            ticker,
            expiration_date_gte=long_term_start,
            expiration_date_lte=long_term_end,
            contract_type="call",
        )
        long_term_chain = list(long_term_generator)
        
        # Combine both chains
        chain = short_term_chain + long_term_chain
        
        # Process contracts
        options_contracts = []
        for contract in chain:
            try:
                option = self._process_contract(contract)
                options_contracts.append(option)
            except Exception as e:
                logger.warning(f"Skipping contract: {e}")
                continue
        
        # Cache results for 24 hours
        ttl = 86400
        self.finance_dao.cache_options_data(ticker, contracts_dict, ttl=ttl)
        
        return options_contracts
        
    except Exception as e:
        logger.error(f"Failed to fetch options chain: {e}")
        # Return cached data if available
        cached = self.finance_dao.get_cached_options_data(ticker)
        if cached:
            return [OptionContract(**opt) for opt in cached]
        raise
```

### Example 3: Get Individual Option Price

```python
async def get_option_price(self, ticker: str, option_ticker: str) -> float:
    # Check cache
    cached_price = self.finance_dao.get_cached_option_price(option_ticker)
    if cached_price is not None:
        return cached_price
    
    try:
        # Fetch from API
        snapshot = self.massive_client.get_option_contract_snapshot(ticker, option_ticker)
        
        # Extract price with fallback logic
        price = 0.0
        if snapshot.last_quote:
            bid = snapshot.last_quote.bid or 0.0
            ask = snapshot.last_quote.ask or 0.0
            if bid > 0 and ask > 0:
                price = (bid + ask) / 2
            elif bid > 0:
                price = bid
            elif ask > 0:
                price = ask
        
        # Fallback to day.close
        if price == 0.0 and snapshot.day and snapshot.day.close > 0:
            price = snapshot.day.close
        
        # Cache result
        if price > 0:
            ttl = get_cache_ttl()
            self.finance_dao.cache_option_price(option_ticker, price, ttl=ttl)
        
        return price
        
    except Exception as e:
        logger.error(f"Failed to get option price: {e}")
        return 0.0
```

---

## Monitoring & Logging

### Key Metrics to Track

1. **API Call Volume:**
   - Calls per minute/hour
   - Calls by endpoint type
   - Cache hit/miss ratio

2. **Response Times:**
   - Average API response time
   - P95/P99 latency
   - Timeout frequency

3. **Error Rates:**
   - Failed requests by error type
   - Retry success rate
   - Cache fallback usage

4. **Cache Performance:**
   - Hit rate by cache type
   - Average TTL effectiveness
   - Memory usage

### Logging Examples

```python
# Successful API call
logger.info(f"Fetched daily bars for {ticker}: {len(bars)} bars")

# Cache hit
logger.info(f"Using cached stock data for {ticker}")

# Retry attempt
logger.warning(f"API request failed (attempt {attempt + 1}/{max_retries}): {error}")

# Final failure
logger.error(f"API request failed after {max_retries} attempts: {error}")

# Cache fallback
logger.warning(f"Using cached data after API failure for {ticker}")
```

---

## Future Enhancements

### 1. Implement Earnings Calendar

```python
# Potential endpoint (not currently available in Massive API)
def get_earnings_date(self, ticker: str) -> Optional[date]:
    """Fetch next earnings date for ticker."""
    # May need alternative data source
    pass
```

### 2. Add Historical IV Data

```python
# Calculate IV percentile from historical data
def calculate_iv_percentile(self, ticker: str, current_iv: float) -> float:
    """Calculate IV percentile from 52-week IV history."""
    # Fetch historical IV data
    # Calculate percentile
    pass
```

### 3. Implement Request Throttling

```python
# Rate limiting to avoid API quota issues
class RateLimiter:
    def __init__(self, max_calls_per_minute: int = 60):
        self.max_calls = max_calls_per_minute
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        # Implementation
        pass
```

### 4. Add Concurrent Fetching

```python
# Fetch multiple tickers in parallel
async def get_dashboard_data(self, tickers: List[str]) -> List[StockData]:
    """Fetch data for multiple tickers concurrently."""
    tasks = [self.get_stock_data(ticker) for ticker in tickers]
    return await asyncio.gather(*tasks)
```

---

## References

- **Massive API Documentation:** https://polygon.io/docs
- **Python SDK:** https://github.com/polygon-io/client-python
- **Market Hours Logic:** `mojo-api/api/lib/util/market_hours.py`
- **Caching Implementation:** `mojo-api/api/dao/finance_dao.py`
- **API Client:** `mojo-api/api/lib/stock_tracking/massive_client.py`
- **Service Layer:** `mojo-api/api/lib/stock_tracking/services/market_data_service.py`
