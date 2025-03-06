import yfinance as yf
import numpy as np

def get_current_price(symbol):
    """"Get latest stock price using yahoo finance api"""
    stock = yf.Ticker(symbol)
    #Get closing price with .iloc[-1] (last row of "Close") 
    current_price = stock.history(period ="1d")["Close"].iloc[-1]
    return current_price

def get_historical_volatility(symbol, lookback="2y"):
    """"Get historical volatility of a stock for X period (6mo, 2y, 5y)"""
    stock = yf.Ticker(symbol)
    hist = stock.history(period = lookback)
    returns = np.log(hist["Close"]/hist["Close"].shift(1)) # daily volatility
    return returns.std() * np.sqrt(252) # annual volatility = daily volatility x sqrt of nb of trading days in a yr (252 days)

def get_intrinsic_value_data(symbol):
    """Fetch intrinsic value calculation inputs from Yahoo Finance API """
    stock = yf.Ticker(symbol)
    info = stock.info
    cashflow = stock.cashflow

    # Free Cash Flow (FCF)
    if "Free Cash Flow" in cashflow.index:
        fcf = cashflow.loc['Free Cash Flow'].iloc[0]
    else:
        fcf = 0.0
    
    # Fetch analyst consensus estimates dynamically from Yahoo Finance
    analyst_growth_estimates = info.get("earningsQuarterlyGrowth", 0.10)  # earnings growth as proxy (to verify)
    terminal_growth_rate = info.get("revenueGrowth", 0.02)  # revenue growth as terminal growth estimate (to verify)

    # Growth rates reasonable values (to verify)
    growth_rate = max(min(analyst_growth_estimates, 0.30), 0.05)  # Cap between 5% and 30%
    terminal_growth_rate = max(min(terminal_growth_rate, 0.03), 0.01)  # Cap between 1% and 3%

    # Discount rate (default to 8%)
    discount_rate = 0.08

    # P/E ratio (trailing P/E) (default 15 if unavailable)
    pe_ratio = info.get("trailingPE", 15)  

    # Earnings growth rate (default 10% if unavailable)
    earnings_growth = info.get("earningsGrowth", 0.10)

    return fcf, growth_rate, terminal_growth_rate, discount_rate, pe_ratio, earnings_growth

