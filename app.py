#!/usr/bin/env python3
"""
Advanced Stock Valuation Web Application

This Flask application provides a web interface to the advanced stock valuation
functionality from the hopper_backend services and advanced_valuation_example.py.
It offers the same precision and accuracy as the command-line version.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
import numpy as np
from flask import Flask, request, jsonify, render_template, send_from_directory

# Add the parent directory to the path so we can import the hopper_backend package
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

# Import hopper_backend services
from hopper_backend.services.market_data.service import MarketDataService
from hopper_backend.services.valuation.service import ValuationService
from hopper_backend.config.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize hopper_backend services
settings = Settings()
market_data_service = MarketDataService(config=settings)
valuation_service = ValuationService(market_data_service, config={})

# Helper function to run async functions in Flask
def run_async(coro):
    """Run an async coroutine in the Flask context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/')
def index():
    """Render the main page of the application."""
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """Get available stock symbols."""
    try:
        # Get symbols dynamically from the market data service
        symbols = run_async(market_data_service.get_available_symbols())
        return jsonify({"symbols": symbols})
    except Exception as e:
        logger.error(f"Error fetching symbols: {str(e)}")
        # Return a basic list as fallback
        return jsonify({
            "symbols": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'PLTR', 'ASML', 
                       'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'INTC', 'VZ', 'ADBE', 
                       'NFLX', 'CSCO', 'PFE', 'CRM', 'ABT', 'KO', 'PEP', 'NKE', 'T', 'MRK', 'DIS', 'VOO']
        })

@app.route('/api/valuation', methods=['POST'])
def perform_valuation():
    """Perform advanced valuation analysis based on the provided parameters."""
    try:
        # Get request data
        data = request.json
        symbol = data.get('symbol', 'AAPL').upper()
        
        logger.info(f"Performing valuation for symbol: {symbol}")
        
        # Extract parameters with defaults
        fcf_growth = data.get('fcf_growth', 15) / 100  # Convert to decimal
        eps_growth = data.get('eps_growth', 20) / 100  # Convert to decimal
        ebitda_growth = data.get('ebitda_growth', 18) / 100  # Convert to decimal
        fcf_yield = data.get('fcf_yield', 4) / 100  # Convert to decimal
        terminal_pe = data.get('terminal_pe', 15)
        eps_multiple = data.get('eps_multiple', 20)  # New EPS multiple parameter
        desired_return = data.get('desired_return', 15) / 100  # Convert to decimal
        years = int(data.get('years', 5))
        projection_years = int(data.get('projection_years', 5))  # New projection years parameter
        sbc_impact = data.get('sbc_impact', 0) / 100  # Convert to decimal
        
        # Weights for weighted average calculation
        fcf_weight = data.get('fcf_weight', 50) / 100  # Convert to decimal
        eps_weight = data.get('eps_weight', 30) / 100  # Convert to decimal
        ev_ebitda_weight = data.get('ev_ebitda_weight', 20) / 100  # Convert to decimal
        use_ev_ebitda = data.get('use_ev_ebitda', True)
        include_sensitivity = data.get('sensitivity', False)
        
        try:
            # Fetch market data using the hopper_backend services
            current_price = run_async(market_data_service.get_current_price(symbol))
            financial_data = run_async(market_data_service.get_financial_data(symbol))
            
            # Extract relevant data
            shares_outstanding = financial_data.get('sharesOutstanding', 0)
            fcf = financial_data.get('freeCashFlow', 0)
            net_income = financial_data.get('netIncome', 0)
            ebitda = financial_data.get('ebitda', 0)
            total_debt = financial_data.get('totalDebt', 0)
            cash_and_equivalents = financial_data.get('cashAndEquivalents', 0)
            net_debt = total_debt - cash_and_equivalents
            
            # Calculate per share metrics with safety checks
            if shares_outstanding <= 0:
                logger.warning(f"Invalid shares outstanding ({shares_outstanding}) for {symbol}")
                shares_outstanding = 1  # Use 1 as a fallback to avoid division by zero

            fcf_per_share = fcf / shares_outstanding
            eps = net_income / shares_outstanding
            
            # Calculate P/E ratio with safety check
            pe_ratio = 0
            if eps > 0:
                pe_ratio = current_price / eps
            else:
                logger.warning(f"Invalid EPS ({eps}) for {symbol}, P/E ratio set to 0")
            
            # Apply SBC impact if provided
            if sbc_impact > 0:
                fcf = fcf * (1 - sbc_impact)
                net_income = net_income * (1 - sbc_impact)
                ebitda = ebitda * (1 - sbc_impact)
                fcf_per_share = fcf / shares_outstanding
                eps = net_income / shares_outstanding
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return jsonify({
                "error": f"Symbol '{symbol}' not found or error fetching data."
            }), 404
        
        # Prepare market data for response
        market_data_response = {
            "current_price": current_price,
            "shares_outstanding": shares_outstanding,
            "fcf": fcf,
            "net_income": net_income,
            "ebitda": ebitda,
            "fcf_per_share": fcf_per_share,
            "eps": eps,
            "pe_ratio": pe_ratio,  # Add P/E ratio to market data
            "net_debt": net_debt
        }
        
        # Use the valuation service to calculate intrinsic values
        custom_weights = {
            "dcf": fcf_weight,
            "pe": eps_weight,
            "ev_ebitda": ev_ebitda_weight if use_ev_ebitda else 0
        }
        
        try:
            # For simplicity, we'll use our own calculation functions instead of the valuation service
            # In a production environment, you would use the valuation service directly
            from examples.advanced_valuation_example import (
                calculate_fcf_per_share_valuation,
                calculate_ev_ebitda_valuation,
                calculate_weighted_average_valuation,
                calculate_entry_price
            )
            # Import the new hopper-style EPS valuation function and sanity check
            from hopper_backend_eps import calculate_eps_based_valuation, apply_sanity_check
            
            # Calculate valuations
            try:
                fcf_valuation = calculate_fcf_per_share_valuation(
                    fcf_per_share=fcf_per_share,
                    growth_rate=fcf_growth,
                    years=years,
                    fcf_yield=fcf_yield,
                    discount_rate=desired_return
                )
                logger.info(f"FCF valuation keys: {list(fcf_valuation.keys())}")
            except Exception as e:
                logger.error(f"Error in FCF valuation: {str(e)}")
                fcf_valuation = {"intrinsic_value": 0, "estimated_value": 0}
            
            try:
                eps_valuation = calculate_eps_based_valuation(
                    eps=eps,
                    growth_rate=eps_growth,
                    years=years,
                    terminal_pe=eps_multiple,  # Use eps_multiple instead of terminal_pe
                    discount_rate=desired_return,
                    current_price=current_price
                )
                logger.info(f"EPS valuation using eps_multiple: {eps_multiple}")
                logger.info(f"EPS valuation keys: {list(eps_valuation.keys())}")
            except Exception as e:
                logger.error(f"Error in EPS valuation: {str(e)}")
                eps_valuation = {"intrinsic_value": 0, "estimated_value": 0}
            
            ev_ebitda_valuation = None
            if use_ev_ebitda:
                try:
                    ev_ebitda_valuation = calculate_ev_ebitda_valuation(
                        ebitda=ebitda,
                        growth_rate=ebitda_growth,
                        years=years,
                        discount_rate=desired_return,
                        net_debt=net_debt,
                        shares_outstanding=shares_outstanding
                    )
                    logger.info(f"EV/EBITDA valuation keys: {list(ev_ebitda_valuation.keys())}")
                except Exception as e:
                    logger.error(f"Error in EV/EBITDA valuation: {str(e)}")
                    ev_ebitda_valuation = {"intrinsic_value": 0, "estimated_value": 0}
            
            # Calculate weighted average
            valuations = []
            weights = []
            
            valuations.append(fcf_valuation['intrinsic_value'])
            weights.append(fcf_weight)
            
            valuations.append(eps_valuation['intrinsic_value'])
            weights.append(eps_weight)
            
            if use_ev_ebitda and ev_ebitda_valuation:
                valuations.append(ev_ebitda_valuation['intrinsic_value'])
                weights.append(ev_ebitda_weight)
            
            # Call the weighted average function with the correct parameters
            try:
                weighted_valuation = calculate_weighted_average_valuation(
                    fcf_valuation=fcf_valuation,
                    eps_valuation=eps_valuation,
                    ev_ebitda_valuation=ev_ebitda_valuation if use_ev_ebitda else None,
                    fcf_weight=fcf_weight,
                    eps_weight=eps_weight,
                    ev_ebitda_weight=ev_ebitda_weight
                )
                logger.info(f"Weighted valuation keys: {list(weighted_valuation.keys())}")
            except Exception as e:
                logger.error(f"Error in weighted valuation: {str(e)}")
                # Create a basic weighted valuation result
                weighted_value = sum(v * w for v, w in zip(valuations, weights)) / sum(weights)
                weighted_valuation = {
                    "intrinsic_value": weighted_value,
                    "estimated_value": weighted_value,
                    "weighted_value": weighted_value
                }
            
            # Apply sanity checks
            try:
                fcf_valuation = apply_sanity_check(fcf_valuation, current_price)
            except Exception as e:
                logger.error(f"Error in FCF sanity check: {str(e)}")
                
            try:
                eps_valuation = apply_sanity_check(eps_valuation, current_price)
            except Exception as e:
                logger.error(f"Error in EPS sanity check: {str(e)}")
                
            if use_ev_ebitda and ev_ebitda_valuation:
                try:
                    ev_ebitda_valuation = apply_sanity_check(ev_ebitda_valuation, current_price)
                except Exception as e:
                    logger.error(f"Error in EV/EBITDA sanity check: {str(e)}")
                    
            try:
                weighted_valuation = apply_sanity_check(weighted_valuation, current_price)
            except Exception as e:
                logger.error(f"Error in weighted valuation sanity check: {str(e)}")
                
            # Calculate entry prices
            try:
                fcf_entry = calculate_entry_price(current_price, fcf_valuation['intrinsic_value'], desired_return, years)
                fcf_valuation['entry_price'] = fcf_entry['entry_price_for_target']
                fcf_valuation['implied_return'] = fcf_entry['implied_return'] * 100
            except Exception as e:
                logger.error(f"Error calculating FCF entry price: {str(e)}")
                fcf_valuation['entry_price'] = 0
                fcf_valuation['implied_return'] = 0
            
            try:
                eps_entry = calculate_entry_price(current_price, eps_valuation['intrinsic_value'], desired_return, years)
                # For EPS valuation, we want to use the intrinsic value directly as the entry price
                # This matches Hopper's approach
                eps_valuation['entry_price'] = eps_valuation['intrinsic_value']
                eps_valuation['implied_return'] = eps_entry['implied_return'] * 100
                logger.info(f"EPS entry price: ${eps_valuation['entry_price']:.2f}, implied return: {eps_valuation['implied_return']:.2f}%")
            except Exception as e:
                logger.error(f"Error calculating EPS entry price: {str(e)}")
                eps_valuation['entry_price'] = 0
                eps_valuation['implied_return'] = 0
            
            if use_ev_ebitda and ev_ebitda_valuation:
                try:
                    ev_ebitda_entry = calculate_entry_price(current_price, ev_ebitda_valuation['intrinsic_value'], desired_return, years)
                    ev_ebitda_valuation['entry_price'] = ev_ebitda_entry['entry_price_for_target']
                    ev_ebitda_valuation['implied_return'] = ev_ebitda_entry['implied_return'] * 100
                except Exception as e:
                    logger.error(f"Error calculating EV/EBITDA entry price: {str(e)}")
                    ev_ebitda_valuation['entry_price'] = 0
                    ev_ebitda_valuation['implied_return'] = 0
            
            try:
                weighted_entry = calculate_entry_price(current_price, weighted_valuation['intrinsic_value'], desired_return, years)
                weighted_valuation['entry_price'] = weighted_entry['entry_price_for_target']
                weighted_valuation['implied_return'] = weighted_entry['implied_return'] * 100
            except Exception as e:
                logger.error(f"Error calculating weighted entry price: {str(e)}")
                weighted_valuation['entry_price'] = 0
                weighted_valuation['implied_return'] = 0
            
            # Prepare valuation results for response
            valuation_results = {
                "fcf_valuation": fcf_valuation,
                "eps_valuation": eps_valuation,
                "weighted_valuation": weighted_valuation
            }
            
            if use_ev_ebitda and ev_ebitda_valuation:
                valuation_results["ev_ebitda_valuation"] = ev_ebitda_valuation
            
        except Exception as e:
            logger.error(f"Error calculating valuation: {str(e)}")
            return jsonify({"error": f"Error calculating valuation: {str(e)}"}), 500
        
        # Generate projections
        current_year = datetime.now().year
        
        # FCF projections
        fcf_projections = []
        fcf_projections.append({
            "year": current_year,
            "value": fcf_per_share,
            "growth": 0
        })
        
        for i in range(1, years + 1):
            projected_fcf = fcf_per_share * (1 + fcf_growth) ** i
            fcf_projections.append({
                "year": current_year + i,
                "value": projected_fcf,
                "growth": fcf_growth * 100  # Convert back to percentage
            })
        
        # EPS projections
        eps_projections = []
        eps_projections.append({
            "year": current_year,
            "value": eps,
            "growth": 0
        })
        
        for i in range(1, years + 1):
            projected_eps = eps * (1 + eps_growth) ** i
            eps_projections.append({
                "year": current_year + i,
                "value": projected_eps,
                "growth": eps_growth * 100  # Convert back to percentage
            })
        
        # EBITDA projections
        ebitda_projections = []
        ebitda_projections.append({
            "year": current_year,
            "value": ebitda / shares_outstanding,
            "growth": 0
        })
        
        for i in range(1, years + 1):
            projected_ebitda = (ebitda / shares_outstanding) * (1 + ebitda_growth) ** i
            ebitda_projections.append({
                "year": current_year + i,
                "value": projected_ebitda,
                "growth": ebitda_growth * 100  # Convert back to percentage
            })
        
        # Generate quarterly projections
        quarterly_projections = []
        current_quarter = (datetime.now().month - 1) // 3 + 1
        
        for i in range(8):  # Next 8 quarters
            quarter_offset = (current_quarter + i - 1) % 4 + 1
            year_offset = (current_quarter + i - 1) // 4
            quarter_year = current_year + year_offset
            quarter_label = f"{quarter_year}-Q{quarter_offset}"
            
            # Calculate quarterly values (simplified as annual / 4 with growth)
            quarter_fcf = fcf_per_share * (1 + fcf_growth) ** (year_offset + (i / 4)) / 4
            quarter_eps = eps * (1 + eps_growth) ** (year_offset + (i / 4)) / 4
            quarter_ebitda = ebitda * (1 + ebitda_growth) ** (year_offset + (i / 4)) / 4
            
            quarterly_projections.append({
                "quarter": quarter_label,
                "fcf_per_share": quarter_fcf,
                "eps": quarter_eps,
                "ebitda": quarter_ebitda
            })
        
        # Calculate 2-year targets
        two_year_fcf_target = fcf_per_share * (1 + fcf_growth) ** 2
        two_year_eps_target = eps * (1 + eps_growth) ** 2
        
        two_year_fcf_price = two_year_fcf_target / fcf_yield
        two_year_eps_price = two_year_eps_target * eps_multiple  # Use the new EPS multiple instead of terminal_pe
        
        two_year_weighted_price = (two_year_fcf_price * fcf_weight + 
                                  two_year_eps_price * eps_weight) / (fcf_weight + eps_weight)
        
        two_year_fcf_entry = calculate_entry_price(current_price, two_year_fcf_price, desired_return * 2, 2)
        two_year_eps_entry = calculate_entry_price(current_price, two_year_eps_price, desired_return * 2, 2)
        two_year_weighted_entry = calculate_entry_price(current_price, two_year_weighted_price, desired_return * 2, 2)
        
        two_year_targets = {
            "fcf": {
                "target_price": two_year_fcf_price,
                "entry_price": two_year_fcf_entry['entry_price_for_target'],
                "implied_return": two_year_fcf_entry['implied_return'] * 100 / 2  # Annualized
            },
            "eps": {
                "target_price": two_year_eps_price,
                "entry_price": two_year_eps_entry['entry_price_for_target'],
                "implied_return": two_year_eps_entry['implied_return'] * 100 / 2  # Annualized
            },
            "weighted": {
                "target_price": two_year_weighted_price,
                "entry_price": two_year_weighted_entry['entry_price_for_target'],
                "implied_return": two_year_weighted_entry['implied_return'] * 100 / 2  # Annualized
            }
        }
        
        # Prepare projections for response
        projections_response = {
            "fcf_projections": fcf_projections,
            "eps_projections": eps_projections,
            "ebitda_projections": ebitda_projections,
            "quarterly_projections": quarterly_projections,
            "two_year_targets": two_year_targets
        }
        
        # Generate sensitivity analysis if requested
        sensitivity_analysis = None
        if include_sensitivity:
            # FCF Growth sensitivity
            fcf_growth_sensitivity = {}
            for growth in range(int(fcf_growth * 100) - 10, int(fcf_growth * 100) + 15, 5):
                if growth < 0:
                    continue
                    
                fcf_growth_sensitivity[str(growth)] = {}
                for yield_val in range(int(fcf_yield * 100) - 2, int(fcf_yield * 100) + 3):
                    if yield_val <= 0:
                        continue
                        
                    val = calculate_fcf_per_share_valuation(
                        fcf_per_share=fcf_per_share,
                        growth_rate=growth / 100,
                        years=years,
                        fcf_yield=yield_val / 100,
                        discount_rate=desired_return
                    )
                    fcf_growth_sensitivity[str(growth)][str(yield_val)] = val['intrinsic_value']
            
            # EPS Growth sensitivity
            eps_growth_sensitivity = {}
            for growth in range(int(eps_growth * 100) - 10, int(eps_growth * 100) + 15, 5):
                if growth < 0:
                    continue
                    
                eps_growth_sensitivity[str(growth)] = {}
                for pe in range(int(eps_multiple) - 5, int(eps_multiple) + 6, 2):  # Use eps_multiple instead of terminal_pe
                    if pe <= 0:
                        continue
                        
                    val = calculate_eps_based_valuation(
                        eps=eps,
                        growth_rate=growth / 100,
                        years=years,
                        terminal_pe=pe,
                        discount_rate=desired_return
                    )
                    eps_growth_sensitivity[str(growth)][str(pe)] = val['intrinsic_value']
            
            # FCF Yield sensitivity
            fcf_yield_sensitivity = {}
            for yield_val in range(int(fcf_yield * 100) - 2, int(fcf_yield * 100) + 3):
                if yield_val <= 0:
                    continue
                    
                fcf_yield_sensitivity[str(yield_val)] = {}
                for growth in range(int(fcf_growth * 100) - 10, int(fcf_growth * 100) + 15, 5):
                    if growth < 0:
                        continue
                        
                    val = calculate_fcf_per_share_valuation(
                        fcf_per_share=fcf_per_share,
                        growth_rate=growth / 100,
                        years=years,
                        fcf_yield=yield_val / 100,
                        discount_rate=desired_return
                    )
                    fcf_yield_sensitivity[str(yield_val)][str(growth)] = val['intrinsic_value']
            
            # Terminal P/E sensitivity
            terminal_pe_sensitivity = {}
            for pe in range(int(eps_multiple) - 5, int(eps_multiple) + 6, 2):  # Use eps_multiple instead of terminal_pe
                if pe <= 0:
                    continue
                    
                terminal_pe_sensitivity[str(pe)] = {}
                for growth in range(int(eps_growth * 100) - 10, int(eps_growth * 100) + 15, 5):
                    if growth < 0:
                        continue
                        
                    val = calculate_eps_based_valuation(
                        eps=eps,
                        growth_rate=growth / 100,
                        years=years,
                        terminal_pe=pe,
                        discount_rate=desired_return
                    )
                    terminal_pe_sensitivity[str(pe)][str(growth)] = val['intrinsic_value']
            
            # Discount Rate sensitivity (for EV/EBITDA)
            discount_rate_sensitivity = {}
            if use_ev_ebitda:
                for rate in range(int(desired_return * 100) - 5, int(desired_return * 100) + 6, 2):
                    if rate <= 0:
                        continue
                        
                    discount_rate_sensitivity[str(rate)] = {}
                    for growth in range(int(ebitda_growth * 100) - 10, int(ebitda_growth * 100) + 15, 5):
                        if growth < 0:
                            continue
                            
                        val = calculate_ev_ebitda_valuation(
                            ebitda=ebitda,
                            growth_rate=growth / 100,
                            years=years,
                            discount_rate=rate / 100,
                            net_debt=net_debt,
                            shares_outstanding=shares_outstanding
                        )
                        discount_rate_sensitivity[str(rate)][str(growth)] = val['intrinsic_value']
            
            sensitivity_analysis = {
                "fcf_growth": fcf_growth_sensitivity,
                "eps_growth": eps_growth_sensitivity,
                "fcf_yield": fcf_yield_sensitivity,
                "terminal_pe": terminal_pe_sensitivity
            }
            
            if use_ev_ebitda:
                sensitivity_analysis["discount_rate"] = discount_rate_sensitivity
        
        # Prepare final response
        response = {
            "market_data": market_data_response,
            "valuation_results": valuation_results,
            "projections": projections_response
        }
        
        if include_sensitivity:
            response["sensitivity_analysis"] = sensitivity_analysis
        
        logger.info(f"Completed valuation for {symbol}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error performing valuation: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 