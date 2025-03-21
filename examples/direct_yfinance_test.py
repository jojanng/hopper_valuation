#!/usr/bin/env python3
"""
Direct YFinance Test

This script tests the yfinance library directly without our wrapper.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import time

def test_symbol(symbol):
    """Test getting data for a symbol directly with yfinance."""
    print(f"\nTesting symbol: {symbol}")
    
    # Try different periods
    periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    
    for period in periods:
        try:
            # Get ticker
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            print(f"  Trying period: {period}")
            hist = ticker.history(period=period)
            
            if hist.empty:
                print(f"  ❌ No history data found for {symbol} with period {period}")
                continue
            
            # Success!
            current_price = hist["Close"].iloc[-1]
            print(f"  ✅ Got data for {symbol} with period {period}")
            print(f"     Latest price: ${current_price:.2f}")
            print(f"     Data points: {len(hist)}")
            
            # Try to get info
            try:
                info = ticker.info
                if info and len(info) > 0:
                    print(f"  ✅ Got info for {symbol}")
                    if 'marketCap' in info:
                        market_cap = info['marketCap'] / 1e9  # Convert to billions
                        print(f"     Market Cap: ${market_cap:.2f}B")
                    if 'trailingPE' in info:
                        pe_ratio = info['trailingPE']
                        print(f"     P/E Ratio: {pe_ratio:.2f}")
                else:
                    print(f"  ❌ No info found for {symbol}")
            except Exception as info_e:
                print(f"  ❌ Error getting info for {symbol}: {str(info_e)}")
            
            return True
        except Exception as e:
            print(f"  ❌ Error for {symbol} with period {period}: {str(e)}")
    
    print(f"❌ All periods failed for {symbol}")
    return False

def main():
    """Main function to test yfinance directly."""
    # List of symbols to test
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "SPY", "QQQ", "NVDA", "AMD"]
    
    # Test each symbol
    results = []
    for symbol in symbols:
        success = test_symbol(symbol)
        results.append((symbol, success))
        # Add a delay to avoid rate limiting
        time.sleep(2)
    
    # Print summary
    print("\n=== Summary ===")
    successful = [symbol for symbol, success in results if success]
    failed = [symbol for symbol, success in results if not success]
    
    print(f"Successful: {len(successful)}/{len(symbols)}")
    if successful:
        print(f"Working symbols: {', '.join(successful)}")
    
    print(f"Failed: {len(failed)}/{len(symbols)}")
    if failed:
        print(f"Failed symbols: {', '.join(failed)}")

if __name__ == "__main__":
    main() 