import stock_fft.algorithms.market_data as mkdata
import stock_fft.algorithms.pricing as prc
import yfinance as yf

def get_market_parameters(symbol):
    """Fetch market parameters such as current price, volatility, and dividend yield """
    S0 = mkdata.get_current_price(symbol)
    sigma = mkdata.get_historical_volatility(symbol)
    r = 0.0425  # Risk-free rate
    div = yf.Ticker(symbol).info.get('dividendYield', 0.0) or 0.0
    q=div/100

    return S0, sigma, r, q

def get_pricing_model():
    """Prompt user to choose the pricing model and return corresponding parameters """
    print("\nChoose pricing model:")
    print("1. Risk-Free Rate (Option Pricing)")
    print("2. Real Expected Return (Stock Prediction)")
    choice = input("Enter 1 or 2: ").strip()
    
    if choice == "1":
        return "Risk-Free Rate", 0.0425, None, False
    elif choice == "2":
        mu = float(input("Enter CAGR in % (e.g., 10 for 10%): ").strip()) / 100
        return f"Real Expected Return (μ = {mu:.1%})", None, mu, True
    else:
        print("Invalid choice. Defaulting to risk-free rate.")
        return "Risk-Free Rate", 0.0425, None, False
     

def main():
    # Get stock details
    symbol = input("Enter stock symbol (e.g., NVDA, AAPL): ").strip()
    K = float(input("Enter strike price: ").strip())
    T = float(input("Enter time to maturity in years: ").strip())
    
    # Fetch market parameters
    S0, sigma, r, q = get_market_parameters(symbol)
    rate_type, rate, mu, use_real_world = get_pricing_model()
    
    # Display market parameters
    print(f"\nMarket Parameters ({rate_type}):")
    print(f"Current price for {symbol}: ${S0:.2f}")
    print(f"Historical volatility: {sigma:.1%}")
    print(f"Risk-free rate: {r:.1%}")
    print(f"Dividend yield: {q:.1%}")
    if use_real_world:
        print(f"Real Expected Return: {mu:.1%}")
    
    # Calculate option prices and expected stock price
    call_price, put_price, prob_ST_above_K, _, _ = prc.char_function_fft(S0, K, T, rate, mu, q, sigma, use_real_world)
    expected_price = prc.stock_price_algo(S0, T, rate, mu, q, use_real_world)
    
    print(f"\nOption Prices and Probabilities ({rate_type}):")
    print(f"Call Option Price: ${call_price:.2f}")
    print(f"Put Option Price: ${put_price:.2f}")
    print(f"Probability of Stock Price > Strike Price (call ITM): {prob_ST_above_K:.2%}")
    print(f"\nExpected Stock Price for {symbol} in {T} years: ${expected_price:.2f}")
    
    # Fetch intrinsic value data
    fcf, _ , terminal_growth_rate, discount_rate, pe_ratio, earnings_growth = mkdata.get_intrinsic_value_data(symbol)
    
    # Fetch analyst consensus estimates dynamically from Yahoo Finance
    stock = yf.Ticker(symbol)
    analyst_growth_estimates = stock.info.get("earningsQuarterlyGrowth", 0.10)  # Use earnings growth as proxy
    terminal_growth_rate = stock.info.get("revenueGrowth", 0.02)  # Use revenue growth as terminal growth estimate
    
    # Growth rates
    adjusted_growth_rate = max(min(analyst_growth_estimates, 0.25), 0.05)  
    terminal_growth_rate = max(min(terminal_growth_rate, 0.03), 0.01)
    
    # Intrinsic value (company's worth)
    intrinsic_value = prc.discounted_cash_flow(fcf, adjusted_growth_rate, discount_rate, terminal_growth=terminal_growth_rate)
    
    # Calculate PEG ratio (skip if earnings growth is negative)
    if earnings_growth > 0:
        peg = prc.peg_ratio(pe_ratio, earnings_growth)
    else:
        peg = None
    
    # Intrinsic value per share
    outstanding_shares = stock.info.get("sharesOutstanding", 0)
    intrinsic_value_per_share = intrinsic_value / outstanding_shares
    print(f"\nIntrinsic Value Per Share for {symbol}: ${intrinsic_value_per_share:.2f}")

    print(f"FCF: {fcf}")
    print(f"Growth Rate: {adjusted_growth_rate}")
    print(f"Terminal Growth Rate: {terminal_growth_rate}")
    print(f"Discount Rate: {discount_rate}")
    print(f"P/E Ratio: {pe_ratio}")
    print(f"Earnings Growth: {earnings_growth}")
    
    print(f"\nIntrinsic Value Estimate: ${intrinsic_value:,.2f}")
    print(f"PEG Ratio: {peg:.2f}" if peg is not None else "PEG Ratio: N/A")
    
if __name__ == "__main__":
    main()
