import yfinance as yf
import numpy as np

def get_analyst_growth_estimates(stock):
    """Get growth estimates from analyst forecasts"""
    try:
        # Get analyst data
        info = stock.info
        
        # Get earnings growth estimates
        next_5y_growth = info.get('earningsGrowth5Year', None)
        next_year_growth = info.get('earningsGrowthNextYear', None)
        current_year_growth = info.get('earningsGrowthCurrentYear', None)
        
        # If 5-year estimate available, use it
        if next_5y_growth is not None and next_5y_growth > -1:
            return next_5y_growth
        
        # If not, use weighted average of next year and current year
        if next_year_growth is not None and current_year_growth is not None:
            if next_year_growth > -1 and current_year_growth > -1:
                return (next_year_growth * 0.6) + (current_year_growth * 0.4)
        
        # If still no valid growth rate, use revenue growth estimates
        revenue_growth = info.get('revenueGrowth', None)
        if revenue_growth is not None and revenue_growth > -1:
            return revenue_growth
        
        # Default conservative growth rate
        return 0.05  # 5% default growth
    except Exception:
        return 0.05  # Default to 5% if any error occurs

def get_current_price(symbol):
    """Get latest stock price using yahoo finance api"""
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Invalid symbol provided")
        
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")
        if hist.empty:
            raise ValueError(f"No data found for symbol {symbol}. The stock might be delisted or invalid.")
        current_price = hist["Close"].iloc[-1]
        if not current_price or current_price <= 0:
            raise ValueError(f"Invalid price data for {symbol}")
        return current_price
    except Exception as e:
        if "Failed to download" in str(e):
            raise ValueError(f"Unable to fetch data for {symbol}. Please check the symbol and try again.")
        raise ValueError(f"Error fetching price for {symbol}: {str(e)}")

def get_historical_volatility(symbol, lookback="2y"):
    """Get historical volatility of a stock for X period (6mo, 2y, 5y)"""
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=lookback)
        if hist.empty:
            raise ValueError(f"No historical data found for symbol {symbol}")
        returns = np.log(hist["Close"]/hist["Close"].shift(1))  # daily volatility
        return returns.std() * np.sqrt(252)  # annual volatility
    except Exception as e:
        raise ValueError(f"Error calculating volatility for {symbol}: {str(e)}")

def get_intrinsic_value_data(symbol):
    """Fetch intrinsic value calculation inputs from Yahoo Finance API with manual TTM FCF input"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Get FCF using the improved function
        fcf = get_manual_fcf(symbol)
        
        # Get growth rates from analyst estimates
        earnings_growth = info.get("earningsGrowth", None)
        revenue_growth = info.get("revenueGrowth", None)
        
        # If growth rates are negative or None, use analyst estimates
        if earnings_growth is None or earnings_growth < 0:
            print("\nNegative or missing earnings growth. Using analyst estimates...")
            earnings_growth = get_analyst_growth_estimates(stock)
        
        # Growth rates reasonable values
        growth_rate = max(min(earnings_growth, 0.30), 0.05)  # Cap between 5% and 30%
        terminal_growth_rate = max(min(revenue_growth if revenue_growth and revenue_growth > 0 else 0.02, 0.03), 0.01)  # Cap between 1% and 3%
        
        # Discount rate (default to 8%)
        discount_rate = 0.08
        
        # P/E ratio (trailing P/E) (default 15 if unavailable)
        pe_ratio = info.get("trailingPE", 15)
        
        return fcf, growth_rate, terminal_growth_rate, discount_rate, pe_ratio, earnings_growth
    except Exception as e:
        raise ValueError(f"Error fetching intrinsic value data for {symbol}: {str(e)}")

def get_manual_fcf(symbol):
    """Get TTM Free Cash Flow manually from user input"""
    stock = yf.Ticker(symbol)
    cashflow = stock.cashflow
    
    # Display annual FCF for reference
    if "Free Cash Flow" in cashflow.index:
        annual_fcf = cashflow.loc["Free Cash Flow"].iloc[0]
        print(f"Reference - Most recent annual FCF for {symbol}: {annual_fcf:,.0f}")
    
    # Prompt user to manually input TTM FCF
    print("\nYahoo Finance API doesn't provide direct access to TTM FCF.")
    manual_fcf = input(f"Please enter the TTM Free Cash Flow for {symbol} (shown in Yahoo Finance website): ")
    
    try:
        # Convert input to float, stripping commas if present
        fcf = float(manual_fcf.replace(',', '')) * 1000  # Multiply by 1000 as Yahoo shows values in thousands
    except ValueError:
        print("Invalid input. Using most recent annual FCF as fallback.")
        fcf = annual_fcf if "Free Cash Flow" in cashflow.index else 0.0
    
    return fcf