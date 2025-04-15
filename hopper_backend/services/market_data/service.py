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
    
    async def get_historical_fcf(self, symbol: str, years: int = 5) -> List[float]:
        """
        Get historical free cash flow data for the last several years.
        
        Args:
            symbol: Stock symbol
            years: Number of years of historical data to fetch
            
        Returns:
            List[float]: List of historical FCF values (oldest to newest)
        """
        try:
            # Try to get data from provider
            provider_name = self.default_provider
            
            if provider_name == "yfinance":
                # YFinance doesn't have a direct method for historical FCF,
                # so we calculate it from historical cash flow statements
                return await self.providers[provider_name].get_historical_fcf(symbol, years)
            else:
                # Try other providers
                for name, provider in self.providers.items():
                    try:
                        if hasattr(provider, 'get_historical_fcf'):
                            return await provider.get_historical_fcf(symbol, years)
                    except Exception as e:
                        logger.warning(f"Error getting historical FCF from {name}: {str(e)}")
            
            # If we get here, no provider could provide the data
            logger.warning(f"Could not get historical FCF for {symbol}. Will use regular growth estimate.")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching historical FCF for {symbol}: {str(e)}")
            return []
    
    async def get_risk_free_rate(self) -> float:
        """
        Get the current risk-free rate (10-year Treasury yield).
        
        Returns:
            float: Current risk-free rate as a decimal (e.g., 0.035 for 3.5%)
        """
        try:
            # Try to get data from provider
            provider_name = self.default_provider
            
            if provider_name == "yfinance":
                # For YFinance, use the 10-year Treasury yield (^TNX)
                return await self.providers[provider_name].get_risk_free_rate()
            else:
                # Try other providers
                for name, provider in self.providers.items():
                    try:
                        if hasattr(provider, 'get_risk_free_rate'):
                            return await provider.get_risk_free_rate()
                    except Exception as e:
                        logger.warning(f"Error getting risk-free rate from {name}: {str(e)}")
            
            # If we get here, no provider could provide the data
            # Return a reasonable default
            logger.warning("Could not get risk-free rate. Using default of 3.5%.")
            return 0.035
            
        except Exception as e:
            logger.error(f"Error fetching risk-free rate: {str(e)}")
            return 0.035
    
    async def get_industry_growth_rate(self, symbol: str) -> float:
        """
        Get the average growth rate for the industry the company belongs to.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Industry growth rate as a decimal
        """
        try:
            # Try to get data from provider
            provider_name = self.default_provider
            
            if provider_name == "yfinance":
                # For YFinance, try to get industry peers and calculate average growth
                return await self.providers[provider_name].get_industry_growth_rate(symbol)
            else:
                # Try other providers
                for name, provider in self.providers.items():
                    try:
                        if hasattr(provider, 'get_industry_growth_rate'):
                            return await provider.get_industry_growth_rate(symbol)
                    except Exception as e:
                        logger.warning(f"Error getting industry growth from {name}: {str(e)}")
            
            # If we get here, no provider could provide the data
            # Return a reasonable default based on overall market
            logger.warning(f"Could not get industry growth rate for {symbol}. Using default of 3%.")
            return 0.03
            
        except Exception as e:
            logger.error(f"Error fetching industry growth rate for {symbol}: {str(e)}")
            return 0.03
    
    async def get_cost_of_debt(self, symbol: str) -> Optional[float]:
        """
        Calculate the company's cost of debt based on interest expenses and total debt.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Cost of debt as a decimal, or None if not available
        """
        try:
            # Get financial data
            financial_data = await self.get_financial_data(symbol)
            
            # Check if the required data is available
            interest_expense = financial_data.get("interestExpense")
            total_debt = financial_data.get("totalDebt")
            
            if interest_expense and total_debt and total_debt > 0:
                # Calculate cost of debt = Interest Expense / Total Debt
                cost_of_debt = abs(interest_expense) / total_debt
                
                # Apply reasonable bounds (1% to 15%)
                cost_of_debt = max(min(cost_of_debt, 0.15), 0.01)
                
                return cost_of_debt
            else:
                # If data is missing, return None
                logger.warning(f"Could not calculate cost of debt for {symbol} due to missing data.")
                return None
            
        except Exception as e:
            logger.error(f"Error calculating cost of debt for {symbol}: {str(e)}")
            return None
    
    async def get_debt_to_equity(self, symbol: str) -> Optional[float]:
        """
        Get the company's debt-to-equity ratio.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Debt-to-equity ratio, or None if not available
        """
        try:
            # Get financial data
            financial_data = await self.get_financial_data(symbol)
            
            # Check if the required data is available
            total_debt = financial_data.get("totalDebt")
            total_equity = financial_data.get("totalStockholderEquity")
            
            if total_debt is not None and total_equity is not None and total_equity > 0:
                # Calculate debt-to-equity ratio
                debt_to_equity = total_debt / total_equity
                
                # Apply reasonable bounds (0 to 5)
                debt_to_equity = max(min(debt_to_equity, 5.0), 0.0)
                
                return debt_to_equity
            else:
                # If data is missing, return None
                logger.warning(f"Could not calculate debt-to-equity ratio for {symbol} due to missing data.")
                return None
            
        except Exception as e:
            logger.error(f"Error calculating debt-to-equity ratio for {symbol}: {str(e)}")
            return None
    
    async def get_historical_metrics(self, symbol: str) -> Dict[str, Dict]:
        """
        Get historical financial metrics.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict[str, Dict]: Historical metrics with dates as keys
        """
        try:
            # Try to get data from YFinance first
            if "yfinance" in self.providers:
                try:
                    return await self.providers["yfinance"].get_historical_metrics(symbol)
                except Exception as e:
                    logger.warning(f"Error getting historical metrics from YFinance: {str(e)}")
            
            # Try Finnhub as fallback
            if "finnhub" in self.providers:
                try:
                    return await self.providers["finnhub"].get_historical_metrics(symbol)
                except Exception as e:
                    logger.warning(f"Error getting historical metrics from Finnhub: {str(e)}")
            
            # If we get here, no provider could provide the data
            logger.warning(f"Could not get historical metrics for {symbol}. Using current metrics.")
            
            # Get current financial data as fallback
            financial_data = await self.get_financial_data(symbol)
            historical_data = await self.get_historical_data(symbol, period="5y")
            
            # Create a dict with the same metrics for all dates
            result = {}
            for date in historical_data.keys():
                result[date] = {
                    'sharesOutstanding': financial_data.get('sharesOutstanding'),
                    'netIncome': financial_data.get('netIncome'),
                    'ebitda': financial_data.get('ebitda'),
                    'totalDebt': financial_data.get('totalDebt'),
                    'cashAndEquivalents': financial_data.get('cashAndEquivalents')
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching historical metrics for {symbol}: {str(e)}")
            return {} 