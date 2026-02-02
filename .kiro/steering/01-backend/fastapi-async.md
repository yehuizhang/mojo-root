---
inclusion: fileMatch
fileMatchPattern: '**/*.py'
---
# Async/Await Patterns in FastAPI

## When to Use Async

FastAPI supports both sync and async route handlers. Use async when:

### ✅ Use Async For:

1. **External API calls** (HTTP requests)
2. **Database queries** (if using async driver)
3. **File I/O operations** (reading/writing files)
4. **Long-running operations** that can benefit from concurrency
5. **Multiple I/O operations** that can run concurrently

### ❌ Use Sync For:

1. **CPU-bound operations** (calculations, data processing)
2. **Synchronous libraries** (Redis client, most Python libraries)
3. **Simple CRUD operations** with sync database drivers
4. **Quick operations** that complete in milliseconds

## Async Route Handlers

### Async Handler Pattern

```python
@router.get("/dashboard")
async def get_dashboard(
    force_refresh: bool = Query(False),
    handler: FinanceHandler = Depends(get_finance_handler),
) -> DashboardResponse:
    """Async route handler for I/O-bound operation."""
    return await handler.get_dashboard(force_refresh=force_refresh)
```

### Sync Handler Pattern

```python
@router.get("/watchlist")
def get_watchlist(
    handler: FinanceHandler = Depends(get_finance_handler),
) -> List[str]:
    """Sync route handler for quick operation."""
    return handler.get_watchlist()
```

## Async Handler Methods

### Pattern: Async Method with External API Calls

```python
class FinanceHandler:
    async def get_dashboard(self, force_refresh: bool = False) -> DashboardResponse:
        """Async method that makes external API calls."""
        tickers = self.finance_dao.get_watchlist()  # Sync Redis call
        
        stocks_data = []
        for ticker in tickers:
            # Async external API calls
            stock_data = await self.market_data_service.get_stock_data(ticker, force_refresh)
            options = await self.market_data_service.get_options_chain(ticker, force_refresh)
            
            # Sync calculations
            signal = self.signal_generator_service.generate_signal(stock_data, options)
            
            stocks_data.append(StockDashboardData(
                ticker=ticker,
                stock_data=stock_data,
                signal=signal,
            ))
        
        return DashboardResponse(stocks=stocks_data)
```

### Pattern: Sync Method for Quick Operations

```python
class FinanceHandler:
    def get_watchlist(self) -> List[str]:
        """Sync method for quick Redis operation."""
        return self.finance_dao.get_watchlist()
    
    def add_ticker(self, ticker: str) -> dict:
        """Sync method with validation."""
        if not self.market_data_service.validate_ticker(ticker):
            raise HTTPException(status_code=400, detail="Invalid ticker")
        
        self.finance_dao.add_to_watchlist(ticker)
        return {"ticker": ticker, "status": "added"}
```

## Concurrent Operations

### Pattern: Parallel API Calls with asyncio.gather

```python
import asyncio

async def get_dashboard(self) -> DashboardResponse:
    """Fetch data for multiple tickers concurrently."""
    tickers = self.finance_dao.get_watchlist()
    
    # Create tasks for concurrent execution
    tasks = [
        self._process_ticker(ticker)
        for ticker in tickers
    ]
    
    # Execute all tasks concurrently
    stocks_data = await asyncio.gather(*tasks)
    
    return DashboardResponse(stocks=stocks_data)

async def _process_ticker(self, ticker: str) -> StockDashboardData:
    """Process single ticker (called concurrently)."""
    # These run concurrently for each ticker
    stock_data, options = await asyncio.gather(
        self.market_data_service.get_stock_data(ticker),
        self.market_data_service.get_options_chain(ticker),
    )
    
    # Sync calculation
    signal = self.signal_generator_service.generate_signal(stock_data, options)
    
    return StockDashboardData(
        ticker=ticker,
        stock_data=stock_data,
        signal=signal,
    )
```

### Pattern: Sequential with Error Handling

```python
async def get_dashboard(self) -> DashboardResponse:
    """Process tickers sequentially with error handling."""
    tickers = self.finance_dao.get_watchlist()
    stocks_data = []
    
    for ticker in tickers:
        try:
            # Async operations
            stock_data = await self.market_data_service.get_stock_data(ticker)
            options = await self.market_data_service.get_options_chain(ticker)
            
            # Sync calculation
            signal = self.signal_generator_service.generate_signal(stock_data, options)
            
            stocks_data.append(StockDashboardData(
                ticker=ticker,
                stock_data=stock_data,
                signal=signal,
            ))
        except Exception as e:
            self.ctx.logger.error(f"Failed to process {ticker}: {e}")
            continue  # Skip failed ticker, continue with others
    
    return DashboardResponse(stocks=stocks_data)
```

## Service Layer Async Patterns

### Pattern: Async Service with External API

```python
class MarketDataService:
    async def get_stock_data(self, ticker: str, force_refresh: bool = False) -> StockData:
        """Async method for external API call."""
        # Check cache (sync Redis)
        if not force_refresh:
            cached = self.finance_dao.get_cached_stock_data(ticker)
            if cached:
                return StockData(**cached)
        
        # Fetch from external API (async)
        bars = await self._fetch_bars_from_api(ticker)
        
        # Process data (sync CPU-bound)
        stock_data = self._process_bars(bars)
        
        # Cache result (sync Redis)
        self.finance_dao.cache_stock_data(ticker, stock_data.model_dump())
        
        return stock_data
    
    async def _fetch_bars_from_api(self, ticker: str) -> List[Bar]:
        """Async external API call."""
        # Assuming massive_client has async methods
        return await self.massive_client.get_daily_bars_async(ticker)
```

### Pattern: Sync Service for Calculations

```python
class SignalGeneratorService:
    def generate_csp_signal(
        self,
        stock_data: StockData,
        options: List[OptionContract],
    ) -> CSPSignal:
        """Sync method for CPU-bound calculations."""
        conditions_met = 0
        reasoning = []
        
        # All calculations are CPU-bound, no I/O
        if self._check_pullback(stock_data):
            conditions_met += 1
            reasoning.append("✅ Price near support")
        
        if self._check_iv(stock_data):
            conditions_met += 1
            reasoning.append("✅ High IV")
        
        # More calculations...
        
        return CSPSignal(
            score=self._calculate_score(conditions_met),
            reasoning=reasoning,
        )
```

## Mixing Sync and Async

### Pattern: Async Handler with Sync Dependencies

```python
class FinanceHandler:
    async def add_position(self, position: PositionCreate) -> dict:
        """Async handler with mix of sync and async operations."""
        # Sync validation (Redis)
        if not self.finance_dao.ticker_in_watchlist(position.ticker):
            self.finance_dao.add_to_watchlist(position.ticker)
        
        # Async external API call
        current_price = await self.market_data_service.get_current_price(position.ticker)
        
        # Sync database operation (Redis)
        saved_position = self.finance_dao.save_position(position)
        
        # Async calculation of metrics
        metrics = await self._calculate_position_metrics(saved_position, current_price)
        
        return {**saved_position, "metrics": metrics}
```

## Error Handling in Async Code

### Pattern: Try-Except in Async Methods

```python
async def get_stock_data(self, ticker: str) -> StockData:
    """Async method with error handling."""
    try:
        # Async operation
        bars = await self.massive_client.get_daily_bars(ticker)
        
        if not bars:
            raise ValueError(f"No data for {ticker}")
        
        return self._process_bars(bars)
        
    except asyncio.TimeoutError:
        self.ctx.logger.error(f"Timeout fetching data for {ticker}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout fetching data for {ticker}"
        )
    except Exception as e:
        self.ctx.logger.error(f"Failed to fetch data for {ticker}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch data: {str(e)}"
        )
```

### Pattern: Graceful Degradation

```python
async def get_dashboard(self) -> DashboardResponse:
    """Async method with graceful degradation."""
    tickers = self.finance_dao.get_watchlist()
    stocks_data = []
    
    for ticker in tickers:
        try:
            # Try to fetch fresh data
            stock_data = await self.market_data_service.get_stock_data(ticker)
            stocks_data.append(stock_data)
        except Exception as e:
            self.ctx.logger.warning(f"Failed to fetch {ticker}: {e}")
            
            # Try to use cached data as fallback
            cached = self.finance_dao.get_cached_stock_data(ticker)
            if cached:
                self.ctx.logger.info(f"Using cached data for {ticker}")
                stocks_data.append(StockData(**cached))
            else:
                # Skip ticker if no cached data available
                continue
    
    return DashboardResponse(stocks=stocks_data)
```

## Testing Async Code

### Pattern: Async Test Functions

```python
import pytest

@pytest.mark.asyncio
async def test_get_dashboard():
    """Test async handler method."""
    # Arrange
    mock_dao = Mock()
    mock_dao.get_watchlist.return_value = ["AAPL"]
    
    mock_service = Mock()
    mock_service.get_stock_data = AsyncMock(
        return_value=StockData(ticker="AAPL", current_price=150.0)
    )
    
    handler = FinanceHandler(
        finance_dao=mock_dao,
        market_data_service=mock_service
    )
    
    # Act
    result = await handler.get_dashboard()
    
    # Assert
    assert len(result.stocks) == 1
    assert result.stocks[0].ticker == "AAPL"
```

### Pattern: Mocking Async Methods

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_async_mock():
    """Test with async mock."""
    mock_service = Mock()
    
    # Mock async method
    mock_service.get_stock_data = AsyncMock(
        return_value=StockData(ticker="AAPL", current_price=150.0)
    )
    
    # Call async method
    result = await mock_service.get_stock_data("AAPL")
    
    # Assert
    assert result.ticker == "AAPL"
    mock_service.get_stock_data.assert_called_once_with("AAPL")
```

## Common Mistakes

### ❌ Forgetting await

```python
# BAD - returns coroutine, not result
async def get_data():
    result = self.async_method()  # Missing await
    return result

# GOOD
async def get_data():
    result = await self.async_method()
    return result
```

### ❌ Using async for CPU-bound operations

```python
# BAD - async doesn't help CPU-bound work
async def calculate_rsi(prices: List[float]) -> float:
    # Pure calculation, no I/O
    return sum(prices) / len(prices)

# GOOD - use sync for CPU-bound
def calculate_rsi(prices: List[float]) -> float:
    return sum(prices) / len(prices)
```

### ❌ Not handling exceptions in concurrent operations

```python
# BAD - one failure stops all
async def process_all():
    tasks = [process_ticker(t) for t in tickers]
    results = await asyncio.gather(*tasks)  # Fails if any task fails

# GOOD - handle failures gracefully
async def process_all():
    tasks = [process_ticker(t) for t in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_results = [r for r in results if not isinstance(r, Exception)]
    return valid_results
```

### ❌ Blocking the event loop

```python
# BAD - blocks event loop
async def process_data():
    time.sleep(5)  # Blocks entire event loop
    return result

# GOOD - use async sleep
async def process_data():
    await asyncio.sleep(5)  # Doesn't block
    return result
```

## Performance Considerations

### When Async Improves Performance

```python
# Sequential (slow) - 3 seconds total
async def sequential():
    data1 = await fetch_data1()  # 1 second
    data2 = await fetch_data2()  # 1 second
    data3 = await fetch_data3()  # 1 second
    return [data1, data2, data3]

# Concurrent (fast) - 1 second total
async def concurrent():
    results = await asyncio.gather(
        fetch_data1(),  # All run concurrently
        fetch_data2(),
        fetch_data3(),
    )
    return results
```

### When Async Doesn't Help

```python
# Async doesn't help CPU-bound work
async def calculate_all():
    # These are CPU-bound, can't run concurrently in Python
    result1 = calculate_rsi(prices1)  # Blocks
    result2 = calculate_rsi(prices2)  # Blocks
    result3 = calculate_rsi(prices3)  # Blocks
    return [result1, result2, result3]

# For CPU-bound work, use multiprocessing instead
from concurrent.futures import ProcessPoolExecutor

def calculate_all():
    with ProcessPoolExecutor() as executor:
        results = executor.map(calculate_rsi, [prices1, prices2, prices3])
    return list(results)
```

## Best Practices

1. **Use async for I/O-bound operations** (API calls, file I/O)
2. **Use sync for CPU-bound operations** (calculations, data processing)
3. **Use asyncio.gather for concurrent operations** when order doesn't matter
4. **Handle exceptions in concurrent operations** with `return_exceptions=True`
5. **Don't block the event loop** with sync sleep or CPU-intensive work
6. **Test async code with pytest-asyncio** and `AsyncMock`
7. **Profile before optimizing** - measure actual performance gains
