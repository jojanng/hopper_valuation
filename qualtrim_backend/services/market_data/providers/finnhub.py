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
    
    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> List[Dict]:
        """
        Get historical price data from Finnhub.
        
        Args:
            symbol: Stock symbol
            period: Time period (e.g., 1d, 1mo, 1y, 5y)
            interval: Data interval (e.g., 1m, 5m, 1h, 1d)
            
        Returns:
            List[Dict]: Historical data as a list of dictionaries
        """
        if not self.api_key:
            raise ValueError("Finnhub API key not provided")
        
        # Map period to start and end dates
        end_date = datetime.now()
        
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        elif period == "5y":
            start_date = end_date - timedelta(days=1825)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        # Map interval to Finnhub resolution
        if interval == "1m":
            resolution = "1"
        elif interval == "5m":
            resolution = "5"
        elif interval == "15m":
            resolution = "15"
        elif interval == "30m":
            resolution = "30"
        elif interval == "60m" or interval == "1h":
            resolution = "60"
        elif interval == "1d":
            resolution = "D"
        elif interval == "1wk":
            resolution = "W"
        elif interval == "1mo":
            resolution = "M"
        else:
            resolution = "D"  # Default to daily
        
        # Convert dates to UNIX timestamps
        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())
        
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
                raise ValueError(f"No historical data found for {symbol}")
            
            # Convert to list of dictionaries
            result = []
            for i in range(len(data["t"])):
                timestamp = data["t"][i]
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                result.append({
                    'date': date_str,
                    'open': float(data["o"][i]),
                    'high': float(data["h"][i]),
                    'low': float(data["l"][i]),
                    'close': float(data["c"][i]),
                    'volume': int(data["v"][i])
                })
            
            return result
    
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