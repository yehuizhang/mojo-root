# API Refactoring & Improvements - Design Document

## 1. Architecture Overview

### 1.1 Current Architecture
```
Router → Handler → DAO/Service → Redis/External API
```

### 1.2 Proposed Architecture
```
Router → Handler (extends BaseHandler) → DAO/Service → Redis/External API
                ↓
         ValidationUtils, ErrorUtils
```

**Key Changes**:
- Introduce `BaseHandler` for common functionality
- Extract utilities for validation and error handling
- Optimize DAO operations with pipelines
- Refactor large methods into focused components

## 2. Component Design

### 2.1 BaseHandler Class

**Purpose**: Provide common functionality for all handlers

**Location**: `api/handlers/base_handler.py`

**Design**:
```python
from abc import ABC
from typing import Optional
from fastapi import HTTPException, status
from api.lib.util.app_context import build_context, AppContext

class BaseHandler(ABC):
    """Base handler with common functionality for all handlers."""
    
    def __init__(self):
        """Initialize base handler with context."""
        self.ctx: AppContext = build_context()
    
    def _check_service_initialized(self, service: Optional[object], service_name: str) -> None:
        """Check if required service is initialized.
        
        Args:
            service: Service instance to check
            service_name: Name of service for error message
            
        Raises:
            HTTPException: If service is not initialized
        """
        if service is None:
            self.ctx.logger.error(f"{service_name} not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{service_name} not initialized"
            )
    
    def _check_services_initialized(self, **services) -> None:
        """Check multiple services are initialized.
        
        Args:
            **services: Keyword arguments of service_name=service_instance
            
        Raises:
            HTTPException: If any service is not initialized
        """
        missing = [name for name, service in services.items() if service is None]
        if missing:
            services_str = ", ".join(missing)
            self.ctx.logger.error(f"Services not initialized: {services_str}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Required services not initialized: {services_str}"
            )
    
    def _log_and_raise_error(
        self, 
        operation: str, 
        error: Exception, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None
    ) -> None:
        """Log error and raise HTTPException.
        
        Args:
            operation: Operation that failed
            error: Original exception
            status_code: HTTP status code to return
            detail: Custom error detail (defaults to generic message)
            
        Raises:
            HTTPException: Always raises with appropriate status and detail
        """
        self.ctx.logger.error(f"{operation} failed: {error}")
        raise HTTPException(
            status_code=status_code,
            detail=detail or f"Operation failed: {operation}"
        )
```

**Benefits**:
- Eliminates repeated service checks
- Consistent error handling
- Single place to manage context
- Easy to extend with more common functionality

### 2.2 ValidationUtils Class

**Purpose**: Centralize common validation logic

**Location**: `api/lib/util/validation_util.py`

**Design**:
```python
from typing import Optional
from fastapi import HTTPException, status

class ValidationUtils:
    """Utility class for common validation operations."""
    
    @staticmethod
    def validate_ticker_format(ticker: str) -> str:
        """Validate and normalize ticker format.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Normalized ticker (uppercase, trimmed)
            
        Raises:
            HTTPException: If ticker format is invalid
        """
        if not ticker or not ticker.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticker cannot be empty"
            )
        
        normalized = ticker.strip().upper()
        
        # Basic format validation
        if not normalized.isalpha() or len(normalized) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ticker format: {ticker}"
            )
        
        return normalized
    
    @staticmethod
    def validate_required_field(value: Optional[object], field_name: str) -> None:
        """Validate that required field is present.
        
        Args:
            value: Field value to check
            field_name: Name of field for error message
            
        Raises:
            HTTPException: If field is None or empty
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Required field missing: {field_name}"
            )
    
    @staticmethod
    def validate_positive_number(value: float, field_name: str) -> None:
        """Validate that number is positive.
        
        Args:
            value: Number to validate
            field_name: Name of field for error message
            
        Raises:
            HTTPException: If number is not positive
        """
        if value <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be positive, got {value}"
            )
```

**Benefits**:
- Reusable validation logic
- Consistent error messages
- Easy to test in isolation
- Single source of truth for validation rules

### 2.3 Optimized FinanceDAO

**Purpose**: Improve Redis operations with pipelines

**Location**: `api/dao/finance_dao.py`

**Design Changes**:

```python
def get_all_positions(self) -> List[dict]:
    """Get all positions using pipeline for batch retrieval.
    
    Returns:
        List of position dictionaries with date objects
    """
    try:
        position_ids = self.redis.client.smembers(self.POSITIONS_INDEX_KEY)
        if not position_ids:
            return []

        # Use pipeline for batch retrieval
        pipe = self.redis.client.pipeline()
        for pos_id in position_ids:
            pipe.get(f"{self.POSITION_PREFIX}{pos_id}")
        
        results = pipe.execute()
        
        # Process results
        positions = []
        for pos_data in results:
            if pos_data:
                position_dict = json.loads(pos_data)
                positions.append(self._deserialize_position(position_dict))
        
        return positions
    except Exception as e:
        self._log_error("get_all_positions", e)
        return []

def delete_positions_batch(self, position_ids: List[str]) -> bool:
    """Delete multiple positions atomically.
    
    Args:
        position_ids: List of position IDs to delete
        
    Returns:
        True if all positions deleted successfully
    """
    try:
        if not position_ids:
            return True
        
        pipe = self.redis.client.pipeline()
        
        # Delete all position objects
        for pos_id in position_ids:
            pipe.delete(f"{self.POSITION_PREFIX}{pos_id}")
        
        # Remove all from index
        for pos_id in position_ids:
            pipe.srem(self.POSITIONS_INDEX_KEY, pos_id)
        
        pipe.execute()
        return True
    except Exception as e:
        self._log_error(f"delete_positions_batch {len(position_ids)} positions", e)
        return False
```

**Benefits**:
- Reduces network round trips
- Atomic operations
- Better performance with many positions
- Consistent with Redis best practices

### 2.4 Refactored FinanceHandler

**Purpose**: Break down large methods into focused components

**Location**: `api/handlers/finance_handler.py`

**Design Changes**:

```python
class FinanceHandler(BaseHandler):
    """Handler for finance business logic."""

    def __init__(
        self,
        finance_dao: Optional[FinanceDAO] = None,
        market_data_service: Optional[MarketDataService] = None,
        signal_generator_service: Optional[SignalGeneratorService] = None,
        position_recommendation_service: Optional[PositionRecommendationService] = None,
    ):
        """Initialize finance handler with injected dependencies."""
        super().__init__()  # Initialize BaseHandler (sets self.ctx)
        self.finance_dao = finance_dao
        self.market_data_service = market_data_service
        self.signal_generator_service = signal_generator_service
        self.position_recommendation_service = position_recommendation_service

    async def get_dashboard(self, force_refresh: bool = False) -> DashboardResponse:
        """Get complete dashboard data for all watchlist tickers.
        
        Refactored to use helper methods for better organization.
        """
        # Check services
        self._check_services_initialized(
            finance_dao=self.finance_dao,
            market_data_service=self.market_data_service,
            signal_generator_service=self.signal_generator_service
        )

        try:
            tickers = self.finance_dao.get_watchlist()
            
            if not tickers:
                self.ctx.logger.info("Watchlist is empty")
                return DashboardResponse(
                    stocks=[], 
                    timestamp=datetime.utcnow(),
                    last_refresh=self.finance_dao.get_last_refresh_time()
                )

            # Process all tickers
            stocks_data = []
            for ticker in tickers:
                try:
                    stock_data = await self._process_ticker_for_dashboard(ticker, force_refresh)
                    stocks_data.append(stock_data)
                except Exception as e:
                    self.ctx.logger.error(f"Failed to process ticker {ticker}: {e}")
                    continue
            
            return DashboardResponse(
                stocks=stocks_data, 
                timestamp=datetime.utcnow(),
                last_refresh=self.finance_dao.get_last_refresh_time()
            )
            
        except Exception as e:
            self._log_and_raise_error("Dashboard generation", e)

    async def _process_ticker_for_dashboard(
        self, ticker: str, force_refresh: bool
    ) -> StockDashboardData:
        """Process single ticker for dashboard.
        
        Args:
            ticker: Stock symbol
            force_refresh: Whether to bypass cache
            
        Returns:
            Complete stock dashboard data
        """
        # Fetch market data
        stock_data = await self.market_data_service.get_stock_data(ticker, force_refresh)
        options = await self.market_data_service.get_options_chain(ticker, force_refresh)
        
        # Get and process positions
        positions = self.finance_dao.get_positions_for_ticker(ticker)
        categorized_positions = await self._categorize_positions(
            positions, ticker, stock_data.current_price, options
        )
        
        # Generate signals
        signals = self._generate_signals(stock_data, options, categorized_positions)
        
        # Build strategy data
        strategy_data = StrategyData(
            leaps_signal=signals['leaps'],
            pmcc_signal=signals['pmcc'],
            csp_signal=signals['csp'],
            covered_call_signal=signals['covered_call'],
            leaps_position=categorized_positions['leaps'] or None,
            short_call_position=categorized_positions['short_calls'] or None,
            stock_position=categorized_positions['stocks'] or None,
            short_put_position=categorized_positions['short_puts'] or None,
        )
        
        return StockDashboardData(
            ticker=ticker,
            stock_data=stock_data,
            strategy_data=strategy_data,
        )

    async def _categorize_positions(
        self,
        positions: List[dict],
        ticker: str,
        current_price: float,
        options: List[OptionContract]
    ) -> dict:
        """Categorize positions by type with metrics.
        
        Args:
            positions: Raw position data
            ticker: Stock symbol
            current_price: Current stock price
            options: Available options contracts
            
        Returns:
            Dictionary with categorized positions
        """
        categorized = {
            'leaps': [],
            'short_calls': [],
            'stocks': [],
            'short_puts': []
        }
        
        for pos_dict in positions:
            pos = Position(**pos_dict)
            
            # Calculate metrics
            metrics = await self._calculate_position_metrics(pos, current_price, options)
            
            # Generate recommendation if service available
            recommendation = await self._generate_position_recommendation(
                pos, ticker, options
            )
            
            # Create position with metrics
            pos_with_metrics = PositionWithMetrics(
                **pos.model_dump(), 
                metrics=metrics,
                recommendation=recommendation
            )
            
            # Categorize
            if pos.position_type == "option" and pos.option_type == "call":
                if pos.quantity > 0:
                    categorized['leaps'].append(pos_with_metrics)
                else:
                    categorized['short_calls'].append(pos_with_metrics)
            elif pos.position_type == "option" and pos.option_type == "put":
                if pos.quantity < 0:
                    categorized['short_puts'].append(pos_with_metrics)
            elif pos.position_type == "stock":
                categorized['stocks'].append(pos_with_metrics)
        
        return categorized

    async def _generate_position_recommendation(
        self,
        position: Position,
        ticker: str,
        options: List[OptionContract]
    ) -> Optional[object]:
        """Generate recommendation for a position.
        
        Args:
            position: Position to generate recommendation for
            ticker: Stock symbol
            options: Available options contracts
            
        Returns:
            Recommendation object or None if service unavailable
        """
        if not self.position_recommendation_service:
            return None
        
        try:
            # Get current data for option positions
            current_delta = None
            current_option_price = None
            
            if position.position_type == "option":
                matching_option = next(
                    (opt for opt in options 
                     if opt.strike == position.strike 
                     and opt.expiration == position.expiration
                     and opt.option_type == position.option_type),
                    None
                )
                if matching_option:
                    current_delta = matching_option.delta
                    current_option_price = matching_option.mid_price
            
            # Get stock data (from cache if available)
            stock_data = await self.market_data_service.get_stock_data(ticker)
            
            return self.position_recommendation_service.generate_position_recommendation(
                position=position,
                stock_data=stock_data,
                options=options,
                current_delta=current_delta,
                current_price=current_option_price
            )
        except Exception as e:
            self.ctx.logger.error(f"Failed to generate recommendation for position {position.id}: {e}")
            return None

    def _generate_signals(
        self,
        stock_data: StockData,
        options: List[OptionContract],
        categorized_positions: dict
    ) -> dict:
        """Generate trading signals for all strategies.
        
        Args:
            stock_data: Stock data with indicators
            options: Available options contracts
            categorized_positions: Positions categorized by type
            
        Returns:
            Dictionary of signals by strategy
        """
        # CSP signal
        csp_signal = self.signal_generator_service.generate_csp_signal(stock_data, options)
        
        # Covered call signal (use first stock position for cost basis)
        cost_basis = None
        if categorized_positions['stocks']:
            cost_basis = categorized_positions['stocks'][0].purchase_price
        covered_call_signal = self.signal_generator_service.generate_covered_call_signal(
            stock_data, options, cost_basis
        )
        
        # LEAPS signal
        leaps_signal = self.signal_generator_service.generate_leaps_signal(stock_data, options)
        
        # PMCC signal (use first LEAPS position if available)
        first_leaps = categorized_positions['leaps'][0] if categorized_positions['leaps'] else None
        pmcc_signal = self.signal_generator_service.generate_pmcc_signal(
            stock_data, options, first_leaps
        )
        
        return {
            'csp': csp_signal,
            'covered_call': covered_call_signal,
            'leaps': leaps_signal,
            'pmcc': pmcc_signal
        }

    def add_ticker(self, ticker: str) -> dict:
        """Add ticker to watchlist with validation."""
        # Check services
        self._check_services_initialized(
            finance_dao=self.finance_dao,
            market_data_service=self.market_data_service
        )
        
        # Validate and normalize ticker
        from api.lib.util.validation_util import ValidationUtils
        ticker = ValidationUtils.validate_ticker_format(ticker)
        
        # Validate ticker exists
        if not self.market_data_service.validate_ticker(ticker):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticker {ticker} not found"
            )
        
        # Check if already in watchlist
        if self.finance_dao.ticker_in_watchlist(ticker):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ticker {ticker} already in watchlist"
            )
        
        # Add to watchlist
        if not self.finance_dao.add_to_watchlist(ticker):
            self._log_and_raise_error(
                f"add_ticker {ticker}",
                Exception("DAO operation failed"),
                detail=f"Failed to add ticker {ticker}"
            )
        
        return {"ticker": ticker, "status": "added"}
```

**Benefits**:
- Methods under 50 lines each
- Single responsibility per method
- Easier to test individual components
- Better code organization
- Reusable helper methods

### 2.5 Updated AuthHandler

**Purpose**: Consistent context management

**Location**: `api/handlers/auth_handler.py`

**Design Changes**:

```python
class AuthHandler(BaseHandler):
    """Handler for authentication business logic."""

    def __init__(self, user_dao: UserDAO, invitation_dao: InvitationDAO):
        """Initialize auth handler with dependencies."""
        super().__init__()  # Initialize BaseHandler (sets self.ctx)
        
        self.__secret_key = get_env("JWT_SECRET_KEY")
        if not self.__secret_key:
            raise ValueError("JWT_SECRET_KEY must be set")
        
        self.access_token_expires = timedelta(hours=24 * 180)
        self.user_dao = user_dao
        self.invitation_dao = invitation_dao

    def get_current_user(self, token: str) -> UserModel:
        """Get the current authenticated user from JWT token."""
        # Use self.ctx instead of creating new context
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            jwt_payload = SecretsManager.decode_jwt(token=token, secret_key=self.__secret_key)
            username = jwt_payload.sub
            if username is None:
                raise credentials_exception
        except (ValueError, Exception):
            raise credentials_exception

        user = self.user_dao.get_user_by_username(username)
        if user is None:
            self.ctx.logger.warning("User not found. username: %s", username)
            raise credentials_exception

        if not user.is_active:
            self.ctx.logger.warning("User not active. username: %s", username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
```

**Benefits**:
- Consistent with other handlers
- No repeated context creation
- Inherits common functionality from BaseHandler

## 3. Data Flow

### 3.1 Dashboard Request Flow (Refactored)

```
1. Router receives request
   ↓
2. Handler.get_dashboard() called
   ↓
3. Check services initialized (BaseHandler method)
   ↓
4. Get watchlist from DAO
   ↓
5. For each ticker:
   a. _process_ticker_for_dashboard()
      - Fetch market data (async)
      - Fetch options chain (async)
      - _categorize_positions()
        * Calculate metrics for each position
        * Generate recommendations
      - _generate_signals()
        * Generate all strategy signals
   ↓
6. Return DashboardResponse
```

### 3.2 Add Ticker Flow (Refactored)

```
1. Router receives request
   ↓
2. Handler.add_ticker() called
   ↓
3. Check services initialized (BaseHandler method)
   ↓
4. Validate ticker format (ValidationUtils)
   ↓
5. Validate ticker exists (MarketDataService)
   ↓
6. Check if already in watchlist (DAO)
   ↓
7. Add to watchlist (DAO)
   ↓
8. Return success response
```

## 4. Error Handling Strategy

### 4.1 Error Hierarchy

```
BaseHandler._log_and_raise_error()
    ↓
Logs error with context
    ↓
Raises HTTPException with appropriate status
```

### 4.2 Service Initialization Checks

```
BaseHandler._check_services_initialized()
    ↓
Checks all required services
    ↓
Raises HTTPException if any missing
```

### 4.3 Validation Errors

```
ValidationUtils.validate_*()
    ↓
Validates input
    ↓
Raises HTTPException with 400 status if invalid
```

## 5. Testing Strategy

### 5.1 Unit Tests for BaseHandler

```python
def test_check_service_initialized_success():
    handler = BaseHandler()
    service = Mock()
    # Should not raise
    handler._check_service_initialized(service, "TestService")

def test_check_service_initialized_failure():
    handler = BaseHandler()
    with pytest.raises(HTTPException) as exc_info:
        handler._check_service_initialized(None, "TestService")
    assert exc_info.value.status_code == 500
    assert "TestService" in exc_info.value.detail
```

### 5.2 Unit Tests for ValidationUtils

```python
def test_validate_ticker_format_valid():
    result = ValidationUtils.validate_ticker_format("aapl")
    assert result == "AAPL"

def test_validate_ticker_format_invalid():
    with pytest.raises(HTTPException) as exc_info:
        ValidationUtils.validate_ticker_format("TOOLONG")
    assert exc_info.value.status_code == 400
```

### 5.3 Integration Tests for Refactored Handler

```python
@pytest.mark.asyncio
async def test_get_dashboard_with_positions():
    # Setup mocks
    mock_dao = Mock()
    mock_dao.get_watchlist.return_value = ["AAPL"]
    mock_dao.get_positions_for_ticker.return_value = [...]
    
    mock_service = Mock()
    mock_service.get_stock_data = AsyncMock(return_value=...)
    
    handler = FinanceHandler(
        finance_dao=mock_dao,
        market_data_service=mock_service,
        signal_generator_service=Mock()
    )
    
    result = await handler.get_dashboard()
    
    assert len(result.stocks) == 1
    assert result.stocks[0].ticker == "AAPL"
```

## 6. Migration Strategy

### 6.1 Phase 1: Foundation (No Breaking Changes)

1. Create `BaseHandler` class
2. Create `ValidationUtils` class
3. Add tests for new utilities
4. **No changes to existing handlers yet**

### 6.2 Phase 2: Handler Migration (One at a time)

1. Update `AuthHandler` to extend `BaseHandler`
2. Test thoroughly
3. Update `FinanceHandler` to extend `BaseHandler`
4. Test thoroughly
5. Update remaining handlers

### 6.3 Phase 3: Method Refactoring

1. Extract helper methods from `get_dashboard()`
2. Test each helper method
3. Update main method to use helpers
4. Verify integration tests pass

### 6.4 Phase 4: DAO Optimization

1. Update `get_all_positions()` to use pipeline
2. Add batch operations
3. Benchmark performance
4. Deploy and monitor

## 7. Performance Considerations

### 7.1 Redis Pipeline Benefits

**Before**:
- N network round trips for N positions
- ~1ms per round trip
- 100 positions = ~100ms

**After**:
- 2 network round trips (get IDs, get all data)
- ~2ms total
- 100 positions = ~2ms
- **50x improvement**

### 7.2 Method Extraction Impact

**Concern**: More method calls = slower?

**Reality**: 
- Method call overhead is negligible (~nanoseconds)
- Improved code organization enables better optimization
- Easier to identify bottlenecks
- **Net positive for performance**

## 8. Backward Compatibility

### 8.1 API Contracts

**No changes to**:
- Router endpoints
- Request/response models
- HTTP status codes
- Error message formats (improved but compatible)

### 8.2 Internal Contracts

**Changes to**:
- Handler constructors (add `super().__init__()`)
- Internal method signatures (new helper methods)
- Import statements (new utilities)

**Impact**: Internal only, no external API changes

## 9. Monitoring & Observability

### 9.1 Logging Improvements

**Before**:
```python
ctx = build_context()
ctx.logger.error(f"Failed: {e}")
```

**After**:
```python
self.ctx.logger.error(f"Operation failed: {e}")
# Consistent format, always includes context
```

### 9.2 Performance Metrics

**Track**:
- Dashboard generation time
- Position retrieval time
- Cache hit rates
- Error rates by handler

**Alert on**:
- Dashboard > 2 seconds
- Error rate > 1%
- Cache hit rate < 80%

## 10. Rollback Plan

### 10.1 If Issues Arise

1. **Revert commits** - All changes in feature branch
2. **Deploy previous version** - Known good state
3. **Investigate** - Review logs and metrics
4. **Fix and redeploy** - Address issues incrementally

### 10.2 Rollback Triggers

- Error rate increases > 5%
- Response time increases > 50%
- Any critical functionality broken
- Test failures in production

## 11. Documentation Updates

### 11.1 Code Documentation

- Add docstrings to all new classes/methods
- Update existing docstrings for refactored methods
- Add inline comments for complex logic

### 11.2 Steering Files

- Update `api-dependency-injection.md` with BaseHandler pattern
- Update `api-error-handling.md` with new utilities
- Update `api-context-management.md` with BaseHandler example

### 11.3 README Updates

- Document new utilities
- Update architecture diagrams
- Add migration guide for future handlers

## 12. Success Metrics

### 12.1 Code Quality

- ✅ No methods > 50 lines
- ✅ No repeated code blocks
- ✅ All handlers extend BaseHandler
- ✅ Consistent error handling

### 12.2 Performance

- ✅ Position retrieval < 10ms for 100 positions
- ✅ Dashboard generation < 2 seconds
- ✅ No N+1 query patterns

### 12.3 Maintainability

- ✅ 80%+ test coverage
- ✅ All public methods documented
- ✅ Consistent patterns across handlers

## 13. Future Enhancements

### 13.1 Not in Scope (But Documented)

- Async Redis client (requires library change)
- GraphQL API (different architecture)
- Microservices split (major refactor)
- Real-time WebSocket updates (new feature)

### 13.2 Follow-up Improvements

- Add request/response logging middleware
- Implement circuit breaker for external APIs
- Add distributed tracing
- Implement rate limiting per user

## 14. Correctness Properties

### 14.1 Property 1: Service Initialization

**Property**: All handler methods that require services MUST check initialization before use

**Validation**: 
- Unit tests verify `_check_services_initialized()` is called
- Integration tests verify HTTPException raised when service is None

### 14.2 Property 2: Error Logging

**Property**: All errors MUST be logged before raising HTTPException

**Validation**:
- Unit tests verify logger.error() called
- Integration tests check log output

### 14.3 Property 3: Ticker Normalization

**Property**: All ticker inputs MUST be normalized (uppercase, trimmed)

**Validation**:
- Unit tests verify normalization
- Property-based tests with random inputs

### 14.4 Property 4: Redis Atomicity

**Property**: Batch operations MUST be atomic (all succeed or all fail)

**Validation**:
- Unit tests with pipeline mocks
- Integration tests with Redis

### 14.5 Property 5: No Silent Failures

**Property**: No exceptions MUST be silently swallowed

**Validation**:
- Code review checklist
- Static analysis tools
- Test coverage reports
