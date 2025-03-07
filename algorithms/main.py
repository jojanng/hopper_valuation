import market_data as mkdata
import pricing as prc
import yfinance as yf

def get_market_parameters(symbol):
    """Fetch market parameters such as current price, volatility, and dividend yield """
    try:
        S0 = mkdata.get_current_price(symbol)
        sigma = mkdata.get_historical_volatility(symbol)
        r = 0.0425  # Risk-free rate
        stock = yf.Ticker(symbol)
        div = stock.info.get('dividendYield', 0.0) or 0.0
        q = div/100
        return S0, sigma, r, q
    except ValueError as e:
        print(f"\nError: {str(e)}")
        return None, None, None, None

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
    """Main function to run the stock valuation and option pricing tool"""
    try:
        print("\nStock Valuation and Option Pricing Tool")
        print("=" * 40)
        
        while True:
            try:
                # Get stock details with proper input handling
                symbol = input("\nEnter stock symbol (e.g., NVDA, AAPL) or 'quit' to exit: ")
                if not symbol:  # Handle empty input
                    print("Please enter a valid stock symbol.")
                    continue
                    
                symbol = symbol.strip().upper()
                if symbol.lower() == 'quit':
                    print("Exiting program...")
                    break
                
                # Basic symbol validation
                if not all(c.isalpha() or c == '.' for c in symbol):  # Allow dots for BRK.A type symbols
                    print("Invalid symbol. Please enter only letters (and dots for special cases).")
                    continue
                    
                # Validate stock data is available
                try:
                    S0, sigma, r, q = get_market_parameters(symbol)
                    if None in (S0, sigma, r, q):
                        continue
                except Exception as e:
                    print(f"Error: Unable to fetch data for {symbol}. Please try another symbol.")
                    continue
                
                # Get option parameters
                try:
                    K = float(input("Enter strike price: ").strip())
                    T = float(input("Enter time to maturity in years: ").strip())
                    if K <= 0 or T <= 0:
                        raise ValueError("Strike price and time to maturity must be positive numbers.")
                except ValueError as e:
                    print(f"Error: {str(e)}")
                    continue
                
                # Get pricing model parameters
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
                
                try:
                    # Get valuation results
                    results = prc.weighted_valuation(symbol)
                    
                    # Print the comprehensive valuation report
                    prc.print_valuation_report(results)
                    
                except Exception as e:
                    print(f"\nError calculating valuation: {str(e)}")
                    print("Some financial data might not be available for this stock.")
                
                # Ask if user wants to analyze another stock
                choice = input("\nAnalyze another stock? (y/n): ").strip().lower()
                if choice != 'y':
                    break
                    
            except Exception as e:
                print(f"\nUnexpected error: {str(e)}")
                print("Please try again with a different stock symbol.")
                continue
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"\nCritical error: {str(e)}")
        print("Program will now exit.")

if __name__ == "__main__":
    main()
