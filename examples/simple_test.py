#!/usr/bin/env python3
"""
Simple Test Script

This script tests basic functionality of the YFinanceProvider directly.
"""

import asyncio
import logging
import os
import sys

# Add the parent directory to the path so we can import the qualtrim_backend package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qualtrim_backend.services.market_data.providers.yfinance_provider import YFinanceProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_symbol(provider, symbol):
    """Test getting the current price for a symbol."""
    print(f"\nTesting symbol: {symbol}")
    try:
        price = await provider.get_current_price(symbol)
        print(f"✅ Success! Current price for {symbol}: ${price:.2f}")
        return True
    except Exception as e:
        print(f"❌ Error getting price for {symbol}: {str(e)}")
        return False

async def main():
    """Main function to test the YFinanceProvider."""
    # Create a YFinanceProvider instance
    provider = YFinanceProvider()
    
    # List of symbols to test
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "SPY", "QQQ", "NVDA", "AMD"]
    
    # Test each symbol
    results = []
    for symbol in symbols:
        success = await test_symbol(provider, symbol)
        results.append((symbol, success))
        # Add a delay to avoid rate limiting
        await asyncio.sleep(2)
    
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
    asyncio.run(main()) 