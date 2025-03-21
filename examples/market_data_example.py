#!/usr/bin/env python3
"""
Market Data Service Example

This script demonstrates how to use the MarketDataService to fetch market data.
"""

import asyncio
import logging
import os
import sys
from pprint import pprint

# Add the parent directory to the path so we can import the qualtrim_backend package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qualtrim_backend.services.market_data.service import MarketDataService
from qualtrim_backend.config.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to demonstrate the MarketDataService."""
    # Create a settings object
    settings = Settings()
    
    # Create a MarketDataService instance
    market_data_service = MarketDataService(config=settings)
    
    # Define a symbol to use for the examples
    symbol = "MSFT"
    
    # Example 1: Get current price
    print(f"\n=== Getting current price for {symbol} ===")
    try:
        price = await market_data_service.get_current_price(symbol)
        print(f"Current price: ${price:.2f}")
    except Exception as e:
        logger.error(f"Error getting current price: {str(e)}")
    
    # Add a small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Example 2: Get historical volatility
    print(f"\n=== Getting historical volatility for {symbol} ===")
    try:
        volatility = await market_data_service.get_historical_volatility(symbol)
        print(f"Historical volatility (annualized): {volatility:.4f} ({volatility*100:.2f}%)")
    except Exception as e:
        logger.error(f"Error getting historical volatility: {str(e)}")
    
    # Add a small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Example 3: Get historical data
    print(f"\n=== Getting historical data for {symbol} (last 5 days) ===")
    try:
        historical_data = await market_data_service.get_historical_data(symbol, period="5d")
        # Print the last 5 days of data
        for date, data in list(historical_data.items())[-5:]:
            print(f"{date}: Open=${data['open']:.2f}, Close=${data['close']:.2f}, Volume={data['volume']}")
    except Exception as e:
        logger.error(f"Error getting historical data: {str(e)}")
    
    # Add a small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Example 4: Get financial data
    print(f"\n=== Getting financial data for {symbol} ===")
    try:
        financial_data = await market_data_service.get_financial_data(symbol)
        # Print a subset of the financial data
        print(f"Market Cap: ${financial_data['marketCap']/1e9:.2f}B")
        print(f"Enterprise Value: ${financial_data['enterpriseValue']/1e9:.2f}B")
        print(f"P/E Ratio: {financial_data['peRatio']}")
        print(f"Free Cash Flow: ${financial_data['freeCashFlow']/1e9:.2f}B")
    except Exception as e:
        logger.error(f"Error getting financial data: {str(e)}")
    
    # Add a small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Example 5: Get growth estimates
    print(f"\n=== Getting growth estimates for {symbol} ===")
    try:
        growth_rate = await market_data_service.get_analyst_growth_estimates(symbol)
        print(f"Growth rate estimate: {growth_rate:.4f} ({growth_rate*100:.2f}%)")
    except Exception as e:
        logger.error(f"Error getting growth estimates: {str(e)}")
    
    # Add a small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Example 6: Using a specific provider
    print(f"\n=== Using a specific provider (yfinance) ===")
    try:
        price = await market_data_service.get_current_price(symbol, provider="yfinance")
        print(f"Current price from YFinance: ${price:.2f}")
    except Exception as e:
        logger.error(f"Error getting price from YFinance: {str(e)}")
    
    # Add a small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Example 7: Fallback behavior
    print(f"\n=== Testing fallback behavior ===")
    try:
        # Try to use a non-existent provider, should fall back to default
        price = await market_data_service.get_current_price(symbol, provider="nonexistent")
        print(f"Price with fallback: ${price:.2f}")
    except Exception as e:
        logger.error(f"Error with fallback: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 