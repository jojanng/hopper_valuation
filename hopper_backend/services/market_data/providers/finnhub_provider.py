import logging
import asyncio
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FinnhubProvider:
    """Provider for fetching market data from Finnhub API"""
    
    def __init__(self, api_key: str = None):
        self.name = "finnhub"
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        
        if not api_key:
            logger.warning("Finnhub API key not provided. This provider will be disabled.")
    
    async def get_current_price(self, symbol: str) -> float:
        """
        Get the latest stock price from Finnhub.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Current stock price
        """
        if not self.api_key:
            raise ValueError("Finnhub API key not provided")
        
        url = f"{self.base_url}/quote"
        headers = {"X-Finnhub-Token": self.api_key}
        params = {"symbol": symbol}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "c" not in data or data["c"] == 0:
                raise ValueError(f"No data found for symbol {symbol}")
            
            price = float(data["c"])  # Current price
            if price <= 0:
                raise ValueError(f"Invalid price for {symbol}")
                
            return price
    
    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> Dict:
        """
        Get historical price data from Finnhub.
        
        Args:
            symbol: Stock symbol
            period: Time period (e.g., 1d, 1mo, 1y, 5y)
            interval: Data interval (e.g., 1m, 5m, 1h, 1d)
            
        Returns:
            Dict: Historical data with dates as keys and OHLCV data as values
        """
        if not self.api_key:
            raise ValueError("Finnhub API key not provided")
        
        # Convert period to start and end dates
        end_date = datetime.now()
        
        # Map period to days
        period_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
            "10y": 3650,
            "ytd": (end_date - datetime(end_date.year, 1, 1)).days
        }
        
        days = period_map.get(period, 365)  # Default to 1 year
        start_date = end_date - timedelta(days=days)
        
        # Convert dates to UNIX timestamps
        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())
        
        # Map interval to resolution
        resolution_map = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "1h": "60",
            "1d": "D",
            "1wk": "W",
            "1mo": "M"
        }
        
        resolution = resolution_map.get(interval, "D")  # Default to daily
        
        url = f"{self.base_url}/stock/candle"
        headers = {"X-Finnhub-Token": self.api_key}
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": from_timestamp,
            "to": to_timestamp
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "s" not in data or data["s"] != "ok":
                raise ValueError(f"No historical data found for symbol {symbol}")
            
            # Convert to dictionary with dates as keys
            result = {}
            for i in range(len(data["t"])):
                date = datetime.fromtimestamp(data["t"][i])
                date_str = date.strftime('%Y-%m-%d')
                
                result[date_str] = {
                    "open": float(data["o"][i]),
                    "high": float(data["h"][i]),
                    "low": float(data["l"][i]),
                    "close": float(data["c"][i]),
                    "volume": int(data["v"][i])
                }
            
            return result
    
    async def get_historical_volatility(self, symbol: str, lookback: int = 252) -> float:
        """
        Calculate historical volatility from Finnhub data.
        
        Args:
            symbol: Stock symbol
            lookback: Number of trading days to look back
            
        Returns:
            float: Historical volatility (annualized)
        """
        import numpy as np
        
        if not self.api_key:
            raise ValueError("Finnhub API key not provided")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback * 1.5)  # Add buffer for weekends/holidays
        
        # Convert dates to UNIX timestamps
        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())
        
        url = f"{self.base_url}/stock/candle"
        headers = {"X-Finnhub-Token": self.api_key}
        params = {
            "symbol": symbol,
            "resolution": "D",  # Daily data
            "from": from_timestamp,
            "to": to_timestamp
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "s" not in data or data["s"] != "ok" or len(data.get("c", [])) < lookback:
                raise ValueError(f"Insufficient historical data for {symbol}")
            
            # Calculate daily returns
            prices = np.array(data["c"])[-lookback:]  # Use the most recent lookback days
            returns = np.log(prices[1:] / prices[:-1])
            
            # Calculate annualized volatility
            daily_volatility = np.std(returns)
            annualized_volatility = daily_volatility * np.sqrt(252)
            
            return float(annualized_volatility)
    
    async def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive financial data from Finnhub.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict: Financial data including balance sheet, income statement, etc.
        """
        if not self.api_key:
            raise ValueError("Finnhub API key not provided")
        
        headers = {"X-Finnhub-Token": self.api_key}
        
        async with httpx.AsyncClient() as client:
            # Get basic profile
            profile_url = f"{self.base_url}/stock/profile2"
            profile_params = {"symbol": symbol}
            
            profile_response = await client.get(profile_url, headers=headers, params=profile_params)
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            
            # Get quote for current price
            quote_url = f"{self.base_url}/quote"
            quote_params = {"symbol": symbol}
            
            quote_response = await client.get(quote_url, headers=headers, params=quote_params)
            quote_response.raise_for_status()
            quote_data = quote_response.json()
            
            # Get balance sheet
            bs_url = f"{self.base_url}/stock/financials-reported"
            bs_params = {"symbol": symbol, "statement": "bs"}
            
            bs_response = await client.get(bs_url, headers=headers, params=bs_params)
            bs_response.raise_for_status()
            bs_data = bs_response.json()
            
            # Get income statement
            is_url = f"{self.base_url}/stock/financials-reported"
            is_params = {"symbol": symbol, "statement": "ic"}
            
            is_response = await client.get(is_url, headers=headers, params=is_params)
            is_response.raise_for_status()
            is_data = is_response.json()
            
            # Get cash flow statement
            cf_url = f"{self.base_url}/stock/financials-reported"
            cf_params = {"symbol": symbol, "statement": "cf"}
            
            cf_response = await client.get(cf_url, headers=headers, params=cf_params)
            cf_response.raise_for_status()
            cf_data = cf_response.json()
            
            # Get basic metrics
            metrics_url = f"{self.base_url}/stock/metric"
            metrics_params = {"symbol": symbol, "metric": "all"}
            
            metrics_response = await client.get(metrics_url, headers=headers, params=metrics_params)
            metrics_response.raise_for_status()
            metrics_data = metrics_response.json()
            
            # Extract key metrics
            market_cap = profile_data.get("marketCapitalization", 0) * 1e6  # Convert from millions
            shares_outstanding = metrics_data.get("metric", {}).get("sharesOutstanding", 0) * 1e6  # Convert from millions
            current_price = quote_data.get("c", 0)
            
            # Extract balance sheet data
            balance_sheet_reports = bs_data.get("data", [])
            total_debt = 0
            cash_and_equivalents = 0
            
            if balance_sheet_reports:
                # Find the most recent annual report
                annual_reports = [r for r in balance_sheet_reports if r.get("form") == "10-K"]
                if annual_reports:
                    latest_bs = annual_reports[0].get("report", {}).get("bs", {})
                    
                    # Look for debt and cash in the report
                    for item in latest_bs:
                        if "debt" in item.get("concept", "").lower():
                            total_debt += float(item.get("value", 0))
                        
                        if "cash" in item.get("concept", "").lower() and "equivalent" in item.get("concept", "").lower():
                            cash_and_equivalents = float(item.get("value", 0))
            
            # Extract income statement data
            income_stmt_reports = is_data.get("data", [])
            net_income = 0
            ebitda = 0
            
            if income_stmt_reports:
                # Find the most recent annual report
                annual_reports = [r for r in income_stmt_reports if r.get("form") == "10-K"]
                if annual_reports:
                    latest_is = annual_reports[0].get("report", {}).get("ic", {})
                    
                    # Look for net income and EBITDA in the report
                    for item in latest_is:
                        if "net income" in item.get("concept", "").lower():
                            net_income = float(item.get("value", 0))
                        
                        if "ebitda" in item.get("concept", "").lower():
                            ebitda = float(item.get("value", 0))
            
            # Extract cash flow data
            cash_flow_reports = cf_data.get("data", [])
            fcf = None
            
            if cash_flow_reports:
                # Find the most recent annual report
                annual_reports = [r for r in cash_flow_reports if r.get("form") == "10-K"]
                if annual_reports:
                    latest_cf = annual_reports[0].get("report", {}).get("cf", {})
                    
                    operating_cash_flow = 0
                    capital_expenditures = 0
                    
                    # Look for operating cash flow and capital expenditures in the report
                    for item in latest_cf:
                        if "operating" in item.get("concept", "").lower() and "cash flow" in item.get("concept", "").lower():
                            operating_cash_flow = float(item.get("value", 0))
                        
                        if "capital expenditure" in item.get("concept", "").lower():
                            capital_expenditures = float(item.get("value", 0))
                    
                    fcf = operating_cash_flow - abs(capital_expenditures)
            
            # Calculate enterprise value
            enterprise_value = market_cap + total_debt - cash_and_equivalents
            
            # Get growth rates from metrics
            earnings_growth = metrics_data.get("metric", {}).get("epsGrowth", None)
            revenue_growth = metrics_data.get("metric", {}).get("revenueGrowth", None)
            
            # Construct the result
            return {
                'symbol': symbol,
                'price': current_price,
                'marketCap': market_cap,
                'sharesOutstanding': shares_outstanding,
                'totalDebt': total_debt,
                'cashAndEquivalents': cash_and_equivalents,
                'enterpriseValue': enterprise_value,
                'netIncome': net_income,
                'ebitda': ebitda,
                'freeCashFlow': fcf,
                'earningsGrowth': earnings_growth,
                'revenueGrowth': revenue_growth,
                'peRatio': metrics_data.get("metric", {}).get("peBasicExclExtraTTM", None),
                'balanceSheet': balance_sheet_reports,
                'incomeStatement': income_stmt_reports,
                'cashFlow': cash_flow_reports
            } 