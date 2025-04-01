import logging
import asyncio
from typing import Dict, List, Optional, Any
import yfinance as yf
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class YFinanceProvider:
    """Provider for fetching market data from Yahoo Finance"""
    
    def __init__(self):
        self.name = "yfinance"
    
    async def get_current_price(self, symbol: str) -> float:
        """
        Get the latest stock price from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Current stock price
        """
        def _get_price():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if hist.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            current_price = hist["Close"].iloc[-1]
            if current_price <= 0:
                raise ValueError(f"Invalid price for {symbol}")
                
            return float(current_price)
        
        # Run in a separate thread to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_price)
    
    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> Dict:
        """
        Get historical price data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            period: Time period (e.g., 1d, 1mo, 1y, 5y)
            interval: Data interval (e.g., 1m, 5m, 1h, 1d)
            
        Returns:
            Dict: Historical data with dates as keys and OHLCV data as values
        """
        def _get_historical_data():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                raise ValueError(f"No historical data found for symbol {symbol}")
            
            # Convert DataFrame to dictionary
            result = {}
            for date, row in hist.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                result[date_str] = {
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                }
            
            return result
        
        # Run in a separate thread to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_historical_data)
    
    async def get_historical_volatility(self, symbol: str, lookback: int = 252) -> float:
        """
        Calculate historical volatility from Yahoo Finance data.
        
        Args:
            symbol: Stock symbol
            lookback: Number of trading days to look back
            
        Returns:
            float: Historical volatility (annualized)
        """
        import numpy as np
        
        def _calculate_volatility():
            ticker = yf.Ticker(symbol)
            # Get enough data to cover the lookback period plus some buffer
            hist = ticker.history(period=f"{lookback + 50}d")
            
            if hist.empty or len(hist) < lookback:
                raise ValueError(f"Insufficient historical data for {symbol}")
            
            # Calculate daily returns
            hist = hist.tail(lookback)
            returns = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
            
            # Calculate annualized volatility
            daily_volatility = returns.std()
            annualized_volatility = daily_volatility * np.sqrt(252)
            
            return float(annualized_volatility)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _calculate_volatility)
    
    async def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive financial data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict: Financial data including balance sheet, income statement, etc.
        """
        def _get_financial_data():
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get balance sheet
            balance_sheet = ticker.balance_sheet
            balance_sheet_dict = {}
            if not balance_sheet.empty:
                # Convert DataFrame to nested dict
                balance_sheet_dict = {
                    col.strftime('%Y-%m-%d') if isinstance(col, pd.Timestamp) else str(col): {
                        index: float(value) if pd.notna(value) else None
                        for index, value in balance_sheet[col].items()
                    }
                    for col in balance_sheet.columns
                }
            
            # Get income statement
            income_stmt = ticker.income_stmt
            income_stmt_dict = {}
            if not income_stmt.empty:
                income_stmt_dict = {
                    col.strftime('%Y-%m-%d') if isinstance(col, pd.Timestamp) else str(col): {
                        index: float(value) if pd.notna(value) else None
                        for index, value in income_stmt[col].items()
                    }
                    for col in income_stmt.columns
                }
            
            # Get cash flow statement
            cashflow = ticker.cashflow
            cashflow_dict = {}
            if not cashflow.empty:
                cashflow_dict = {
                    col.strftime('%Y-%m-%d') if isinstance(col, pd.Timestamp) else str(col): {
                        index: float(value) if pd.notna(value) else None
                        for index, value in cashflow[col].items()
                    }
                    for col in cashflow.columns
                }
            
            # Extract key metrics
            market_cap = info.get('marketCap', 0)
            shares_outstanding = info.get('sharesOutstanding', 0)
            current_price = info.get('currentPrice', 0)
            
            # Get growth rates
            earnings_growth = info.get('earningsGrowth', None)
            revenue_growth = info.get('revenueGrowth', None)
            
            # Additional growth metrics
            next_5y_growth = info.get('earningsGrowth5Year', None)
            next_year_growth = info.get('earningsGrowthNextYear', None)
            current_year_growth = info.get('earningsGrowthCurrentYear', None)
            
            # Get enterprise value components
            total_debt = 0
            cash_and_equivalents = 0
            
            if not balance_sheet.empty:
                if 'Total Debt' in balance_sheet.index:
                    total_debt = balance_sheet.loc['Total Debt'].iloc[0]
                elif 'Long Term Debt' in balance_sheet.index:
                    total_debt = balance_sheet.loc['Long Term Debt'].iloc[0]
                
                if 'Cash And Cash Equivalents' in balance_sheet.index:
                    cash_and_equivalents = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
            
            # Get income statement data
            net_income = 0
            ebitda = 0
            
            if not income_stmt.empty:
                if 'Net Income' in income_stmt.index:
                    net_income = income_stmt.loc['Net Income'].iloc[0]
                
                if 'EBITDA' in income_stmt.index:
                    ebitda = income_stmt.loc['EBITDA'].iloc[0]
            
            # Calculate enterprise value
            enterprise_value = market_cap + total_debt - cash_and_equivalents
            
            # Get free cash flow
            fcf = None
            if not cashflow.empty and 'Free Cash Flow' in cashflow.index:
                fcf = cashflow.loc['Free Cash Flow'].iloc[0]
            
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
                'earningsGrowth5Year': next_5y_growth,
                'earningsGrowthNextYear': next_year_growth,
                'earningsGrowthCurrentYear': current_year_growth,
                'peRatio': info.get('trailingPE', None),
                'balanceSheet': balance_sheet_dict,
                'incomeStatement': income_stmt_dict,
                'cashFlow': cashflow_dict
            }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_financial_data)
    
    async def get_available_symbols(self) -> List[str]:
        """
        Get a list of available symbols from Yahoo Finance.
        This includes stocks, ETFs, and other financial instruments.
        
        Returns:
            List[str]: List of available symbols
        """
        def _get_symbols():
            # Get popular ETFs and stocks
            etfs = ['SPY', 'VOO', 'QQQ', 'VTI', 'BND', 'VEA', 'VWO', 'AGG']
            stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'PLTR', 'ASML', 
                     'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'INTC', 'VZ', 'ADBE', 
                     'NFLX', 'CSCO', 'PFE', 'CRM', 'ABT', 'KO', 'PEP', 'NKE', 'T', 'MRK', 'DIS']
            
            # Combine and sort
            symbols = sorted(list(set(etfs + stocks)))
            
            # Verify each symbol is valid
            valid_symbols = []
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    if info and 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
                        valid_symbols.append(symbol)
                except Exception as e:
                    logger.debug(f"Symbol {symbol} not available: {str(e)}")
            
            return valid_symbols
        
        # Run in a separate thread to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_symbols) 