#!/usr/bin/env python3
"""
This module provides a simplified EPS-based valuation function designed to be integrated into the main application backend.
"""

from datetime import datetime
import logging

# Configure logging
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
    
    # Debug logging
    logger.info(f"apply_sanity_check input: {list(result.keys())}")
    
    # Calculate the maximum and minimum reasonable values
    max_value = current_price * (1 + max_deviation)
    min_value = current_price * (1 - max_deviation)
    
    # Store original values for reporting
    original_value = modified_result.get('intrinsic_value', current_price)
    
    # Apply sanity check to the intrinsic value
    if modified_result['intrinsic_value'] > max_value:
        modified_result['intrinsic_value'] = max_value
        modified_result['estimated_value'] = max_value
        logger.info(f"Adjusted intrinsic value from ${original_value:.2f} to ${max_value:.2f}")
    elif modified_result['intrinsic_value'] < min_value:
        modified_result['intrinsic_value'] = min_value
        modified_result['estimated_value'] = min_value
        logger.info(f"Adjusted intrinsic value from ${original_value:.2f} to ${min_value:.2f}")
    
    # Ensure all required fields are present
    if 'estimated_value' not in modified_result:
        modified_result['estimated_value'] = modified_result['intrinsic_value']
        logger.info("Added missing estimated_value field")
    
    # Add weighted_value field if it doesn't exist (might be expected by the app)
    if 'weighted_value' not in modified_result:
        modified_result['weighted_value'] = modified_result['intrinsic_value']
        logger.info("Added missing weighted_value field")
    
    # Store the original value for reference
    modified_result['original_value'] = original_value
    
    # Debug logging
    logger.info(f"apply_sanity_check output: {list(modified_result.keys())}")
    
    return modified_result

def calculate_eps_based_valuation(eps, growth_rate, years, terminal_pe=15, discount_rate=0.15, current_price=None):
    """
    Calculate the intrinsic value and entry price using a simplified EPS-based approach.
    
    This function replaces the more complex DCF-based EPS valuation with a simpler
    approach that matches Hopper's calculation method.
    
    Args:
        eps: Current earnings per share
        growth_rate: Annual EPS growth rate (decimal, e.g., 0.07 for 7%)
        years: Number of years for the projection
        terminal_pe: Target P/E ratio to apply to future EPS (renamed from eps_multiple for compatibility)
        discount_rate: Desired annual return (renamed from desired_return for compatibility)
        current_price: Current stock price (optional, for implied return calculation)
        
    Returns:
        Dictionary with valuation results in the format expected by the main application
    """
    # Input validation
    if eps <= 0 or years <= 0 or discount_rate <= 0:
        logger.warning("Invalid input parameters for EPS valuation")
        return {
            'intrinsic_value': 0,
            'estimated_value': 0,
            'weighted_value': 0,
            'implied_return': 0
        }
    
    # Calculate future EPS
    future_eps = eps * (1 + growth_rate) ** years
    
    # Calculate future value (target price)
    future_value = future_eps * terminal_pe
    
    # Calculate intrinsic value (present value of future value)
    # This is the key calculation that determines the intrinsic value
    intrinsic_value = future_value / (1 + discount_rate) ** years
    
    # Calculate entry price for desired return
    entry_price = intrinsic_value
    
    # Calculate implied return if current price is provided
    implied_return = None
    if current_price is not None and current_price > 0:
        try:
            # Instead of using future_value/current_price, we use a different approach
            # that considers the relationship between intrinsic value and current price
            implied_return = (future_value / current_price) ** (1 / years) - 1
        except ZeroDivisionError:
            logger.warning("Division by zero in implied return calculation")
            implied_return = 0
    else:
        implied_return = 0
    
    # Create the result dictionary
    result = {
        'intrinsic_value': intrinsic_value,
        'estimated_value': intrinsic_value,
        'weighted_value': intrinsic_value,
        'implied_return': implied_return,
        'future_value': future_value,
        'future_eps': future_eps
    }
    
    # Apply sanity check if current price is available
    if current_price is not None and current_price > 0:
        result = apply_sanity_check(result, current_price)
    
    return result

# Example usage for testing
if __name__ == "__main__":
    # Example with Apple's data
    result = calculate_eps_based_valuation(
        eps=6.24,           # Current EPS
        growth_rate=0.07,   # 7% annual growth
        years=5,            # 5-year projection
        terminal_pe=30,     # Target P/E ratio
        discount_rate=0.15, # 15% desired annual return
        current_price=187.52 # Current stock price
    )
    
    print(f"Intrinsic Value: ${result['intrinsic_value']:.2f}")
    print(f"Future EPS (after {result['years']} years): ${result['future_eps']:.2f}")
    print(f"Future Value: ${result['future_value']:.2f}")
    print(f"Entry Price: ${result['entry_price_for_target']:.2f}")
    
    if 'implied_return' in result and result['implied_return'] is not None:
        print(f"Implied Return at Current Price: {result['implied_return']*100:.2f}%")
    
    print(f"\nProjected EPS by Year:")
    for year_data in result['projected_eps']:
        print(f"Year {year_data['year']}: ${year_data['eps']:.2f}")
    
    print(f"\nQuarterly Projections:")
    for quarter_data in result['quarterly_projections']:
        print(f"{quarter_data['quarter']}: ${quarter_data['eps']:.2f}") 