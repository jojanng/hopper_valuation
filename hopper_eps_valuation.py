#!/usr/bin/env python3
"""
EPS-based Valuation

This module provides a simplified EPS-based valuation function that matches.
"""

print("Script starting...")

def calculate_hopper_eps_valuation(eps, growth_rate, years, eps_multiple, desired_return, current_price=None):
    """
    Calculate the intrinsic value and entry price using a simplified EPS-based approach.
    
    Args:
        eps: Current earnings per share
        growth_rate: Annual EPS growth rate (decimal, e.g., 0.07 for 7%)
        years: Number of years for the projection
        eps_multiple: Target P/E ratio to apply to future EPS
        desired_return: Desired annual return (decimal, e.g., 0.15 for 15%)
        current_price: Current stock price (optional, for implied return calculation)
        
    Returns:
        Dictionary with valuation results
    """
    print(f"Calculating with: EPS=${eps}, Growth={growth_rate*100}%, Years={years}, P/E={eps_multiple}")
    
    # Calculate future EPS
    future_eps = eps * (1 + growth_rate) ** years
    
    # Calculate future value (target price)
    future_value = future_eps * eps_multiple
    
    # Calculate entry price for desired return
    entry_price = future_value / (1 + desired_return) ** years
    
    # Calculate implied return if current price is provided
    implied_return = None
    if current_price is not None and current_price > 0:
        implied_return = (future_value / current_price) ** (1 / years) - 1
    
    return {
        'current_eps': eps,
        'growth_rate': growth_rate,
        'years': years,
        'eps_multiple': eps_multiple,
        'desired_return': desired_return,
        'future_eps': future_eps,
        'future_value': future_value,
        'entry_price': entry_price,
        'current_price': current_price,
        'implied_return': implied_return,
        'intrinsic_value': future_value / (1 + desired_return) ** years
    }

print("Defining main...")

# Example usage
if __name__ == "__main__":
    print("Running example calculation...")
    
    # Example with Apple's data
    result = calculate_hopper_eps_valuation(
        eps=6.24,           # Current EPS
        growth_rate=0.07,   # 7% annual growth
        years=5,            # 5-year projection
        eps_multiple=30,    # Target P/E ratio
        desired_return=0.15, # 15% desired annual return
        current_price=187.52 # Current stock price
    )
    
    print("\nResults:")
    print(f"Current EPS: ${result['current_eps']:.2f}")
    print(f"Future EPS (after {result['years']} years): ${result['future_eps']:.2f}")
    print(f"Future Value: ${result['future_value']:.2f}")
    print(f"Entry Price for {result['desired_return']*100:.0f}% Return: ${result['entry_price']:.2f}")
    
    if result['implied_return'] is not None:
        print(f"Implied Return at Current Price: {result['implied_return']*100:.2f}%")
    
    print(f"Intrinsic Value: ${result['intrinsic_value']:.2f}")
    
    print("\nScript completed.") 