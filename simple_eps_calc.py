#!/usr/bin/env python3
"""
Simple EPS-based Valuation Calculator
"""

# Input parameters
current_eps = 6.24        # Current EPS
growth_rate = 0.07        # 7% annual growth
years = 5                 # 5-year projection
eps_multiple = 30         # Target P/E ratio
desired_return = 0.15     # 15% desired annual return
current_price = 187.52    # Current stock price

# Open a file to write results
with open('eps_valuation_results.txt', 'w') as f:
    f.write("Original Parameters:\n")
    f.write(f"Current EPS: ${current_eps}\n")
    f.write(f"Growth Rate: {growth_rate*100:.1f}%\n")
    f.write(f"Years: {years}\n")
    f.write(f"EPS Multiple (P/E): {eps_multiple}\n")
    f.write(f"Desired Return: {desired_return*100:.1f}%\n")
    f.write(f"Current Price: ${current_price}\n\n")
    
    # Calculate future EPS
    future_eps = current_eps * (1 + growth_rate) ** years
    f.write(f"Future EPS (after {years} years): ${future_eps:.2f}\n")
    
    # Calculate future value (target price)
    future_value = future_eps * eps_multiple
    f.write(f"Future Value: ${future_value:.2f}\n")
    
    # Calculate entry price for desired return
    entry_price = future_value / (1 + desired_return) ** years
    f.write(f"Entry Price for {desired_return*100:.0f}% Return: ${entry_price:.2f}\n")
    
    # Calculate implied return at current price
    implied_return = (future_value / current_price) ** (1 / years) - 1
    f.write(f"Implied Return at Current Price: {implied_return*100:.2f}%\n")
    
    # Calculate intrinsic value (same as entry price in this model)
    intrinsic_value = entry_price
    f.write(f"Intrinsic Value: ${intrinsic_value:.2f}\n\n")
    
    # Try to match Qualtrim's results
    f.write("Attempting to match Qualtrim's results:\n")
    
    # Try different growth rates
    f.write("\nTrying different growth rates:\n")
    for test_growth in [0.065, 0.06, 0.055, 0.05]:
        future_eps = current_eps * (1 + test_growth) ** years
        future_value = future_eps * eps_multiple
        entry_price = future_value / (1 + desired_return) ** years
        implied_return = (future_value / current_price) ** (1 / years) - 1
        f.write(f"Growth={test_growth*100:.1f}%: Entry=${entry_price:.2f}, Return={implied_return*100:.2f}%\n")
    
    # Try different EPS multiples
    f.write("\nTrying different EPS multiples:\n")
    for test_multiple in [28, 26, 24, 22]:
        future_eps = current_eps * (1 + growth_rate) ** years
        future_value = future_eps * test_multiple
        entry_price = future_value / (1 + desired_return) ** years
        implied_return = (future_value / current_price) ** (1 / years) - 1
        f.write(f"P/E={test_multiple}: Entry=${entry_price:.2f}, Return={implied_return*100:.2f}%\n")
    
    # Try a combination that might match Qualtrim's results
    f.write("\nTrying combinations to match Qualtrim's results:\n")
    
    # Combination 1: Higher EPS, lower growth, lower P/E
    test_eps = 6.30
    test_growth = 0.05
    test_multiple = 24
    
    future_eps = test_eps * (1 + test_growth) ** years
    future_value = future_eps * test_multiple
    entry_price = future_value / (1 + desired_return) ** years
    implied_return = (future_value / current_price) ** (1 / years) - 1
    
    f.write(f"Combination 1: EPS=${test_eps:.2f}, Growth={test_growth*100:.1f}%, P/E={test_multiple}\n")
    f.write(f"Entry Price: ${entry_price:.2f}, Implied Return: {implied_return*100:.2f}%\n\n")
    
    # Combination 2: Try to match the entry price
    test_eps = 6.30
    test_growth = 0.07
    test_multiple = 30
    test_desired_return = 0.10  # Lower desired return
    
    future_eps = test_eps * (1 + test_growth) ** years
    future_value = future_eps * test_multiple
    entry_price = future_value / (1 + test_desired_return) ** years
    implied_return = (future_value / current_price) ** (1 / years) - 1
    
    f.write(f"Combination 2: EPS=${test_eps:.2f}, Growth={test_growth*100:.1f}%, P/E={test_multiple}, Desired Return={test_desired_return*100:.1f}%\n")
    f.write(f"Entry Price: ${entry_price:.2f}, Implied Return: {implied_return*100:.2f}%\n\n")
    
    # Compare with Qualtrim results
    f.write("Qualtrim's reported results:\n")
    f.write(f"Entry Price: $132.00\n")
    f.write(f"Implied Return: 2.14%\n")

print(f"Results written to eps_valuation_results.txt") 