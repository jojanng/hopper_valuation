"""
Tests for the MarketDataService.

This module contains tests for the MarketDataService class.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from hopper_backend.services.market_data.service import MarketDataService
from hopper_backend.services.market_data.providers.yfinance_provider import YFinanceProvider
from hopper_backend.services.market_data.providers.finnhub_provider import FinnhubProvider

# Test data
TEST_SYMBOL = "AAPL"
TEST_PRICE = 150.0
TEST_VOLATILITY = 0.25
TEST_FINANCIAL_DATA = {
    "dividendYield": 0.5,  # 0.5%
    "freeCashFlow": 100000000000,  # $100B
    "beta": 1.2
}

@pytest.fixture
def mock_yfinance_provider():
    """Create a mock YFinanceProvider."""
    provider = MagicMock(spec=YFinanceProvider)
    
    # Set up async method mocks
    async def mock_get_current_price(symbol):
        assert symbol == TEST_SYMBOL
        return TEST_PRICE
    
    async def mock_get_historical_volatility(symbol, lookback=252):
        assert symbol == TEST_SYMBOL
        return TEST_VOLATILITY
    
    async def mock_get_financial_data(symbol):
        assert symbol == TEST_SYMBOL
        return TEST_FINANCIAL_DATA
    
    provider.get_current_price.side_effect = mock_get_current_price
    provider.get_historical_volatility.side_effect = mock_get_historical_volatility
    provider.get_financial_data.side_effect = mock_get_financial_data
    
    return provider

@pytest.fixture
def mock_finnhub_provider():
    """Create a mock FinnhubProvider."""
    provider = MagicMock(spec=FinnhubProvider)
    
    # Set up async method mocks
    async def mock_get_current_price(symbol):
        assert symbol == TEST_SYMBOL
        return TEST_PRICE + 0.5  # Slightly different price
    
    provider.get_current_price.side_effect = mock_get_current_price
    
    # Other methods not implemented
    provider.get_historical_volatility.side_effect = NotImplementedError
    provider.get_financial_data.side_effect = NotImplementedError
    
    return provider

@pytest.fixture
def market_data_service(mock_yfinance_provider, mock_finnhub_provider):
    """Create a MarketDataService with mock providers."""
    with patch("hopper_backend.services.market_data.service.YFinanceProvider", return_value=mock_yfinance_provider), \
         patch("hopper_backend.services.market_data.service.FinnhubProvider", return_value=mock_finnhub_provider):
        service = MarketDataService()
        # Manually set providers for testing
        service.providers = {
            "yfinance": mock_yfinance_provider,
            "finnhub": mock_finnhub_provider
        }
        service.default_provider = "yfinance"
        return service

@pytest.mark.asyncio
async def test_get_current_price_default_provider(market_data_service, mock_yfinance_provider):
    """Test getting current price with default provider."""
    price = await market_data_service.get_current_price(TEST_SYMBOL)
    assert price == TEST_PRICE
    mock_yfinance_provider.get_current_price.assert_called_once_with(TEST_SYMBOL)

@pytest.mark.asyncio
async def test_get_current_price_specific_provider(market_data_service, mock_finnhub_provider):
    """Test getting current price with specific provider."""
    price = await market_data_service.get_current_price(TEST_SYMBOL, provider="finnhub")
    assert price == TEST_PRICE + 0.5
    mock_finnhub_provider.get_current_price.assert_called_once_with(TEST_SYMBOL)

@pytest.mark.asyncio
async def test_get_historical_volatility(market_data_service, mock_yfinance_provider):
    """Test getting historical volatility."""
    volatility = await market_data_service.get_historical_volatility(TEST_SYMBOL)
    assert volatility == TEST_VOLATILITY
    mock_yfinance_provider.get_historical_volatility.assert_called_once_with(TEST_SYMBOL, 252)

@pytest.mark.asyncio
async def test_get_financial_data(market_data_service, mock_yfinance_provider):
    """Test getting financial data."""
    data = await market_data_service.get_financial_data(TEST_SYMBOL)
    assert data == TEST_FINANCIAL_DATA
    mock_yfinance_provider.get_financial_data.assert_called_once_with(TEST_SYMBOL)

@pytest.mark.asyncio
async def test_provider_fallback(market_data_service, mock_yfinance_provider, mock_finnhub_provider):
    """Test provider fallback mechanism."""
    # Make the default provider fail
    mock_yfinance_provider.get_current_price.side_effect = Exception("Provider failed")
    
    # Service should fall back to another provider
    price = await market_data_service.get_current_price(TEST_SYMBOL, fallback=True)
    assert price == TEST_PRICE + 0.5
    mock_yfinance_provider.get_current_price.assert_called_once_with(TEST_SYMBOL)
    mock_finnhub_provider.get_current_price.assert_called_once_with(TEST_SYMBOL)

@pytest.mark.asyncio
async def test_no_fallback_raises_exception(market_data_service, mock_yfinance_provider):
    """Test that no fallback raises the original exception."""
    # Make the default provider fail
    mock_yfinance_provider.get_current_price.side_effect = Exception("Provider failed")
    
    # Service should not fall back and should raise the exception
    with pytest.raises(Exception, match="Provider failed"):
        await market_data_service.get_current_price(TEST_SYMBOL, fallback=False)
    
    mock_yfinance_provider.get_current_price.assert_called_once_with(TEST_SYMBOL) 