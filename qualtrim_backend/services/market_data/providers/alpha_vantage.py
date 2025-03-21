import logging
import asyncio
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AlphaVantageProvider:
    """Provider for fetching market data from Alpha Vantage API"""
    
    def __init__(self, api_key: str = None):
        self.name = "alpha_vantage"
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        
        if not api_key:
            logger.warning("Alpha Vantage API key not provided. This provider will be disabled.")
    
    async def get_current_price(self, symbol: str) -> float:
        """
        Get the latest stock price from Alpha Vantage.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Current stock price
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not provided")
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Global Quote" not in data or not data["Global Quote"]:
                raise ValueError(f"No data found for symbol {symbol}")
            
            price = float(data["Global Quote"]["05. price"])
            if price <= 0:
                raise ValueError(f"Invalid price for {symbol}")
                
            return price
    
    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> List[Dict]:
        """
        Get historical price data from Alpha Vantage.
        
        Args:
            symbol: Stock symbol
            period: Time period (e.g., 1d, 1mo, 1y, 5y)
            interval: Data interval (e.g., 1m, 5m, 1h, 1d)
            
        Returns:
            List[Dict]: Historical data as a list of dictionaries
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not provided")
        
        # Map period and interval to Alpha Vantage parameters
        function = "TIME_SERIES_DAILY_ADJUSTED"
        output_size = "compact"  # Default to last 100 data points
        
        # If period is longer than 100 days, use full output
        if period in ["1y", "2y", "5y"]:
            output_size = "full"
        
        # If interval is intraday, use appropriate function
        if interval in ["1m", "5m", "15m", "30m", "60m"]:
            function = "TIME_SERIES_INTRADAY"
            interval_param = interval.replace("m", "min")
        else:
            interval_param = None
        
        params = {
            "function": function,
            "symbol": symbol,
            "outputsize": output_size,
            "apikey": self.api_key
        }
        
        if interval_param:
            params["interval"] = interval_param
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract time series data
            time_series_key = None
            for key in data.keys():
                if "Time Series" in key:
                    time_series_key = key
                    break
            
            if not time_series_key or not data[time_series_key]:
                raise ValueError(f"No historical data found for {symbol}")
            
            # Convert to list of dictionaries
            result = []
            for date, values in data[time_series_key].items():
                result.append({
                    'date': date,
                    'open': float(values.get("1. open", 0)),
                    'high': float(values.get("2. high", 0)),
                    'low': float(values.get("3. low", 0)),
                    'close': float(values.get("4. close", 0)),
                    'volume': int(values.get("6. volume", 0))
                })
            
            # Sort by date
            result.sort(key=lambda x: x['date'])
            
            return result
    
    async def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive financial data from Alpha Vantage.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict: Financial data including balance sheet, income statement, etc.
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not provided")
        
        # We need to make multiple API calls to get all the data
        # 1. Overview for general info
        # 2. Balance Sheet
        # 3. Income Statement
        # 4. Cash Flow
        
        async with httpx.AsyncClient() as client:
            # Get company overview
            overview_params = {
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            overview_response = await client.get(self.base_url, params=overview_params)
            overview_response.raise_for_status()
            overview_data = overview_response.json()
            
            if not overview_data or "Symbol" not in overview_data:
                raise ValueError(f"No overview data found for {symbol}")
            
            # Get balance sheet
            balance_sheet_params = {
                "function": "BALANCE_SHEET",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            balance_sheet_response = await client.get(self.base_url, params=balance_sheet_params)
            balance_sheet_response.raise_for_status()
            balance_sheet_data = balance_sheet_response.json()
            
            # Get income statement
            income_stmt_params = {
                "function": "INCOME_STATEMENT",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            income_stmt_response = await client.get(self.base_url, params=income_stmt_params)
            income_stmt_response.raise_for_status()
            income_stmt_data = income_stmt_response.json()
            
            # Get cash flow
            cash_flow_params = {
                "function": "CASH_FLOW",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            cash_flow_response = await client.get(self.base_url, params=cash_flow_params)
            cash_flow_response.raise_for_status()
            cash_flow_data = cash_flow_response.json()
            
            # Extract key metrics
            market_cap = float(overview_data.get("MarketCapitalization", 0))
            shares_outstanding = float(overview_data.get("SharesOutstanding", 0))
            current_price = await self.get_current_price(symbol)
            
            # Get balance sheet data
            balance_sheet_reports = balance_sheet_data.get("annualReports", [])
            total_debt = 0
            cash_and_equivalents = 0
            
            if balance_sheet_reports:
                latest_bs = balance_sheet_reports[0]
                total_debt = float(latest_bs.get("totalLongTermDebt", 0))
                cash_and_equivalents = float(latest_bs.get("cashAndCashEquivalentsAtCarryingValue", 0))
            
            # Get income statement data
            income_stmt_reports = income_stmt_data.get("annualReports", [])
            net_income = 0
            ebitda = 0
            
            if income_stmt_reports:
                latest_is = income_stmt_reports[0]
                net_income = float(latest_is.get("netIncome", 0))
                ebitda = float(latest_is.get("ebitda", 0))
            
            # Get cash flow data
            cash_flow_reports = cash_flow_data.get("annualReports", [])
            fcf = None
            
            if cash_flow_reports:
                latest_cf = cash_flow_reports[0]
                operating_cash_flow = float(latest_cf.get("operatingCashflow", 0))
                capital_expenditures = float(latest_cf.get("capitalExpenditures", 0))
                fcf = operating_cash_flow - abs(capital_expenditures)
            
            # Calculate enterprise value
            enterprise_value = market_cap + total_debt - cash_and_equivalents
            
            # Get growth rates
            earnings_growth = None
            revenue_growth = None
            
            if len(income_stmt_reports) >= 2:
                current_earnings = float(income_stmt_reports[0].get("netIncome", 0))
                prev_earnings = float(income_stmt_reports[1].get("netIncome", 0))
                
                if prev_earnings != 0:
                    earnings_growth = (current_earnings / prev_earnings) - 1
                
                current_revenue = float(income_stmt_reports[0].get("totalRevenue", 0))
                prev_revenue = float(income_stmt_reports[1].get("totalRevenue", 0))
                
                if prev_revenue != 0:
                    revenue_growth = (current_revenue / prev_revenue) - 1
            
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
                'peRatio': float(overview_data.get("PERatio", 0)) if overview_data.get("PERatio") else None,
                'balanceSheet': balance_sheet_reports,
                'incomeStatement': income_stmt_reports,
                'cashFlow': cash_flow_reports
            } 