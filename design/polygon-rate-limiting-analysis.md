# Polygon.io API Rate Limiting - Root Cause & Fix

## Problem Summary

User hit Polygon.io (Massive API) rate limit (429 errors) when visiting the finance dashboard page, despite:
- ❌ No auto-refresh enabled
- ❌ No force refresh used
- ❌ Cache TTLs properly configured (10 min / 1 hour)

Investigation revealed: **Cache was completely broken** due to date deserialization bug.

## Root Cause: Cache Deserialization Bug 🔥

### The Bug

When `earnings_date` field was added to `StockData` model, a serialization mismatch was introduced:

1. **Caching** (write): `model_dump()` converts `date` objects → strings (ISO format)
   ```python
   # Cached data in Redis
   {"earnings_date": "2026-02-25", ...}  # String
   ```

2. **Retrieval** (read): `StockData(**cached)` expects `date` objects, not strings
   ```python
   # Pydantic validation
   StockData(earnings_date="2026-02-25")  # ❌ ValidationError: expected date, got str
   ```

3. **Result**: Validation fails silently, `get_cached_stock_data()` returns `None`

4. **Impact**: Every page visit = fresh API calls (cache never used)

### Code Location

**File**: `mojo-api/api/lib/stock_tracking/services/market_data_service.py`

**Before (Broken)**:
```python
# Line 62
if cached:
    self.ctx.logger.info(f"Using cached stock data for {ticker}")
    return StockData(**cached)  # ❌ FAILS: earnings_date is string, expects date
```

**After (Fixed)**:
```python
# Line 62
if cached:
    self.ctx.logger.info(f"Using cached stock data for {ticker}")
    # Convert date strings back to date objects
    if "earnings_date" in cached and cached["earnings_date"]:
        cached["earnings_date"] = date.fromisoformat(cached["earnings_date"])
    return StockData(**cached)  # ✅ WORKS: earnings_date is now date object
```

**Also Fixed** (Line 140):
```python
# Ensure proper JSON serialization when caching
self.finance_dao.cache_stock_data(ticker, stock_data.model_dump(mode='json'), ttl=ttl)
```

## Why This Caused Rate Limiting

### API Call Pattern (Per Dashboard Load)

For **3 tickers** in watchlist:
- Stock data: 3 × 1 call = **3 calls**
- Options chain: 3 × 2 calls = **6 calls** (short-term + long-term)
- Position valuation: 6 positions × 1 call = **6 calls**
- **Total: 15 API calls per page visit**

### With Broken Cache

- **Every page visit** = 15 fresh API calls (cache never hit)
- **Polygon.io free tier**: 5 calls/minute
- **Result**: Hit rate limit after 2-3 page visits 🔴

### Timeline

1. ✅ Added `earnings_date` field to `StockData` model
2. ✅ Cached data with `model_dump()` (dates → strings)
3. ❌ Retrieved cached data with `StockData(**cached)` (validation failed)
4. ❌ Cache always returned `None`
5. ❌ Every page visit fetched fresh data from API
6. 🔴 Hit rate limit after 2-3 visits

## The Fix

### Changes Made

1. **Date Deserialization** (`market_data_service.py:62`)
   - Convert `earnings_date` string back to `date` object before creating `StockData`

2. **Explicit JSON Mode** (`market_data_service.py:140`)
   - Use `model_dump(mode='json')` to ensure proper serialization

### Expected Behavior After Fix

**First visit** (cold cache):
- 15 API calls
- Data cached for 10 min (market hours) or 1 hour (off-hours)

**Subsequent visits** (within cache TTL):
- 0 API calls (all data from cache) ✅
- No rate limiting issues ✅

**Cache expiration**:
- After 10 min / 1 hour, next visit fetches fresh data
- With 3 tickers, 15 calls every 10 minutes = **1.5 calls/minute** ✅ (well under 5/min limit)

## Verification Steps

### 1. Check Cache is Working

```bash
# Visit dashboard page
# Check logs for "Using cached stock data" messages

# Should see:
# "Using cached stock data for NVDA"
# "Using cached stock data for GOOGL"
# "Using cached stock data for TSLA"
```

### 2. Monitor API Calls (NEW - Enhanced Logging)

All Massive API calls now have distinctive emoji markers:

- 🔵 `MASSIVE API CALL` - API call attempt
- ✅ `MASSIVE API CALL SUCCESS` - Successful API call
- ❌ `MASSIVE API CALL FAILED` - Failed after all retries
- 📊 `get_daily_bars` - Stock historical data
- 📈 `get_options_chain_snapshot` - Options chain data
- 💰 `get_option_contract_snapshot` - Individual option price
- 🔍 `validate_ticker` - Ticker validation

**Count API calls:**
```bash
cd mojo-api
./count_massive_calls.sh

# Output shows:
# - Total successful calls
# - Total attempted calls
# - Failed calls
# - Breakdown by endpoint
# - Last 10 API calls
```

**Watch live API calls:**
```bash
# In terminal where 'bb dev' is running, watch for:
tail -f _local/logs/api_*.log | grep "MASSIVE API"

# First visit: Should see API calls
# Second visit (within 10 min): Should see NO API calls
```

**Expected pattern after fix:**
```
# First page visit (cold cache)
📊 MASSIVE API: get_daily_bars(NVDA, ...)
🔵 MASSIVE API CALL (attempt 1/3)
✅ MASSIVE API CALL SUCCESS
📈 MASSIVE API: get_options_chain_snapshot(NVDA, ...)
🔵 MASSIVE API CALL (attempt 1/3)
✅ MASSIVE API CALL SUCCESS
... (15 total calls for 3 tickers)

# Second page visit (within cache TTL)
# NO MASSIVE API CALLS - all from cache ✅
```

### 3. Check Redis Cache

```bash
# Check if cache keys exist (requires Redis password)
redis-cli -h 192.168.0.105 -p 6380 -a <password> KEYS "finance:cache:stock:*"

# Should return:
# finance:cache:stock:NVDA
# finance:cache:stock:GOOGL
# finance:cache:stock:TSLA
```

## Prevention for Future

### When Adding Date/DateTime Fields to Models

1. **Always handle deserialization** when retrieving from cache:
   ```python
   if "date_field" in cached and cached["date_field"]:
       cached["date_field"] = date.fromisoformat(cached["date_field"])
   ```

2. **Use `mode='json'`** when caching:
   ```python
   cache_data(model.model_dump(mode='json'))
   ```

3. **Test cache round-trip** after adding date fields:
   ```python
   # Test
   cached = cache.get(key)
   model = Model(**cached)  # Should not raise ValidationError
   ```

### Pattern for All Date Fields

```python
# Caching (write)
data = model.model_dump(mode='json')  # Dates → strings
cache.set(key, data)

# Retrieval (read)
cached = cache.get(key)
if cached:
    # Convert all date fields back
    for field in ["date_field1", "date_field2"]:
        if field in cached and cached[field]:
            cached[field] = date.fromisoformat(cached[field])
    return Model(**cached)
```

## Conclusion

The rate limiting was **not** caused by:
- ❌ Auto-refresh (was disabled)
- ❌ Force refresh (was not used)
- ❌ Aggressive cache TTLs (were appropriate)

The rate limiting **was** caused by:
- ✅ **Broken cache** due to date deserialization bug
- ✅ Every page visit hitting API instead of cache

**Fix applied**: Date deserialization in cache retrieval + explicit JSON mode in caching

**Expected result**: Cache now works correctly, API calls reduced by ~95% ✅
