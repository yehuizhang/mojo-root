---
inclusion: fileMatch
fileMatchPattern: '**/*.py'
---
# API Testing Patterns

## Testing Philosophy

Write tests that:
- Verify core business logic
- Test important edge cases
- Are maintainable and readable
- Run quickly
- Don't test framework code

## Test Organization

### Directory Structure

```
api/
├── handlers/
│   └── finance_handler.py
├── dao/
│   └── finance_dao.py
├── lib/
│   └── stock_tracking/
│       └── services/
│           └── signal_generator_service.py
└── test/
    ├── __init__.py
    ├── handlers/
    │   └── test_finance_handler.py
    ├── dao/
    │   └── test_finance_dao.py
    └── stock_tracking/
        └── test_signal_generator_service.py
```

### Test File Naming

- Prefix with `test_`: `test_finance_handler.py`
- Mirror source structure: `api/handlers/x.py` → `api/test/handlers/test_x.py`
- One test file per source file

## Unit Testing Patterns

### Testing Handlers with Mocks

```python
import pytest
from unittest.mock import Mock, patch
from api.handlers.finance_handler import FinanceHandler

def test_add_ticker_success():
    # Arrange
    mock_dao = Mock()
    mock_dao.ticker_in_watchlist.return_value = False
    mock_dao.add_to_watchlist.return_value = True
    
    mock_service = Mock()
    mock_service.validate_ticker.return_value = True
    
    handler = FinanceHandler(
        finance_dao=mock_dao,
        market_data_service=mock_service
    )
    
    # Act
    result = handler.add_ticker("AAPL")
    
    # Assert
    assert result["ticker"] == "AAPL"
    assert result["status"] == "added"
    mock_dao.add_to_watchlist.assert_called_once_with("AAPL")

def test_add_ticker_already_exists():
    # Arrange
    mock_dao = Mock()
    mock_dao.ticker_in_watchlist.return_value = True
    
    mock_service = Mock()
    mock_service.validate_ticker.return_value = True
    
    handler = FinanceHandler(
        finance_dao=mock_dao,
        market_data_service=mock_service
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        handler.add_ticker("AAPL")
    
    assert exc_info.value.status_code == 409
    assert "already in watchlist" in exc_info.value.detail
```

### Testing DAOs with Redis Mock

```python
import pytest
from unittest.mock import Mock, MagicMock
from api.dao.finance_dao import FinanceDAO

@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_mock = Mock()
    redis_mock.client = MagicMock()
    return redis_mock

def test_get_watchlist(mock_redis):
    # Arrange
    mock_redis.client.smembers.return_value = {"AAPL", "GOOGL", "MSFT"}
    
    dao = FinanceDAO(redis_client=mock_redis)
    
    # Act
    result = dao.get_watchlist()
    
    # Assert
    assert len(result) == 3
    assert "AAPL" in result
    mock_redis.client.smembers.assert_called_once_with("finance:watchlist")

def test_add_to_watchlist(mock_redis):
    # Arrange
    mock_redis.client.sadd.return_value = 1
    
    dao = FinanceDAO(redis_client=mock_redis)
    
    # Act
    result = dao.add_to_watchlist("AAPL")
    
    # Assert
    assert result is True
    mock_redis.client.sadd.assert_called_once_with("finance:watchlist", "AAPL")
```

### Testing Services with External APIs

```python
import pytest
from unittest.mock import Mock, AsyncMock
from api.lib.stock_tracking.services.market_data_service import MarketDataService

@pytest.mark.asyncio
async def test_get_stock_data_cache_hit():
    # Arrange
    mock_dao = Mock()
    mock_dao.get_cached_stock_data.return_value = {
        "ticker": "AAPL",
        "current_price": 150.0,
        "rsi": 55.0
    }
    
    service = MarketDataService(finance_dao=mock_dao)
    
    # Act
    result = await service.get_stock_data("AAPL")
    
    # Assert
    assert result.ticker == "AAPL"
    assert result.current_price == 150.0
    mock_dao.get_cached_stock_data.assert_called_once_with("AAPL")

@pytest.mark.asyncio
async def test_get_stock_data_cache_miss():
    # Arrange
    mock_dao = Mock()
    mock_dao.get_cached_stock_data.return_value = None
    mock_dao.cache_stock_data.return_value = True
    
    mock_client = Mock()
    mock_client.get_daily_bars.return_value = [
        Mock(close=150.0, high=152.0, low=148.0)
        for _ in range(252)
    ]
    
    service = MarketDataService(
        finance_dao=mock_dao,
        massive_client=mock_client
    )
    
    # Act
    result = await service.get_stock_data("AAPL")
    
    # Assert
    assert result.ticker == "AAPL"
    mock_client.get_daily_bars.assert_called_once()
    mock_dao.cache_stock_data.assert_called_once()
```

## Integration Testing

### Testing Router Endpoints

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_get_dashboard():
    # Act
    response = client.get("/finance/dashboard")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    assert "timestamp" in data

def test_add_ticker():
    # Act
    response = client.post("/finance/watchlist?ticker=AAPL")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["status"] == "added"

def test_add_invalid_ticker():
    # Act
    response = client.post("/finance/watchlist?ticker=INVALID")
    
    # Assert
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]
```

### Testing with Authentication

```python
def test_protected_endpoint_without_auth():
    # Act
    response = client.get("/internal/positions")
    
    # Assert
    assert response.status_code == 401

def test_protected_endpoint_with_auth():
    # Arrange
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Act
    response = client.get("/internal/positions", headers=headers)
    
    # Assert
    assert response.status_code == 200
```

## Fixtures and Test Utilities

### Pytest Fixtures

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_finance_dao():
    """Create mock FinanceDAO."""
    dao = Mock()
    dao.get_watchlist.return_value = ["AAPL", "GOOGL"]
    dao.ticker_in_watchlist.return_value = False
    dao.add_to_watchlist.return_value = True
    return dao

@pytest.fixture
def mock_market_service():
    """Create mock MarketDataService."""
    service = Mock()
    service.validate_ticker.return_value = True
    return service

@pytest.fixture
def finance_handler(mock_finance_dao, mock_market_service):
    """Create FinanceHandler with mocked dependencies."""
    return FinanceHandler(
        finance_dao=mock_finance_dao,
        market_data_service=mock_market_service
    )

# Use fixtures in tests
def test_with_fixtures(finance_handler):
    result = finance_handler.add_ticker("AAPL")
    assert result["status"] == "added"
```

### Test Data Builders

```python
from datetime import date, datetime
from api.lib.stock_tracking.models.position_models import PositionCreate

def create_test_position(
    ticker: str = "AAPL",
    position_type: str = "stock",
    quantity: int = 100,
    purchase_price: float = 150.0,
) -> PositionCreate:
    """Create test position with defaults."""
    return PositionCreate(
        ticker=ticker,
        position_type=position_type,
        quantity=quantity,
        purchase_price=purchase_price,
        transaction_date=date.today(),
    )

def create_test_option_position(
    ticker: str = "AAPL",
    strike: float = 150.0,
    expiration: date = None,
) -> PositionCreate:
    """Create test option position."""
    return PositionCreate(
        ticker=ticker,
        position_type="option",
        option_type="call",
        quantity=1,
        strike=strike,
        expiration=expiration or date(2025, 12, 31),
        premium=5.0,
        transaction_date=date.today(),
    )

# Use in tests
def test_position_creation():
    position = create_test_position(ticker="GOOGL", quantity=50)
    assert position.ticker == "GOOGL"
    assert position.quantity == 50
```

## Testing Async Code

### Async Test Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_handler_method():
    # Arrange
    mock_dao = Mock()
    handler = FinanceHandler(finance_dao=mock_dao)
    
    # Act
    result = await handler.get_dashboard()
    
    # Assert
    assert result is not None
```

### Mocking Async Functions

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_async_mock():
    # Arrange
    mock_service = Mock()
    mock_service.get_stock_data = AsyncMock(
        return_value=StockData(ticker="AAPL", current_price=150.0)
    )
    
    # Act
    result = await mock_service.get_stock_data("AAPL")
    
    # Assert
    assert result.ticker == "AAPL"
```

## Testing Edge Cases

### Boundary Conditions

```python
def test_rsi_boundary_conditions():
    service = SignalGeneratorService()
    
    # Test RSI at exact boundaries
    stock_data_30 = create_stock_data(rsi=30.0)
    stock_data_45 = create_stock_data(rsi=45.0)
    stock_data_29 = create_stock_data(rsi=29.9)
    
    signal_30 = service.generate_csp_signal(stock_data_30, [])
    signal_45 = service.generate_csp_signal(stock_data_45, [])
    signal_29 = service.generate_csp_signal(stock_data_29, [])
    
    assert signal_30.conditions_met["good_rsi"] is True
    assert signal_45.conditions_met["good_rsi"] is True
    assert signal_29.conditions_met["good_rsi"] is False
```

### Null/Empty Handling

```python
def test_empty_watchlist():
    mock_dao = Mock()
    mock_dao.get_watchlist.return_value = []
    
    handler = FinanceHandler(finance_dao=mock_dao)
    result = handler.get_watchlist()
    
    assert result == []

def test_none_earnings_date():
    stock_data = create_stock_data(earnings_date=None)
    service = SignalGeneratorService()
    
    signal = service.generate_csp_signal(stock_data, [])
    
    # Should handle None gracefully
    assert signal.conditions_met["safe_earnings"] is True
```

### Error Conditions

```python
def test_invalid_ticker():
    mock_service = Mock()
    mock_service.validate_ticker.return_value = False
    
    handler = FinanceHandler(market_data_service=mock_service)
    
    with pytest.raises(HTTPException) as exc_info:
        handler.add_ticker("INVALID")
    
    assert exc_info.value.status_code == 400

def test_dao_failure():
    mock_dao = Mock()
    mock_dao.add_to_watchlist.return_value = False
    
    mock_service = Mock()
    mock_service.validate_ticker.return_value = True
    
    handler = FinanceHandler(
        finance_dao=mock_dao,
        market_data_service=mock_service
    )
    
    with pytest.raises(HTTPException) as exc_info:
        handler.add_ticker("AAPL")
    
    assert exc_info.value.status_code == 500
```

## Test Coverage

### Running Tests with Coverage

```bash
# Run all tests with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest api/test/handlers/test_finance_handler.py

# Run with verbose output
pytest -v

# Run only failed tests
pytest --lf
```

### Coverage Goals

- **Handlers**: 80%+ coverage (focus on business logic)
- **DAOs**: 70%+ coverage (focus on error handling)
- **Services**: 80%+ coverage (focus on calculations)
- **Routers**: 60%+ coverage (mostly integration tests)

## Common Testing Mistakes

### ❌ Testing Framework Code

```python
# BAD - testing FastAPI's dependency injection
def test_dependency_injection():
    handler = Depends(get_finance_handler)
    assert handler is not None

# GOOD - test business logic
def test_add_ticker_logic():
    handler = FinanceHandler(mock_dao, mock_service)
    result = handler.add_ticker("AAPL")
    assert result["status"] == "added"
```

### ❌ Not Isolating Tests

```python
# BAD - tests depend on each other
def test_add_ticker():
    handler.add_ticker("AAPL")

def test_get_watchlist():
    # Assumes AAPL was added in previous test
    watchlist = handler.get_watchlist()
    assert "AAPL" in watchlist

# GOOD - each test is independent
def test_add_ticker():
    mock_dao = Mock()
    handler = FinanceHandler(finance_dao=mock_dao)
    handler.add_ticker("AAPL")

def test_get_watchlist():
    mock_dao = Mock()
    mock_dao.get_watchlist.return_value = ["AAPL"]
    handler = FinanceHandler(finance_dao=mock_dao)
    watchlist = handler.get_watchlist()
    assert "AAPL" in watchlist
```

### ❌ Over-Mocking

```python
# BAD - mocking everything, not testing anything
def test_calculate_rsi():
    mock_service = Mock()
    mock_service.calculate_rsi.return_value = 55.0
    
    result = mock_service.calculate_rsi([100, 101, 102])
    assert result == 55.0  # Just testing the mock

# GOOD - test actual calculation
def test_calculate_rsi():
    service = TechnicalAnalysisService()
    prices = [100, 101, 102, 103, 102, 101, 100]
    
    result = service.calculate_rsi(prices)
    assert 40 < result < 60  # Test actual logic
```

## Test Checklist

When writing tests:

- [ ] Test happy path
- [ ] Test error conditions
- [ ] Test boundary conditions
- [ ] Test null/empty inputs
- [ ] Use descriptive test names
- [ ] Arrange-Act-Assert pattern
- [ ] Mock external dependencies
- [ ] Don't test framework code
- [ ] Keep tests independent
- [ ] Use fixtures for common setup
