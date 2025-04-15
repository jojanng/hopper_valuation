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
    
    async def get_historical_fcf(self, symbol: str, years: int = 5) -> List[float]:
        """
        Get historical free cash flow data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            years: Number of years of historical data to fetch
            
        Returns:
            List[float]: List of historical FCF values (oldest to newest)
        """
        def _get_historical_fcf():
            try:
                ticker = yf.Ticker(symbol)
                
                # Get cash flow statements for the past years
                cash_flow = ticker.cashflow
                
                if cash_flow.empty:
                    return []
                
                # Cash flow statements are typically annual
                # We need to calculate FCF = Operating Cash Flow - Capital Expenditures
                if 'Total Cash From Operating Activities' in cash_flow.index and 'Capital Expenditures' in cash_flow.index:
                    operating_cash_flow = cash_flow.loc['Total Cash From Operating Activities']
                    capital_expenditures = cash_flow.loc['Capital Expenditures']
                    
                    # Calculate FCF for each period
                    fcf_values = operating_cash_flow + capital_expenditures  # CapEx is typically negative
                    
                    # Convert to list (most recent first) and limit to requested years
                    fcf_list = fcf_values.to_list()[:years]
                    
                    # Reverse to get oldest first
                    return fcf_list[::-1]
                else:
                    # If the required rows are not found, try alternative names
                    # This handles different naming conventions in the data
                    ocf_candidates = ['Total Cash From Operating Activities', 'Operating Cash Flow']
                    capex_candidates = ['Capital Expenditures', 'CapEx']
                    
                    for ocf_name in ocf_candidates:
                        if ocf_name in cash_flow.index:
                            operating_cash_flow = cash_flow.loc[ocf_name]
                            break
                    else:
                        return []  # OCF not found
                        
                    for capex_name in capex_candidates:
                        if capex_name in cash_flow.index:
                            capital_expenditures = cash_flow.loc[capex_name]
                            break
                    else:
                        return []  # CapEx not found
                    
                    # Calculate FCF
                    fcf_values = operating_cash_flow + capital_expenditures
                    
                    # Convert to list and limit to requested years
                    fcf_list = fcf_values.to_list()[:years]
                    
                    # Reverse to get oldest first
                    return fcf_list[::-1]
            except Exception as e:
                logger.error(f"Error fetching historical FCF for {symbol}: {str(e)}")
                return []
        
        # Run in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_historical_fcf)
    
    async def get_risk_free_rate(self) -> float:
        """
        Get the current risk-free rate (10-year Treasury yield) from Yahoo Finance.
        
        Returns:
            float: Current risk-free rate as a decimal
        """
        def _get_risk_free_rate():
            try:
                # Get the 10-year Treasury yield (^TNX)
                treasury = yf.Ticker("^TNX")
                
                # Get the current yield (convert from percentage to decimal)
                data = treasury.history(period="1d")
                
                if not data.empty:
                    # Get the latest close price (yield)
                    yield_value = data['Close'].iloc[-1] / 100.0  # Convert from percentage
                    return yield_value
                else:
                    # Default value if data not available
                    return 0.035  # 3.5% as default
                    
            except Exception as e:
                logger.error(f"Error fetching risk-free rate: {str(e)}")
                return 0.035  # 3.5% as default
        
        # Run in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_risk_free_rate)
    
    async def get_industry_growth_rate(self, symbol: str) -> float:
        """
        Get the average growth rate for the industry the company belongs to.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Industry growth rate as a decimal
        """
        def _get_industry_growth_rate():
            try:
                ticker = yf.Ticker(symbol)
                
                # Get the industry and sector information
                info = ticker.info
                
                if 'industry' not in info or 'sector' not in info:
                    return 0.03  # Default if industry info not available
                
                industry = info['industry']
                sector = info['sector']
                
                # Get some benchmark tickers for this industry/sector
                benchmark_symbols = []
                
                # Technology companies
                if sector == 'Technology':
                    if 'Software' in industry:
                        benchmark_symbols = ['MSFT', 'ADBE', 'CRM', 'ORCL', 'INTU']
                    elif 'Hardware' in industry or 'Semiconductor' in industry:
                        benchmark_symbols = ['NVDA', 'AMD', 'INTC', 'TSM', 'AVGO']
                    else:
                        benchmark_symbols = ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA']
                
                # Financial companies
                elif sector == 'Financial Services':
                    if 'Bank' in industry:
                        benchmark_symbols = ['JPM', 'BAC', 'WFC', 'C', 'GS']
                    else:
                        benchmark_symbols = ['JPM', 'V', 'MA', 'BLK', 'MS']
                
                # Healthcare companies
                elif sector == 'Healthcare':
                    benchmark_symbols = ['JNJ', 'PFE', 'MRK', 'ABBV', 'UNH']
                
                # Consumer companies
                elif 'Consumer' in sector:
                    benchmark_symbols = ['AMZN', 'WMT', 'PG', 'KO', 'PEP']
                
                # Add more sectors as needed
                else:
                    # Default to S&P 500 components
                    benchmark_symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META']
                
                # Calculate the average analyst growth estimates for the benchmarks
                growth_rates = []
                
                for bench_symbol in benchmark_symbols:
                    if bench_symbol == symbol:
                        continue  # Skip the original symbol
                        
                    try:
                        bench_ticker = yf.Ticker(bench_symbol)
                        bench_info = bench_ticker.info
                        
                        # Try to get growth estimates
                        if 'earningsGrowth' in bench_info and bench_info['earningsGrowth'] is not None:
                            growth_rates.append(bench_info['earningsGrowth'])
                        elif 'revenueGrowth' in bench_info and bench_info['revenueGrowth'] is not None:
                            growth_rates.append(bench_info['revenueGrowth'])
                    except Exception:
                        continue  # Skip if error
                
                # Calculate the average growth rate
                if growth_rates:
                    avg_growth = sum(growth_rates) / len(growth_rates)
                    # Apply reasonable bounds (0% to 30%)
                    avg_growth = max(min(avg_growth, 0.30), 0.0)
                    return avg_growth
                else:
                    # Default if no growth rates are found
                    return 0.03  # 3% as default
                    
            except Exception as e:
                logger.error(f"Error calculating industry growth rate for {symbol}: {str(e)}")
                return 0.03  # 3% as default
        
        # Run in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_industry_growth_rate)
    
    async def get_historical_metrics(self, symbol: str) -> Dict[str, Dict]:
        """
        Get historical financial metrics from Yahoo Finance.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict[str, Dict]: Historical metrics with dates as keys
        """
        def _get_historical_metrics():
            ticker = yf.Ticker(symbol)
            
            # Get quarterly financials
            income_stmt = ticker.quarterly_financials
            balance_sheet = ticker.quarterly_balance_sheet
            
            if income_stmt.empty or balance_sheet.empty:
                raise ValueError(f"No historical financial data found for {symbol}")
            
            # Create result dictionary
            result = {}
            
            # Process each date
            all_dates = sorted(set(income_stmt.columns) | set(balance_sheet.columns))
            for date in all_dates:
                date_str = date.strftime('%Y-%m-%d')
                
                # Get metrics for this date
                net_income = float(income_stmt.loc['Net Income', date]) if 'Net Income' in income_stmt.index and date in income_stmt.columns else None
                ebitda = float(income_stmt.loc['EBITDA', date]) if 'EBITDA' in income_stmt.index and date in income_stmt.columns else None
                total_debt = float(balance_sheet.loc['Total Debt', date]) if 'Total Debt' in balance_sheet.index and date in balance_sheet.columns else None
                cash = float(balance_sheet.loc['Cash', date]) if 'Cash' in balance_sheet.index and date in balance_sheet.columns else None
                shares = float(balance_sheet.loc['Share Issued', date]) if 'Share Issued' in balance_sheet.index and date in balance_sheet.columns else None
                
                result[date_str] = {
                    'netIncome': net_income,
                    'ebitda': ebitda,
                    'totalDebt': total_debt,
                    'cashAndEquivalents': cash,
                    'sharesOutstanding': shares
                }
            
            return result
        
        # Run in a separate thread to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_historical_metrics) 