#!/usr/bin/env python3
"""
Mock Valuation Functions

This module provides mock implementations of the valuation functions for testing purposes.
"""

def calculate_fcf_per_share_valuation(fcf_per_share, growth_rate, years, fcf_yield, current_price=None):
    """
    Calculate intrinsic value based on FCF per share with growth projections.
    
    Args:
        fcf_per_share: Free Cash Flow per share (TTM)
        growth_rate: Annual growth rate (%)
        years: Number of years to project
        fcf_yield: Target FCF yield (%)
        current_price: Current market price (optional)
        
    Returns:
        Dictionary with valuation results
    """
    # Project FCF growth
    projected_fcf = fcf_per_share * (1 + growth_rate / 100) ** years
    
    # Calculate intrinsic value based on target FCF yield
    intrinsic_value = projected_fcf * (100 / fcf_yield)
    
    # Calculate upside/downside if current price is provided
    upside_downside = None
    if current_price and current_price > 0:
        upside_downside = (intrinsic_value / current_price - 1) * 100
    
    return {
        "fcf_per_share": fcf_per_share,
        "growth_rate": growth_rate,
        "years": years,
        "fcf_yield": fcf_yield,
        "projected_fcf": projected_fcf,
        "intrinsic_value": intrinsic_value,
        "upside_downside": upside_downside
    }

def calculate_eps_based_valuation(eps, growth_rate, years, terminal_pe, current_price=None):
    """
    Calculate intrinsic value based on EPS with growth projections.
    
    Args:
        eps: Earnings Per Share (TTM)
        growth_rate: Annual growth rate (%)
        years: Number of years to project
        terminal_pe: Terminal P/E ratio
        current_price: Current market price (optional)
        
    Returns:
        Dictionary with valuation results
    """
    # Project EPS growth
    projected_eps = eps * (1 + growth_rate / 100) ** years
    
    # Calculate intrinsic value based on terminal P/E
    intrinsic_value = projected_eps * terminal_pe
    
    # Calculate upside/downside if current price is provided
    upside_downside = None
    if current_price and current_price > 0:
        upside_downside = (intrinsic_value / current_price - 1) * 100
    
    return {
        "eps": eps,
        "growth_rate": growth_rate,
        "years": years,
        "terminal_pe": terminal_pe,
        "projected_eps": projected_eps,
        "intrinsic_value": intrinsic_value,
        "upside_downside": upside_downside
    }

def calculate_ev_ebitda_valuation(ebitda, growth_rate, years, discount_rate, net_debt, shares_outstanding, current_price=None):
    """
    Calculate intrinsic value based on EV/EBITDA with growth projections.
    
    Args:
        ebitda: EBITDA (TTM)
        growth_rate: Annual growth rate (%)
        years: Number of years to project
        discount_rate: Discount rate (%)
        net_debt: Net debt
        shares_outstanding: Shares outstanding
        current_price: Current market price (optional)
        
    Returns:
        Dictionary with valuation results
    """
    # Project EBITDA growth
    projected_ebitda = ebitda * (1 + growth_rate / 100) ** years
    
    # Calculate enterprise value (simplified)
    ev_multiple = 10  # Typical EV/EBITDA multiple
    enterprise_value = projected_ebitda * ev_multiple
    
    # Calculate equity value
    equity_value = enterprise_value - net_debt
    
    # Calculate intrinsic value per share
    intrinsic_value = equity_value / shares_outstanding if shares_outstanding > 0 else 0
    
    # Calculate upside/downside if current price is provided
    upside_downside = None
    if current_price and current_price > 0:
        upside_downside = (intrinsic_value / current_price - 1) * 100
    
    return {
        "ebitda": ebitda,
        "growth_rate": growth_rate,
        "years": years,
        "discount_rate": discount_rate,
        "projected_ebitda": projected_ebitda,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "intrinsic_value": intrinsic_value,
        "upside_downside": upside_downside
    }

def calculate_weighted_average_valuation(valuations, weights, current_price=None):
    """
    Calculate weighted average valuation based on multiple valuation methods.
    
    Args:
        valuations: List of intrinsic values from different methods
        weights: List of weights for each valuation method
        current_price: Current market price (optional)
        
    Returns:
        Dictionary with weighted valuation results
    """
    # Normalize weights
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights] if total_weight > 0 else [1 / len(weights)] * len(weights)
    
    # Calculate weighted average
    weighted_sum = sum(v * w for v, w in zip(valuations, normalized_weights))
    
    # Calculate upside/downside if current price is provided
    upside_downside = None
    if current_price and current_price > 0:
        upside_downside = (weighted_sum / current_price - 1) * 100
    
    return {
        "valuations": valuations,
        "weights": weights,
        "normalized_weights": normalized_weights,
        "intrinsic_value": weighted_sum,
        "upside_downside": upside_downside
    }

def calculate_entry_price(target_price, desired_return):
    """
    Calculate entry price based on target price and desired return.
    
    Args:
        target_price: Target price
        desired_return: Desired return (%)
        
    Returns:
        Entry price
    """
    return target_price / (1 + desired_return / 100)

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
    
    # Check if the intrinsic value is outside the reasonable range
    if modified_result['intrinsic_value'] > max_value:
        modified_result['intrinsic_value'] = max_value
        modified_result['upside_downside'] = (max_value / current_price - 1) * 100
        modified_result['is_adjusted'] = True
    elif modified_result['intrinsic_value'] < min_value:
        modified_result['intrinsic_value'] = min_value
        modified_result['upside_downside'] = (min_value / current_price - 1) * 100
        modified_result['is_adjusted'] = True
    else:
        modified_result['is_adjusted'] = False
    
    return modified_result 