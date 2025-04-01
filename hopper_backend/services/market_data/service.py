import logging
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import asyncio

# Import provider modules
from .providers.yfinance_provider import YFinanceProvider
from .providers.finnhub_provider import FinnhubProvider

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Service for fetching and processing market data from multiple sources.
    Uses a fallback strategy to ensure data availability.
    """
    
    def __init__(self, cache_service=None, config=None):
        """
        Initialize the Market Data service.
        
        Args:
            cache_service: Optional cache service for storing results
            config: Optional configuration object
        """
        self.cache_service = cache_service
        self.config = config
        
        # Initialize providers
        self.providers = {}
        
        # Always initialize YFinance provider as it doesn't require an API key
        self.providers["yfinance"] = YFinanceProvider()
        
        # Initialize Finnhub provider if API key is available
        finnhub_api_key = None
        if config and hasattr(config, "market_data") and hasattr(config.market_data, "finnhub_api_key"):
            finnhub_api_key = config.market_data.finnhub_api_key
        
        if finnhub_api_key:
            self.providers["finnhub"] = FinnhubProvider(api_key=finnhub_api_key)
        
        # Set default provider
        self.default_provider = "yfinance"
        if config and hasattr(config, "market_data") and hasattr(config.market_data, "default_provider"):
            if config.market_data.default_provider in self.providers:
                self.default_provider = config.market_data.default_provider
    
    async def get_current_price(self, symbol: str, provider: str = None, fallback: bool = True) -> float:
        """
        Get the latest stock price.
        
        Args:
            symbol: Stock symbol
            provider: Specific provider to use (optional)
            fallback: Whether to try other providers if the first one fails
            
        Returns:
            float: Current stock price
        """
        # Use specified provider or default
        provider_name = provider if provider in self.providers else self.default_provider
        
        try:
            # Try to get price from the specified provider
            price = await self.providers[provider_name].get_current_price(symbol)
            return price
        except Exception as e:
            logger.warning(f"Error getting price from {provider_name}: {str(e)}")
            
            # If fallback is enabled, try other providers
            if fallback:
                for name, provider_instance in self.providers.items():
                    if name != provider_name:
                        try:
                            price = await provider_instance.get_current_price(symbol)
                            logger.info(f"Successfully got price from fallback provider {name}")
                            return price
                        except Exception as fallback_error:
                            logger.warning(f"Fallback provider {name} also failed: {str(fallback_error)}")
            
            # If fallback is disabled, re-raise the original exception
            if not fallback:
                raise e
            
            # If we get here, all providers failed
            raise ValueError(f"Failed to get price for {symbol} from any provider")
    
    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> Dict:
        """
        Get historical price data.
        
        Args:
            symbol: Stock symbol
            period: Time period (e.g., 1d, 1mo, 1y, 5y)
            interval: Data interval (e.g., 1m, 5m, 1h, 1d)
            
        Returns:
            Dict: Historical data
        """
        # YFinance is the most reliable for historical data
        try:
            return await self.providers["yfinance"].get_historical_data(symbol, period, interval)
        except Exception as e:
            logger.warning(f"Error getting historical data from YFinance: {str(e)}")
            
            # Try Finnhub if available
            if "finnhub" in self.providers:
                try:
                    return await self.providers["finnhub"].get_historical_data(symbol, period, interval)
                except Exception as fallback_error:
                    logger.warning(f"Fallback provider Finnhub also failed: {str(fallback_error)}")
            
            # If we get here, all providers failed
            raise ValueError(f"Failed to get historical data for {symbol} from any provider")
    
    async def get_historical_volatility(self, symbol: str, lookback: int = 252) -> float:
        """
        Calculate historical volatility.
        
        Args:
            symbol: Stock symbol
            lookback: Number of trading days to look back
            
        Returns:
            float: Historical volatility (annualized)
        """
        # YFinance is the most reliable for historical data
        try:
            return await self.providers["yfinance"].get_historical_volatility(symbol, lookback)
        except Exception as e:
            logger.warning(f"Error calculating volatility from YFinance: {str(e)}")
            
            # Try Finnhub if available
            if "finnhub" in self.providers:
                try:
                    return await self.providers["finnhub"].get_historical_volatility(symbol, lookback)
                except Exception as fallback_error:
                    logger.warning(f"Fallback provider Finnhub also failed: {str(fallback_error)}")
            
            # If we get here, all providers failed
            raise ValueError(f"Failed to calculate volatility for {symbol} from any provider")
    
    async def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive financial data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict: Financial data including balance sheet, income statement, etc.
        """
        # YFinance is the most reliable for financial data
        try:
            return await self.providers["yfinance"].get_financial_data(symbol)
        except Exception as e:
            logger.warning(f"Error getting financial data from YFinance: {str(e)}")
            
            # Try Finnhub if available
            if "finnhub" in self.providers:
                try:
                    return await self.providers["finnhub"].get_financial_data(symbol)
                except Exception as fallback_error:
                    logger.warning(f"Fallback provider Finnhub also failed: {str(fallback_error)}")
            
            # If we get here, all providers failed
            raise ValueError(f"Failed to get financial data for {symbol} from any provider")
    
    async def get_analyst_growth_estimates(self, symbol: str) -> float:
        """
        Get growth estimates from analyst forecasts.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Growth rate estimate
        """
        try:
            # Get financial data which includes growth estimates
            financial_data = await self.get_financial_data(symbol)
            
            # Get earnings growth estimates
            next_5y_growth = financial_data.get('earningsGrowth5Year')
            next_year_growth = financial_data.get('earningsGrowthNextYear')
            current_year_growth = financial_data.get('earningsGrowthCurrentYear')
            
            # If 5-year estimate available, use it
            if next_5y_growth is not None and next_5y_growth > -1:
                return next_5y_growth
            
            # If not, use weighted average of next year and current year
            if next_year_growth is not None and current_year_growth is not None:
                if next_year_growth > -1 and current_year_growth > -1:
                    return (next_year_growth * 0.6) + (current_year_growth * 0.4)
            
            # If still no valid growth rate, use revenue growth estimates
            revenue_growth = financial_data.get('revenueGrowth')
            if revenue_growth is not None and revenue_growth > -1:
                return revenue_growth
            
            # Default conservative growth rate
            return 0.05  # 5% default growth
        except Exception as e:
            logger.warning(f"Error getting growth estimates for {symbol}: {str(e)}")
            return 0.05  # Default to 5% if any error occurs
    
    async def get_free_cash_flow(self, symbol: str) -> float:
        """
        Get the latest free cash flow.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Free cash flow
        """
        try:
            financial_data = await self.get_financial_data(symbol)
            fcf = financial_data.get('freeCashFlow')
            
            if fcf is None:
                # If FCF not directly available, calculate from cash flow statement
                cash_flow = financial_data.get('cashFlow', {})
                if cash_flow:
                    # Get the most recent year
                    latest_year = list(cash_flow.keys())[0] if cash_flow else None
                    
                    if latest_year:
                        operating_cash_flow = cash_flow[latest_year].get('Operating Cash Flow', 0)
                        capital_expenditures = cash_flow[latest_year].get('Capital Expenditures', 0)
                        
                        # Capital expenditures are typically negative
                        fcf = operating_cash_flow + capital_expenditures
            
            return fcf if fcf is not None else 0.0
        except Exception as e:
            logger.warning(f"Error getting free cash flow for {symbol}: {str(e)}")
            return 0.0
    
    async def get_available_symbols(self) -> List[str]:
        """
        Get a list of available symbols from the market data providers.
        
        Returns:
            List[str]: List of available symbols
        """
        try:
            # Try to get symbols from the default provider
            symbols = await self.providers[self.default_provider].get_available_symbols()
            return symbols
        except Exception as e:
            logger.error(f"Error getting symbols from {self.default_provider}: {str(e)}")
            # Return a basic list of common symbols as fallback
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'PLTR', 'ASML', 
                   'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'INTC', 'VZ', 'ADBE', 
                   'NFLX', 'CSCO', 'PFE', 'CRM', 'ABT', 'KO', 'PEP', 'NKE', 'T', 'MRK', 'DIS', 'VOO'] 