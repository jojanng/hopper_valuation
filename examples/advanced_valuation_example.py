#!/usr/bin/env python3
"""
Advanced Valuation Service Example

This script demonstrates advanced valuation techniques including:
1. FCF/share-based valuation with user-defined growth rates
2. EPS-based valuation with user-defined growth rates
3. Entry price calculations for desired returns over specific time periods
4. Quarterly projections for future valuations
"""

import asyncio
import logging
import os
import sys
from pprint import pprint
import argparse
from datetime import datetime, timedelta
import numpy as np

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

def calculate_fcf_per_share_valuation(fcf_per_share, growth_rate, years, fcf_yield, discount_rate):
    """
    Calculate intrinsic value and growth path based on FCF/share.
    
    Args:
        fcf_per_share: Free Cash Flow per share (current)
        growth_rate: Expected growth rate (decimal)
        years: Number of years to project
        fcf_yield: Expected FCF yield for terminal value
        discount_rate: Discount rate / required return
        
    Returns:
        Dict: Valuation results
    """
    # Ensure inputs are valid
    if fcf_per_share <= 0:
        return {
            "intrinsic_value": 0,
            "estimated_value": 0,
            "growth_path": []
        }
    
    try:
        # Calculate future FCF per share
        future_fcf_per_share = fcf_per_share * (1 + growth_rate) ** years
        
        # Calculate terminal value based on FCF yield
        terminal_value = future_fcf_per_share / fcf_yield
        
        # Calculate present value (intrinsic value)
        intrinsic_value = terminal_value / (1 + discount_rate) ** years
        
        # Generate growth path for visualization
        growth_path = []
        for year in range(years + 1):
            year_fcf = fcf_per_share * (1 + growth_rate) ** year
            year_value = year_fcf / fcf_yield
            growth_path.append({
                "year": year,
                "fcf_per_share": year_fcf,
                "value": year_value
            })
        
        # Return the results
        return {
            "intrinsic_value": intrinsic_value,
            "estimated_value": intrinsic_value,  # For compatibility
            "terminal_value": terminal_value,
            "future_fcf_per_share": future_fcf_per_share,
            "years": years,
            "growth_rate": growth_rate,
            "discount_rate": discount_rate,
            "fcf_yield": fcf_yield,
            "growth_path": growth_path
        }
    except Exception as e:
        logger.error(f"Error in FCF/share valuation: {str(e)}")
        return {
            "intrinsic_value": 0,
            "estimated_value": 0,
            "growth_path": [],
            "error": str(e)
        }

def calculate_eps_based_valuation(eps, growth_rate, years, terminal_pe=15, discount_rate=0.1):
    """
    Calculate intrinsic value based on EPS with growth projections.
    
    Args:
        eps: Current earnings per share
        growth_rate: Expected annual growth rate for EPS
        years: Number of years to project
        terminal_pe: Terminal P/E ratio to apply
        discount_rate: Discount rate to apply
        
    Returns:
        Dictionary with valuation results
    """
    # For high-growth companies, use a higher terminal P/E
    if growth_rate > 0.25:  # If growth rate > 25%
        adjusted_terminal_pe = max(terminal_pe, 25)  # Use at least 25x P/E
    elif growth_rate > 0.15:  # If growth rate > 15%
        adjusted_terminal_pe = max(terminal_pe, 20)  # Use at least 20x P/E
    else:
        adjusted_terminal_pe = terminal_pe
    
    # Project EPS for each year
    projected_eps = []
    for year in range(1, years + 1):
        projected_eps.append(eps * (1 + growth_rate) ** year)
    
    # Calculate terminal value using P/E method
    terminal_eps = projected_eps[-1]
    terminal_value = terminal_eps * adjusted_terminal_pe
    
    # Calculate present value of projected EPS (assuming earnings are distributed or reinvested at same return)
    pv_eps = 0
    for year, eps_val in enumerate(projected_eps, 1):
        pv_eps += eps_val / (1 + discount_rate) ** year
    
    # Calculate present value of terminal value
    pv_terminal = terminal_value / (1 + discount_rate) ** years
    
    # Calculate intrinsic value (sum of present values)
    intrinsic_value = pv_eps + pv_terminal
    
    # Create quarterly projections
    quarterly_projections = []
    current_date = datetime.now()
    current_year = current_date.year
    current_quarter = (current_date.month - 1) // 3 + 1
    
    for quarter in range(1, years * 4 + 1):
        # Calculate the projected year and quarter
        projected_quarter = current_quarter + quarter
        projected_year = current_year + (projected_quarter - 1) // 4
        projected_quarter = ((projected_quarter - 1) % 4) + 1
        
        # Calculate the growth and values
        quarter_growth = (1 + growth_rate) ** (quarter / 4)
        quarter_eps = eps * quarter_growth
        quarter_value = quarter_eps * adjusted_terminal_pe
        
        quarterly_projections.append({
            'date': f"{projected_year}-Q{projected_quarter}",
            'eps': quarter_eps,
            'estimated_value': quarter_value
        })
    
    return {
        'intrinsic_value': intrinsic_value,
        'projected_eps': projected_eps,
        'terminal_value': terminal_value,
        'terminal_pe': adjusted_terminal_pe,
        'pv_eps': pv_eps,
        'pv_terminal': pv_terminal,
        'quarterly_projections': quarterly_projections
    }

def calculate_entry_price(current_price, target_value, desired_return, years):
    """
    Calculate the entry price needed to achieve a desired return over a specific time period.
    
    Args:
        current_price: Current market price
        target_value: Target future value
        desired_return: Desired annual return (e.g., 0.15 for 15%)
        years: Number of years for the investment
        
    Returns:
        Dictionary with entry price calculations
    """
    # Calculate the future value with the desired return
    future_value_desired = current_price * (1 + desired_return) ** years
    
    # Calculate the entry price needed to achieve the target value
    entry_price_for_target = target_value / (1 + desired_return) ** years
    
    # Calculate the discount needed from current price
    discount_needed = (current_price - entry_price_for_target) / current_price * 100
    
    # Calculate the implied return if buying at current price
    implied_return = (target_value / current_price) ** (1 / years) - 1
    
    return {
        'current_price': current_price,
        'target_value': target_value,
        'desired_return': desired_return,
        'years': years,
        'future_value_desired': future_value_desired,
        'entry_price_for_target': entry_price_for_target,
        'discount_needed': discount_needed,
        'implied_return': implied_return
    }

def calculate_ev_ebitda_valuation(ebitda, growth_rate, years=5, discount_rate=0.1, net_debt=0, shares_outstanding=1):
    """
    Calculate intrinsic value based on EV/EBITDA with growth projections.
    
    Args:
        ebitda: Current EBITDA
        growth_rate: Expected annual growth rate for EBITDA
        years: Number of years to project
        discount_rate: Discount rate to apply
        net_debt: Total debt minus cash and cash equivalents
        shares_outstanding: Number of shares outstanding
        
    Returns:
        Dictionary with valuation results
    """
    # Calculate target EV/EBITDA multiple based on growth rate
    # Higher growth rates justify higher multiples
    base_multiple = 6.0  # Base multiple for zero growth
    growth_factor = 10.0  # Multiple increase per 10% growth
    
    # Calculate the target multiple (capped between 5 and 20)
    target_multiple = base_multiple + (growth_rate * 100 * growth_factor / 10)
    target_multiple = max(min(target_multiple, 20), 5)
    
    # Project EBITDA for each year
    projected_ebitda = []
    for year in range(1, years + 1):
        projected_ebitda.append(ebitda * (1 + growth_rate) ** year)
    
    # Calculate terminal value using EV/EBITDA method
    terminal_ebitda = projected_ebitda[-1]
    terminal_value = terminal_ebitda * target_multiple
    
    # Calculate present value of projected EBITDA and terminal value
    pv_ebitda = 0
    for year, ebitda_val in enumerate(projected_ebitda, 1):
        pv_ebitda += ebitda_val / (1 + discount_rate) ** year
    
    pv_terminal = terminal_value / (1 + discount_rate) ** years
    
    # Calculate enterprise value
    enterprise_value = pv_ebitda + pv_terminal
    
    # Calculate equity value by subtracting net debt
    equity_value = enterprise_value - net_debt
    
    # Calculate per share value
    per_share_value = equity_value / shares_outstanding
    
    # Create quarterly projections
    quarterly_projections = []
    current_date = datetime.now()
    current_year = current_date.year
    current_quarter = (current_date.month - 1) // 3 + 1
    
    for quarter in range(1, years * 4 + 1):
        # Calculate the projected year and quarter
        projected_quarter = current_quarter + quarter
        projected_year = current_year + (projected_quarter - 1) // 4
        projected_quarter = ((projected_quarter - 1) % 4) + 1
        
        # Calculate the growth and values
        quarter_growth = (1 + growth_rate) ** (quarter / 4)
        quarter_ebitda = ebitda * quarter_growth
        quarter_ev = quarter_ebitda * target_multiple
        quarter_equity = quarter_ev - net_debt
        quarter_value = quarter_equity / shares_outstanding
        
        quarterly_projections.append({
            'date': f"{projected_year}-Q{projected_quarter}",
            'ebitda': quarter_ebitda,
            'estimated_value': quarter_value
        })
    
    return {
        'intrinsic_value': per_share_value,
        'projected_ebitda': projected_ebitda,
        'terminal_value': terminal_value,
        'ev_ebitda_multiple': target_multiple,
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'pv_ebitda': pv_ebitda,
        'pv_terminal': pv_terminal,
        'quarterly_projections': quarterly_projections
    }

def calculate_weighted_average_valuation(fcf_valuation, eps_valuation, ev_ebitda_valuation=None, fcf_weight=0.5, eps_weight=0.3, ev_ebitda_weight=0.2):
    """
    Calculate a weighted average valuation based on FCF, EPS, and EV/EBITDA valuations.
    
    Args:
        fcf_valuation: FCF-based valuation result
        eps_valuation: EPS-based valuation result
        ev_ebitda_valuation: EV/EBITDA-based valuation result (optional)
        fcf_weight: Weight to assign to FCF valuation (0-1)
        eps_weight: Weight to assign to EPS valuation (0-1)
        ev_ebitda_weight: Weight to assign to EV/EBITDA valuation (0-1)
        
    Returns:
        Dictionary with weighted valuation results
    """
    # If EV/EBITDA valuation is not provided, adjust weights
    if ev_ebitda_valuation is None:
        total_weight = fcf_weight + eps_weight
        fcf_weight = fcf_weight / total_weight
        eps_weight = eps_weight / total_weight
        ev_ebitda_weight = 0
    else:
        # Ensure weights sum to 1
        total_weight = fcf_weight + eps_weight + ev_ebitda_weight
        fcf_weight = fcf_weight / total_weight
        eps_weight = eps_weight / total_weight
        ev_ebitda_weight = ev_ebitda_weight / total_weight
    
    # Calculate weighted intrinsic value
    weighted_value = (
        fcf_valuation['intrinsic_value'] * fcf_weight + 
        eps_valuation['intrinsic_value'] * eps_weight
    )
    
    if ev_ebitda_valuation:
        weighted_value += ev_ebitda_valuation['intrinsic_value'] * ev_ebitda_weight
    
    # Create weighted quarterly projections
    weighted_projections = []
    for i in range(len(fcf_valuation['quarterly_projections'])):
        fcf_proj = fcf_valuation['quarterly_projections'][i]
        eps_proj = eps_valuation['quarterly_projections'][i]
        
        if ev_ebitda_valuation:
            ev_ebitda_proj = ev_ebitda_valuation['quarterly_projections'][i]
            weighted_value_proj = (
                fcf_proj['estimated_value'] * fcf_weight + 
                eps_proj['estimated_value'] * eps_weight +
                ev_ebitda_proj['estimated_value'] * ev_ebitda_weight
            )
        else:
            weighted_value_proj = (
                fcf_proj['estimated_value'] * fcf_weight + 
                eps_proj['estimated_value'] * eps_weight
            )
        
        weighted_projections.append({
            'date': fcf_proj['date'],
            'weighted_value': weighted_value_proj
        })
    
    return {
        'intrinsic_value': weighted_value,
        'fcf_valuation': fcf_valuation['intrinsic_value'],
        'eps_valuation': eps_valuation['intrinsic_value'],
        'ev_ebitda_valuation': ev_ebitda_valuation['intrinsic_value'] if ev_ebitda_valuation else None,
        'fcf_weight': fcf_weight,
        'eps_weight': eps_weight,
        'ev_ebitda_weight': ev_ebitda_weight,
        'quarterly_projections': weighted_projections
    }

def perform_sensitivity_analysis(fcf_per_share, eps, current_price, years=5, discount_rate=0.1):
    """
    Perform sensitivity analysis on key valuation parameters.
    
    Args:
        fcf_per_share: Current free cash flow per share
        eps: Current earnings per share
        current_price: Current market price
        years: Projection years
        discount_rate: Base discount rate
        
    Returns:
        Dictionary with sensitivity analysis results
    """
    # Define ranges for sensitivity analysis
    fcf_growth_rates = [0.10, 0.15, 0.20, 0.25]
    eps_growth_rates = [0.15, 0.20, 0.25, 0.30]
    fcf_yields = [0.03, 0.04, 0.05, 0.06]
    terminal_pes = [12, 15, 18, 21]
    discount_rates = [0.08, 0.10, 0.12, 0.14]
    
    # FCF growth rate sensitivity
    fcf_growth_sensitivity = []
    for growth_rate in fcf_growth_rates:
        result = calculate_fcf_per_share_valuation(
            fcf_per_share=fcf_per_share,
            growth_rate=growth_rate,
            years=years,
            discount_rate=discount_rate,
            fcf_yield=0.04
        )
        fcf_growth_sensitivity.append({
            'growth_rate': growth_rate,
            'intrinsic_value': result['intrinsic_value'],
            'upside': (result['intrinsic_value'] / current_price - 1) * 100
        })
    
    # EPS growth rate sensitivity
    eps_growth_sensitivity = []
    for growth_rate in eps_growth_rates:
        result = calculate_eps_based_valuation(
            eps=eps,
            growth_rate=growth_rate,
            years=years,
            discount_rate=discount_rate,
            terminal_pe=15
        )
        eps_growth_sensitivity.append({
            'growth_rate': growth_rate,
            'intrinsic_value': result['intrinsic_value'],
            'upside': (result['intrinsic_value'] / current_price - 1) * 100
        })
    
    # FCF yield sensitivity
    fcf_yield_sensitivity = []
    for fcf_yield in fcf_yields:
        result = calculate_fcf_per_share_valuation(
            fcf_per_share=fcf_per_share,
            growth_rate=0.15,
            years=years,
            discount_rate=discount_rate,
            fcf_yield=fcf_yield
        )
        fcf_yield_sensitivity.append({
            'fcf_yield': fcf_yield,
            'intrinsic_value': result['intrinsic_value'],
            'upside': (result['intrinsic_value'] / current_price - 1) * 100
        })
    
    # Terminal P/E sensitivity
    terminal_pe_sensitivity = []
    for terminal_pe in terminal_pes:
        result = calculate_eps_based_valuation(
            eps=eps,
            growth_rate=0.20,
            years=years,
            discount_rate=discount_rate,
            terminal_pe=terminal_pe
        )
        terminal_pe_sensitivity.append({
            'terminal_pe': terminal_pe,
            'intrinsic_value': result['intrinsic_value'],
            'upside': (result['intrinsic_value'] / current_price - 1) * 100
        })
    
    # Discount rate sensitivity
    discount_rate_sensitivity = []
    for dr in discount_rates:
        fcf_result = calculate_fcf_per_share_valuation(
            fcf_per_share=fcf_per_share,
            growth_rate=0.15,
            years=years,
            discount_rate=dr,
            fcf_yield=0.04
        )
        eps_result = calculate_eps_based_valuation(
            eps=eps,
            growth_rate=0.20,
            years=years,
            discount_rate=dr,
            terminal_pe=15
        )
        weighted_result = calculate_weighted_average_valuation(fcf_result, eps_result)
        
        discount_rate_sensitivity.append({
            'discount_rate': dr,
            'fcf_value': fcf_result['intrinsic_value'],
            'eps_value': eps_result['intrinsic_value'],
            'weighted_value': weighted_result['intrinsic_value'],
            'weighted_upside': (weighted_result['intrinsic_value'] / current_price - 1) * 100
        })
    
    return {
        'fcf_growth_sensitivity': fcf_growth_sensitivity,
        'eps_growth_sensitivity': eps_growth_sensitivity,
        'fcf_yield_sensitivity': fcf_yield_sensitivity,
        'terminal_pe_sensitivity': terminal_pe_sensitivity,
        'discount_rate_sensitivity': discount_rate_sensitivity
    }

def print_fcf_valuation_summary(result, current_price, fcf_per_share, growth_rate, years, fcf_yield):
    """Print a formatted summary of the FCF-based valuation results."""
    print("\n=== FCF/Share Based Valuation Summary ===")
    print(f"Current FCF/Share: ${fcf_per_share:.2f}")
    print(f"Expected Growth Rate: {growth_rate*100:.2f}%")
    print(f"Target FCF Yield: {fcf_yield*100:.2f}%")
    print(f"Projection Years: {years}")
    
    print(f"\nIntrinsic Value: ${result['intrinsic_value']:.2f}")
    print(f"Current Price: ${current_price:.2f}")
    upside = (result['intrinsic_value'] / current_price - 1) * 100
    print(f"Upside/Downside: {upside:.2f}%")
    
    print("\nProjected FCF/Share:")
    for year, fcf in enumerate(result['growth_path'], 1):
        print(f"  Year {year}: ${fcf['value']:.2f}")
    
    print(f"\nTerminal Value: ${result['terminal_value']:.2f}")
    print(f"Present Value of FCF: ${result['pv_ebitda']:.2f}")
    print(f"Present Value of Terminal Value: ${result['pv_terminal']:.2f}")
    
    print("\nQuarterly Projections:")
    for i, quarter in enumerate(result['quarterly_projections']):
        if i % 4 == 0:  # Print only yearly projections to keep output manageable
            print(f"  {quarter['date']}: FCF=${quarter['fcf_per_share']:.2f}, Value=${quarter['estimated_value']:.2f}")

def print_eps_valuation_summary(result, current_price, eps, growth_rate, years, terminal_pe):
    """Print a formatted summary of the EPS-based valuation results."""
    print("\n=== EPS Based Valuation Summary ===")
    print(f"Current EPS: ${eps:.2f}")
    print(f"Expected Growth Rate: {growth_rate*100:.2f}%")
    print(f"Terminal P/E Ratio: {result['terminal_pe']:.2f}x")
    print(f"Projection Years: {years}")
    
    print(f"\nIntrinsic Value: ${result['intrinsic_value']:.2f}")
    print(f"Current Price: ${current_price:.2f}")
    upside = (result['intrinsic_value'] / current_price - 1) * 100
    print(f"Upside/Downside: {upside:.2f}%")
    
    print("\nProjected EPS:")
    for year, eps_val in enumerate(result['projected_eps'], 1):
        print(f"  Year {year}: ${eps_val:.2f}")
    
    print(f"\nTerminal Value: ${result['terminal_value']:.2f}")
    print(f"Present Value of EPS: ${result['pv_eps']:.2f}")
    print(f"Present Value of Terminal Value: ${result['pv_terminal']:.2f}")
    
    print("\nQuarterly Projections:")
    for i, quarter in enumerate(result['quarterly_projections']):
        if i % 4 == 0:  # Print only yearly projections to keep output manageable
            print(f"  {quarter['date']}: EPS=${quarter['eps']:.2f}, Value=${quarter['estimated_value']:.2f}")

def print_ev_ebitda_valuation_summary(result, current_price, ebitda, growth_rate, years, net_debt, shares_outstanding):
    """Print a formatted summary of the EV/EBITDA-based valuation results."""
    print("\n=== EV/EBITDA Based Valuation Summary ===")
    print(f"Current EBITDA: ${ebitda/1e9:.2f}B")
    print(f"EBITDA/Share: ${ebitda/shares_outstanding:.2f}")
    print(f"Expected Growth Rate: {growth_rate*100:.2f}%")
    print(f"Target EV/EBITDA Multiple: {result['ev_ebitda_multiple']:.2f}x")
    print(f"Net Debt: ${net_debt/1e9:.2f}B")
    print(f"Projection Years: {years}")
    
    print(f"\nIntrinsic Value: ${result['intrinsic_value']:.2f}")
    print(f"Current Price: ${current_price:.2f}")
    upside = (result['intrinsic_value'] / current_price - 1) * 100
    print(f"Upside/Downside: {upside:.2f}%")
    
    print("\nProjected EBITDA:")
    for year, ebitda_val in enumerate(result['projected_ebitda'], 1):
        print(f"  Year {year}: ${ebitda_val/1e9:.2f}B")
    
    print(f"\nEnterprise Value: ${result['enterprise_value']/1e9:.2f}B")
    print(f"Equity Value: ${result['equity_value']/1e9:.2f}B")
    print(f"Terminal Value: ${result['terminal_value']/1e9:.2f}B")
    print(f"Present Value of EBITDA: ${result['pv_ebitda']/1e9:.2f}B")
    print(f"Present Value of Terminal Value: ${result['pv_terminal']/1e9:.2f}B")
    
    print("\nQuarterly Projections:")
    for i, quarter in enumerate(result['quarterly_projections']):
        if i % 4 == 0:  # Print only yearly projections to keep output manageable
            print(f"  {quarter['date']}: EBITDA=${quarter['ebitda']/1e9:.2f}B, Value=${quarter['estimated_value']:.2f}")

def print_entry_price_analysis(result):
    """Print a formatted summary of the entry price analysis."""
    print(f"\n=== Entry Price Analysis for {result['years']} Year Investment ===")
    print(f"Current Price: ${result['current_price']:.2f}")
    print(f"Target Future Value: ${result['target_value']:.2f}")
    print(f"Desired Annual Return: {result['desired_return']*100:.2f}%")
    
    print(f"\nFuture Value with {result['desired_return']*100:.2f}% Return: ${result['future_value_desired']:.2f}")
    print(f"Entry Price Needed for Target Value: ${result['entry_price_for_target']:.2f}")
    
    if result['discount_needed'] > 0:
        print(f"Discount Needed from Current Price: {result['discount_needed']:.2f}%")
    else:
        print(f"Premium Allowed over Current Price: {-result['discount_needed']:.2f}%")
    
    print(f"Implied Annual Return at Current Price: {result['implied_return']*100:.2f}%")

def print_weighted_valuation_summary(result, current_price):
    """Print a formatted summary of the weighted average valuation results."""
    print("\n=== Weighted Average Valuation Summary ===")
    print(f"FCF-Based Valuation: ${result['fcf_valuation']:.2f} (Weight: {result['fcf_weight']*100:.0f}%)")
    print(f"EPS-Based Valuation: ${result['eps_valuation']:.2f} (Weight: {result['eps_weight']*100:.0f}%)")
    
    if result['ev_ebitda_valuation']:
        print(f"EV/EBITDA-Based Valuation: ${result['ev_ebitda_valuation']:.2f} (Weight: {result['ev_ebitda_weight']*100:.0f}%)")
    
    print(f"\nWeighted Intrinsic Value: ${result['intrinsic_value']:.2f}")
    print(f"Current Price: ${current_price:.2f}")
    upside = (result['intrinsic_value'] / current_price - 1) * 100
    print(f"Upside/Downside: {upside:.2f}%")
    
    print("\nWeighted Quarterly Projections:")
    for i, quarter in enumerate(result['quarterly_projections']):
        if i % 4 == 0:  # Print only yearly projections to keep output manageable
            print(f"  {quarter['date']}: ${quarter['weighted_value']:.2f}")

def print_sensitivity_analysis(sensitivity_results, current_price):
    """Print a formatted summary of the sensitivity analysis results."""
    print("\n=== Sensitivity Analysis ===")
    
    print("\nFCF Growth Rate Sensitivity:")
    print("  Growth Rate | Intrinsic Value | Upside/Downside")
    print("  ------------------------------------")
    for item in sensitivity_results['fcf_growth_sensitivity']:
        print(f"  {item['growth_rate']*100:8.1f}% | ${item['intrinsic_value']:14.2f} | {item['upside']:+14.2f}%")
    
    print("\nEPS Growth Rate Sensitivity:")
    print("  Growth Rate | Intrinsic Value | Upside/Downside")
    print("  ------------------------------------")
    for item in sensitivity_results['eps_growth_sensitivity']:
        print(f"  {item['growth_rate']*100:8.1f}% | ${item['intrinsic_value']:14.2f} | {item['upside']:+14.2f}%")
    
    print("\nFCF Yield Sensitivity:")
    print("  FCF Yield | Intrinsic Value | Upside/Downside")
    print("  ------------------------------------")
    for item in sensitivity_results['fcf_yield_sensitivity']:
        print(f"  {item['fcf_yield']*100:7.1f}% | ${item['intrinsic_value']:14.2f} | {item['upside']:+14.2f}%")
    
    print("\nTerminal P/E Sensitivity:")
    print("  P/E Ratio | Intrinsic Value | Upside/Downside")
    print("  ------------------------------------")
    for item in sensitivity_results['terminal_pe_sensitivity']:
        print(f"  {item['terminal_pe']:9.1f}x | ${item['intrinsic_value']:14.2f} | {item['upside']:+14.2f}%")
    
    print("\nDiscount Rate Sensitivity:")
    print("  Discount | FCF Value | EPS Value | Weighted Value | Weighted Upside")
    print("  -----------------------------------------------------------------")
    for item in sensitivity_results['discount_rate_sensitivity']:
        print(f"  {item['discount_rate']*100:7.1f}% | ${item['fcf_value']:9.2f} | ${item['eps_value']:9.2f} | ${item['weighted_value']:14.2f} | {item['weighted_upside']:+14.2f}%")

async def main():
    """Main function to demonstrate the advanced valuation techniques."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Advanced Stock Valuation Example')
    parser.add_argument('--symbol', type=str, default='AAPL', help='Stock symbol to analyze')
    parser.add_argument('--fcf-growth', type=float, default=0.15, help='Expected FCF growth rate (decimal)')
    parser.add_argument('--eps-growth', type=float, default=0.20, help='Expected EPS growth rate (decimal)')
    parser.add_argument('--ebitda-growth', type=float, default=0.18, help='Expected EBITDA growth rate (decimal)')
    parser.add_argument('--fcf-yield', type=float, default=0.04, help='Target FCF yield (decimal)')
    parser.add_argument('--terminal-pe', type=float, default=15, help='Terminal P/E ratio')
    parser.add_argument('--desired-return', type=float, default=0.15, help='Desired annual return (decimal)')
    parser.add_argument('--years', type=int, default=5, help='Projection years')
    parser.add_argument('--fcf-weight', type=float, default=0.5, help='Weight for FCF valuation in weighted average (0-1)')
    parser.add_argument('--eps-weight', type=float, default=0.3, help='Weight for EPS valuation in weighted average (0-1)')
    parser.add_argument('--ev-ebitda-weight', type=float, default=0.2, help='Weight for EV/EBITDA valuation in weighted average (0-1)')
    parser.add_argument('--sbc-impact', type=float, default=0.0, help='Stock-Based Compensation impact as percentage reduction (decimal)')
    parser.add_argument('--use-ev-ebitda', action='store_true', help='Include EV/EBITDA model in valuation')
    parser.add_argument('--sensitivity', action='store_true', help='Perform sensitivity analysis')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Create a settings object
    settings = Settings()
    
    # Create a MarketDataService instance
    market_data_service = MarketDataService(config=settings)
    
    # Create a ValuationService instance
    valuation_service = ValuationService(market_data_service, config={})
    
    symbol = args.symbol
    
    print("\n" + "="*80)
    print(f"ADVANCED VALUATION EXAMPLE FOR {symbol}")
    print("="*80)
    
    # Get current price and financial data
    try:
        current_price = await market_data_service.get_current_price(symbol)
        financial_data = await market_data_service.get_financial_data(symbol)
        
        print(f"\n=== Current Market Data for {symbol} ===")
        print(f"Current Price: ${current_price:.2f}")
        
        # Extract key financial metrics
        shares_outstanding = financial_data.get('sharesOutstanding', 0)
        fcf = financial_data.get('freeCashFlow', 0)
        net_income = financial_data.get('netIncome', 0)
        ebitda = financial_data.get('ebitda', 0)
        total_debt = financial_data.get('totalDebt', 0)
        cash_and_equivalents = financial_data.get('cashAndEquivalents', 0)
        net_debt = total_debt - cash_and_equivalents
        
        # Calculate per share metrics
        fcf_per_share = fcf / shares_outstanding if shares_outstanding > 0 else 0
        eps = net_income / shares_outstanding if shares_outstanding > 0 else 0
        
        # Apply SBC impact adjustment if provided
        sbc_impact = args.sbc_impact
        if sbc_impact > 0:
            adjusted_fcf_per_share = fcf_per_share * (1 - sbc_impact)
            adjusted_eps = eps * (1 - sbc_impact)
            adjusted_ebitda = ebitda * (1 - sbc_impact)
            print(f"Shares Outstanding: {shares_outstanding/1e9:.2f}B")
            print(f"Free Cash Flow (TTM): ${fcf/1e9:.2f}B")
            print(f"Net Income (TTM): ${net_income/1e9:.2f}B")
            print(f"EBITDA (TTM): ${ebitda/1e9:.2f}B")
            print(f"Total Debt: ${total_debt/1e9:.2f}B")
            print(f"Cash & Equivalents: ${cash_and_equivalents/1e9:.2f}B")
            print(f"Net Debt: ${net_debt/1e9:.2f}B")
            print(f"FCF/Share (TTM): ${fcf_per_share:.2f}")
            print(f"EPS (TTM): ${eps:.2f}")
            print(f"SBC Impact: -{sbc_impact*100:.2f}%")
            print(f"Adjusted FCF/Share (TTM): ${adjusted_fcf_per_share:.2f}")
            print(f"Adjusted EPS (TTM): ${adjusted_eps:.2f}")
            print(f"Adjusted EBITDA (TTM): ${adjusted_ebitda/1e9:.2f}B")
            fcf_per_share = adjusted_fcf_per_share
            eps = adjusted_eps
            ebitda = adjusted_ebitda
        else:
            print(f"Shares Outstanding: {shares_outstanding/1e9:.2f}B")
            print(f"Free Cash Flow (TTM): ${fcf/1e9:.2f}B")
            print(f"Net Income (TTM): ${net_income/1e9:.2f}B")
            print(f"EBITDA (TTM): ${ebitda/1e9:.2f}B")
            print(f"Total Debt: ${total_debt/1e9:.2f}B")
            print(f"Cash & Equivalents: ${cash_and_equivalents/1e9:.2f}B")
            print(f"Net Debt: ${net_debt/1e9:.2f}B")
            print(f"FCF/Share (TTM): ${fcf_per_share:.2f}")
            print(f"EPS (TTM): ${eps:.2f}")
        
        # FCF/Share based valuation
        fcf_growth_rate = args.fcf_growth
        fcf_yield = args.fcf_yield
        years = args.years
        
        fcf_result = calculate_fcf_per_share_valuation(
            fcf_per_share=fcf_per_share,
            growth_rate=fcf_growth_rate,
            years=years,
            discount_rate=0.10,
            fcf_yield=fcf_yield
        )
        
        print_fcf_valuation_summary(
            fcf_result, 
            current_price, 
            fcf_per_share, 
            fcf_growth_rate, 
            years, 
            fcf_yield
        )
        
        # EPS based valuation
        eps_growth_rate = args.eps_growth
        terminal_pe = args.terminal_pe
        
        eps_result = calculate_eps_based_valuation(
            eps=eps,
            growth_rate=eps_growth_rate,
            years=years,
            terminal_pe=terminal_pe
        )
        
        print_eps_valuation_summary(
            eps_result, 
            current_price, 
            eps, 
            eps_growth_rate, 
            years, 
            terminal_pe
        )
        
        # EV/EBITDA based valuation (if requested)
        ev_ebitda_result = None
        if args.use_ev_ebitda and ebitda > 0:
            ebitda_growth_rate = args.ebitda_growth
            
            ev_ebitda_result = calculate_ev_ebitda_valuation(
                ebitda=ebitda,
                growth_rate=ebitda_growth_rate,
                years=years,
                net_debt=net_debt,
                shares_outstanding=shares_outstanding
            )
            
            print_ev_ebitda_valuation_summary(
                ev_ebitda_result,
                current_price,
                ebitda,
                ebitda_growth_rate,
                years,
                net_debt,
                shares_outstanding
            )
        
        # Weighted average valuation
        fcf_weight = args.fcf_weight
        eps_weight = args.eps_weight
        ev_ebitda_weight = args.ev_ebitda_weight
        
        weighted_result = calculate_weighted_average_valuation(
            fcf_valuation=fcf_result,
            eps_valuation=eps_result,
            ev_ebitda_valuation=ev_ebitda_result,
            fcf_weight=fcf_weight,
            eps_weight=eps_weight,
            ev_ebitda_weight=ev_ebitda_weight
        )
        
        print_weighted_valuation_summary(
            weighted_result,
            current_price
        )
        
        # Entry price analysis for weighted valuation
        desired_return = args.desired_return
        
        weighted_entry_price = calculate_entry_price(
            current_price=current_price,
            target_value=weighted_result['intrinsic_value'],
            desired_return=desired_return,
            years=years
        )
        
        print_entry_price_analysis(weighted_entry_price)
        
        # Sensitivity analysis
        if args.sensitivity:
            sensitivity_results = perform_sensitivity_analysis(
                fcf_per_share=fcf_per_share,
                eps=eps,
                current_price=current_price,
                years=years
            )
            
            print_sensitivity_analysis(sensitivity_results, current_price)
        
        # Entry price analysis for FCF-based valuation
        fcf_entry_price = calculate_entry_price(
            current_price=current_price,
            target_value=fcf_result['intrinsic_value'],
            desired_return=desired_return,
            years=years
        )
        
        print_entry_price_analysis(fcf_entry_price)
        
        # Entry price analysis for EPS-based valuation
        eps_entry_price = calculate_entry_price(
            current_price=current_price,
            target_value=eps_result['intrinsic_value'],
            desired_return=desired_return,
            years=years
        )
        
        print_entry_price_analysis(eps_entry_price)
        
        # Entry price analysis for EV/EBITDA-based valuation (if available)
        if ev_ebitda_result:
            ev_ebitda_entry_price = calculate_entry_price(
                current_price=current_price,
                target_value=ev_ebitda_result['intrinsic_value'],
                desired_return=desired_return,
                years=years
            )
            
            print_entry_price_analysis(ev_ebitda_entry_price)
        
        # Entry price analysis for 2-year investment
        short_term_years = 2
        
        # Use the 2-year projection from quarterly projections
        fcf_2yr_value = fcf_result['growth_path'][10]['value']  # 11th year (2 years)
        eps_2yr_value = eps_result['projected_eps'][10]  # 11th year (2 years)
        weighted_2yr_value = weighted_result['quarterly_projections'][10]['weighted_value']  # 11th quarter (2 years)
        
        fcf_2yr_entry = calculate_entry_price(
            current_price=current_price,
            target_value=fcf_2yr_value,
            desired_return=desired_return,
            years=short_term_years
        )
        
        eps_2yr_entry = calculate_entry_price(
            current_price=current_price,
            target_value=eps_2yr_value,
            desired_return=desired_return,
            years=short_term_years
        )
        
        weighted_2yr_entry = calculate_entry_price(
            current_price=current_price,
            target_value=weighted_2yr_value,
            desired_return=desired_return,
            years=short_term_years
        )
        
        print("\n=== 2-Year Investment Analysis ===")
        print(f"FCF-Based 2-Year Target: ${fcf_2yr_value:.2f}")
        print(f"Entry Price for {desired_return*100:.0f}% Annual Return: ${fcf_2yr_entry['entry_price_for_target']:.2f}")
        print(f"Implied Annual Return at Current Price: {fcf_2yr_entry['implied_return']*100:.2f}%")
        
        print(f"\nEPS-Based 2-Year Target: ${eps_2yr_value:.2f}")
        print(f"Entry Price for {desired_return*100:.0f}% Annual Return: ${eps_2yr_entry['entry_price_for_target']:.2f}")
        print(f"Implied Annual Return at Current Price: {eps_2yr_entry['implied_return']*100:.2f}%")
        
        print(f"\nWeighted 2-Year Target: ${weighted_2yr_value:.2f}")
        print(f"Entry Price for {desired_return*100:.0f}% Annual Return: ${weighted_2yr_entry['entry_price_for_target']:.2f}")
        print(f"Implied Annual Return at Current Price: {weighted_2yr_entry['implied_return']*100:.2f}%")
        
    except Exception as e:
        logger.error(f"Error in valuation process: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print(f"ADVANCED VALUATION COMPLETE FOR {symbol}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main()) 