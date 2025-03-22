#!/usr/bin/env python3
"""
Valuation Service Example

This script demonstrates how to use the ValuationService for intrinsic valuation.
It applies sanity checks to ensure the valuations are within a reasonable range.
"""

import asyncio
import logging
import os
import sys
from pprint import pprint

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hopper_backend.services.market_data.service import MarketDataService
from hopper_backend.services.valuation.service import ValuationService
from hopper_backend.config.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_sanity_check(result, current_price, max_deviation=0.5):
    """
    Apply a sanity check to the valuation results to ensure they're within a reasonable range.
    
    Args:
        result: The valuation result dictionary
        current_price: The current market price
        max_deviation: Maximum allowed deviation from current price (as a percentage)
        
    Returns:
        A modified result dictionary with reasonable values
    """
    # Make a copy of the result to avoid modifying the original
    modified_result = result.copy()
    
    # Calculate the maximum and minimum reasonable values
    max_value = current_price * (1 + max_deviation)
    min_value = current_price * (1 - max_deviation)
    
    # Store original values for reporting
    original_values = {}
    
    # Apply sanity check to the weighted value (intrinsic value)
    if 'weighted_value' in modified_result:
        original_values['weighted_value'] = modified_result['weighted_value']
        if modified_result['weighted_value'] > max_value:
            modified_result['weighted_value'] = max_value
            logger.info(f"Adjusted weighted value from ${original_values['weighted_value']:.2f} to ${max_value:.2f}")
        elif modified_result['weighted_value'] < min_value:
            modified_result['weighted_value'] = min_value
            logger.info(f"Adjusted weighted value from ${original_values['weighted_value']:.2f} to ${min_value:.2f}")
    
    # Apply sanity check to individual model values
    for key in ['dcf_value', 'pe_value', 'ev_ebitda_value']:
        if key in modified_result:
            original_values[key] = modified_result[key]
            if modified_result[key] > max_value:
                modified_result[key] = max_value
                logger.info(f"Adjusted {key} from ${original_values[key]:.2f} to ${max_value:.2f}")
            elif modified_result[key] < min_value:
                modified_result[key] = min_value
                logger.info(f"Adjusted {key} from ${original_values[key]:.2f} to ${min_value:.2f}")
    
    # Recalculate upside potential based on adjusted weighted value
    if 'weighted_value' in modified_result and 'current_price' in modified_result:
        modified_result['upside_potential'] = (modified_result['weighted_value'] / modified_result['current_price'] - 1) * 100
    
    # Store the original values for reference
    modified_result['original_values'] = original_values
    
    return modified_result

def print_valuation_summary(result, title="Valuation Summary"):
    """Print a formatted summary of the valuation results."""
    print(f"\n=== {title} ===")
    print(f"Symbol: {result['symbol']}")
    print(f"Current Price: ${result['current_price']:.2f}")
    print(f"Intrinsic Value: ${result['weighted_value']:.2f}")
    print(f"Upside/Downside: {result['upside_potential']:.2f}%")
    
    # Print original values if they were adjusted
    if 'original_values' in result and 'weighted_value' in result['original_values']:
        original = result['original_values']['weighted_value']
        print(f"\nOriginal Calculated Value: ${original:.2f}")
        print(f"Adjustment Applied: {abs(original - result['weighted_value']):.2f} ({abs(original - result['weighted_value'])/original*100:.2f}%)")
    
    print("\nValuation Model Weights:")
    weights = result['details']
    print(f"  DCF Weight: {weights['dcf']['weight']*100:.2f}%")
    print(f"  P/E Weight: {weights['pe']['weight']*100:.2f}%")
    print(f"  EV/EBITDA Weight: {weights['ev_ebitda']['weight']*100:.2f}%")
    
    print("\nIndividual Model Valuations:")
    print(f"  DCF Valuation: ${result['dcf_value']:.2f}")
    if 'original_values' in result and 'dcf_value' in result['original_values']:
        print(f"    (Original: ${result['original_values']['dcf_value']:.2f})")
    
    print(f"  P/E Valuation: ${result['pe_value']:.2f}")
    if 'original_values' in result and 'pe_value' in result['original_values']:
        print(f"    (Original: ${result['original_values']['pe_value']:.2f})")
    
    print(f"  EV/EBITDA Valuation: ${result['ev_ebitda_value']:.2f}")
    if 'original_values' in result and 'ev_ebitda_value' in result['original_values']:
        print(f"    (Original: ${result['original_values']['ev_ebitda_value']:.2f})")
    
    print("\nKey Financial Metrics:")
    financials = result['details']['financial']
    print(f"  Market Cap: ${financials['market_cap']/1e9:.2f}B")
    print(f"  EBITDA: ${financials['ebitda']/1e9:.2f}B")
    print(f"  Free Cash Flow: ${financials['fcf']/1e9:.2f}B")
    print(f"  Net Income: ${financials['net_income']/1e9:.2f}B")
    print(f"  P/E Ratio: {financials['pe_ratio']:.2f}x")
    print(f"  Shares Outstanding: {financials['shares_outstanding']/1e9:.2f}B")
    
    # Print DCF model details
    print("\nDCF Model Details:")
    dcf = result['details']['dcf']
    print(f"  Growth Rate: {dcf['growth_rate']*100:.2f}%")
    print(f"  Terminal Growth: {dcf['terminal_growth']*100:.2f}%")
    print(f"  Discount Rate: {dcf['discount_rate']*100:.2f}%")
    print(f"  Enterprise Value: ${dcf['enterprise_value']/1e9:.2f}B")
    print(f"  Equity Value: ${dcf['equity_value']/1e9:.2f}B")

async def main():
    """Main function to demonstrate the ValuationService."""
    # Create a settings object
    settings = Settings()
    
    # Create a config dictionary for the ValuationService
    config_dict = {
        "valuation_weights": {
            "dcf": 0.5,
            "pe": 0.3,
            "ev_ebitda": 0.2
        }
    }
    
    # Create a MarketDataService instance
    market_data_service = MarketDataService(config=settings)
    
    # Create a ValuationService instance with the config dictionary
    valuation_service = ValuationService(market_data_service, config=config_dict)
    
    # Define a symbol to use for the examples
    symbol = "PLTR"
    
    print("\n" + "="*80)
    print(f"INTRINSIC VALUATION EXAMPLE FOR {symbol}")
    print("="*80)
    
    # Example 1: Get current price for reference
    print(f"\n=== Current Market Price for {symbol} ===")
    try:
        price = await market_data_service.get_current_price(symbol)
        print(f"Current price: ${price:.2f}")
    except Exception as e:
        logger.error(f"Error getting current price: {str(e)}")
    
    # Add a small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Example 2: Calculate intrinsic value with default parameters
    print(f"\n=== Default Intrinsic Valuation for {symbol} ===")
    try:
        raw_result = await valuation_service.calculate_intrinsic_value(symbol)
        
        # Print the raw result structure if needed for debugging
        if '--debug' in sys.argv:
            print("\nRaw Result Structure:")
            pprint(raw_result)
        
        # Apply sanity check to make valuations more reasonable
        result = apply_sanity_check(raw_result, raw_result['current_price'])
        
        # Print a formatted summary of the valuation
        print_valuation_summary(result, "Default Valuation Summary")
        
    except Exception as e:
        logger.error(f"Error calculating intrinsic value: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Add a small delay to avoid rate limiting
    await asyncio.sleep(1)
    
    # Example 3: Calculate intrinsic value with custom growth rate
    print(f"\n=== Custom Growth Rate Valuation for {symbol} ===")
    try:
        custom_growth = 0.15  # 15% growth rate
        raw_custom_result = await valuation_service.calculate_intrinsic_value(
            symbol, 
            custom_dcf_growth=custom_growth
        )
        
        # Print the raw result structure if needed for debugging
        if '--debug' in sys.argv:
            print("\nRaw Custom Growth Result Structure:")
            pprint(raw_custom_result)
        
        # Apply sanity check to make valuations more reasonable
        custom_result = apply_sanity_check(raw_custom_result, raw_custom_result['current_price'])
        
        # Print a formatted summary of the valuation
        print_valuation_summary(custom_result, f"Custom Growth ({custom_growth*100:.0f}%) Valuation Summary")
        
        # Only proceed with the comparison if we have valid results
        if result and custom_result:
            print("\nComparison to Default Growth Rate:")
            print(f"  Default Intrinsic Value: ${result['weighted_value']:.2f}")
            print(f"  Custom Intrinsic Value: ${custom_result['weighted_value']:.2f}")
            print(f"  Difference: ${custom_result['weighted_value'] - result['weighted_value']:.2f}")
            
            # Compare the original values before sanity checks
            if 'original_values' in result and 'original_values' in custom_result:
                orig_default = result['original_values'].get('weighted_value', result['weighted_value'])
                orig_custom = custom_result['original_values'].get('weighted_value', custom_result['weighted_value'])
                print(f"\nOriginal Values Comparison (Before Sanity Checks):")
                print(f"  Default Original Value: ${orig_default:.2f}")
                print(f"  Custom Original Value: ${orig_custom:.2f}")
                print(f"  Original Difference: ${orig_custom - orig_default:.2f}")
    except Exception as e:
        logger.error(f"Error calculating custom growth valuation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Example 4: Calculate intrinsic value with custom weights
    print(f"\n=== Custom Weights Valuation for {symbol} ===")
    try:
        custom_weights = {
            "dcf": 0.7,
            "pe": 0.2,
            "ev_ebitda": 0.1
        }
        
        raw_custom_weights_result = await valuation_service.calculate_intrinsic_value(
            symbol,
            custom_weights=custom_weights
        )
        
        # Print the raw result structure if needed for debugging
        if '--debug' in sys.argv:
            print("\nRaw Custom Weights Result Structure:")
            pprint(raw_custom_weights_result)
        
        # Apply sanity check to make valuations more reasonable
        custom_weights_result = apply_sanity_check(raw_custom_weights_result, raw_custom_weights_result['current_price'])
        
        # Print a formatted summary of the valuation
        print_valuation_summary(custom_weights_result, "Custom Weights Valuation Summary")
        
        # Only proceed with the comparison if we have valid results
        if result and custom_weights_result:
            print("\nComparison to Default Weights:")
            print(f"  Default Weights: DCF={result['details']['dcf']['weight']*100:.0f}%, " +
                  f"P/E={result['details']['pe']['weight']*100:.0f}%, " +
                  f"EV/EBITDA={result['details']['ev_ebitda']['weight']*100:.0f}%")
            print(f"  Custom Weights: DCF={custom_weights_result['details']['dcf']['weight']*100:.0f}%, " +
                  f"P/E={custom_weights_result['details']['pe']['weight']*100:.0f}%, " +
                  f"EV/EBITDA={custom_weights_result['details']['ev_ebitda']['weight']*100:.0f}%")
            print(f"  Default Intrinsic Value: ${result['weighted_value']:.2f}")
            print(f"  Custom Weights Intrinsic Value: ${custom_weights_result['weighted_value']:.2f}")
            print(f"  Difference: ${custom_weights_result['weighted_value'] - result['weighted_value']:.2f}")
            
            # Compare the original values before sanity checks
            if 'original_values' in result and 'original_values' in custom_weights_result:
                orig_default = result['original_values'].get('weighted_value', result['weighted_value'])
                orig_custom = custom_weights_result['original_values'].get('weighted_value', custom_weights_result['weighted_value'])
                print(f"\nOriginal Values Comparison (Before Sanity Checks):")
                print(f"  Default Original Value: ${orig_default:.2f}")
                print(f"  Custom Original Value: ${orig_custom:.2f}")
                print(f"  Original Difference: ${orig_custom - orig_default:.2f}")
    except Exception as e:
        logger.error(f"Error calculating custom weights valuation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print(f"VALUATION COMPLETE FOR {symbol}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main()) 