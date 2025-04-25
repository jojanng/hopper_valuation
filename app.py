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
            "pe_ratio": pe_ratio,
            "net_debt": net_debt
        }
        
        # Additional parameters for enhanced DCF model
        try:
            historical_fcf = run_async(market_data_service.get_historical_fcf(symbol))
            logger.info(f"Historical FCF data for {symbol}: {historical_fcf}")
        except Exception as e:
            logger.warning(f"Error fetching historical FCF data: {str(e)}")
            # Create synthetic historical FCF data based on current FCF
            historical_fcf = [fcf * 0.9, fcf * 0.95, fcf]
            logger.info(f"Using synthetic historical FCF data: {historical_fcf}")
            
        try:
            risk_free_rate = run_async(market_data_service.get_risk_free_rate())
            logger.info(f"Risk-free rate: {risk_free_rate}")
        except Exception as e:
            logger.warning(f"Error fetching risk-free rate: {str(e)}")
            risk_free_rate = 0.035  # Use 3.5% as default risk-free rate
            
        try:
            industry_growth = run_async(market_data_service.get_industry_growth_rate(symbol))
            logger.info(f"Industry growth rate for {symbol}: {industry_growth}")
        except Exception as e:
            logger.warning(f"Error fetching industry growth rate: {str(e)}")
            industry_growth = fcf_growth * 0.8  # Use 80% of user-provided growth as fallback
            
        try:
            debt_to_equity = run_async(market_data_service.get_debt_to_equity(symbol))
            logger.info(f"Debt to equity for {symbol}: {debt_to_equity}")
        except Exception as e:
            logger.warning(f"Error fetching debt to equity: {str(e)}")
            debt_to_equity = 0.5  # Use 0.5 as default debt to equity
            
        try:
            cost_of_debt = run_async(market_data_service.get_cost_of_debt(symbol))
            logger.info(f"Cost of debt for {symbol}: {cost_of_debt}")
        except Exception as e:
            logger.warning(f"Error fetching cost of debt: {str(e)}")
            cost_of_debt = 0.05  # Use 5% as default cost of debt
            
        beta = financial_data.get('beta', 1.0)
        logger.info(f"Beta for {symbol}: {beta}")
        discount_rate = 0.10  # Default discount rate

        # Use the valuation service for calculations
        custom_weights = {
            "dcf": fcf_weight,
            "pe": eps_weight,
            "ev_ebitda": ev_ebitda_weight if use_ev_ebitda else 0
        }
        
        # Calculate DCF valuation
        try:
            # Validate input parameters for DCF calculation
            if fcf <= 0:
                logger.warning(f"FCF value for {symbol} is negative or zero: {fcf}")
                # Use historical FCF if available
                if isinstance(historical_fcf, list) and historical_fcf:
                    fcf = max(historical_fcf) if max(historical_fcf) > 0 else abs(fcf)
                else:
                    fcf = abs(fcf) if abs(fcf) > 0 else 1000000
            
            if shares_outstanding <= 0:
                logger.warning(f"Invalid shares outstanding for {symbol}: {shares_outstanding}")
                # Try to get shares from financial data
                shares_outstanding = financial_data.get('sharesOutstanding', 1000000)
                if shares_outstanding <= 0:
                    shares_outstanding = 1000000
            
            if discount_rate <= 0.01 or discount_rate >= 0.3:
                logger.warning(f"Invalid discount rate: {discount_rate}, adjusting to reasonable range")
                # Calculate WACC as fallback with additional validation
                try:
                    # Ensure all components are valid numbers
                    beta = float(beta) if beta is not None else 1.0
                    risk_free_rate = float(risk_free_rate) if risk_free_rate is not None else 0.035
                    debt_to_equity = float(debt_to_equity) if debt_to_equity is not None else 0.5
                    cost_of_debt = float(cost_of_debt) if cost_of_debt is not None else 0.05
                    
                    # Calculate WACC with bounds
                    wacc = (beta * 0.06 + risk_free_rate) * (1 - debt_to_equity) + cost_of_debt * debt_to_equity
                    discount_rate = max(0.08, min(0.25, wacc))
                except (TypeError, ValueError) as e:
                    logger.error(f"Error calculating WACC: {str(e)}")
                    discount_rate = 0.1
            
            if not isinstance(historical_fcf, list) or not historical_fcf:
                logger.warning(f"Invalid historical FCF data for {symbol}")
                # Create synthetic data with reasonable growth and validation
                try:
                    fcf = float(fcf) if fcf is not None else 1000000
                    historical_fcf = [fcf * 0.8, fcf * 0.9, fcf]
                except (TypeError, ValueError) as e:
                    logger.error(f"Error creating synthetic FCF data: {str(e)}")
                    historical_fcf = [1000000, 1100000, 1200000]
            
            # Calculate DCF valuation using the enhanced model with additional validation
            try:
                # Validate all inputs before calculation
                fcf = float(fcf) if fcf is not None else 1000000
                fcf_growth = float(fcf_growth) if fcf_growth is not None else 0.1
                discount_rate = float(discount_rate) if discount_rate is not None else 0.1
                years = int(years) if years is not None else 5
                net_debt = float(net_debt) if net_debt is not None else 0
                shares_outstanding = float(shares_outstanding) if shares_outstanding is not None else 1000000
                industry_growth = float(industry_growth) if industry_growth is not None else fcf_growth
                beta = float(beta) if beta is not None else 1.0
                risk_free_rate = float(risk_free_rate) if risk_free_rate is not None else 0.035
                debt_to_equity = float(debt_to_equity) if debt_to_equity is not None else 0.5
                cost_of_debt = float(cost_of_debt) if cost_of_debt is not None else 0.05
                
                dcf_result = run_async(valuation_service.dcf_model.calculate(
                    fcf=fcf,
                    growth_rate=fcf_growth,
                    discount_rate=discount_rate,
                    years=years,
                    terminal_growth=0.02,
                    net_debt=net_debt,
                    shares_outstanding=shares_outstanding,
                    historical_fcf=historical_fcf,
                    analyst_growth_estimate=fcf_growth,
                    industry_growth=industry_growth,
                    beta=beta,
                    risk_free_rate=risk_free_rate,
                    debt_to_equity=debt_to_equity,
                    cost_of_debt=cost_of_debt
                ))
                
                fcf_valuation = {
                    "intrinsic_value": dcf_result['per_share_value'],
                    "estimated_value": dcf_result['per_share_value'],
                    "projected_growth_rates": dcf_result.get('projected_growth_rates', []),
                    "wacc": dcf_result.get('wacc', discount_rate)
                }
                
                logger.info(f"FCF valuation using enhanced DCF model: {dcf_result['per_share_value']:.2f}")
                logger.info(f"Using WACC: {dcf_result.get('wacc', discount_rate):.2%}")
                
            except Exception as e:
                logger.error(f"Error in FCF valuation: {str(e)}")
                logger.error(f"FCF Value: {fcf}, Growth Rate: {fcf_growth}, Discount Rate: {discount_rate}")
                logger.error(f"Shares Outstanding: {shares_outstanding}, Net Debt: {net_debt}")
                
                # Fallback to basic DCF calculation with additional validation
                try:
                    # Simple DCF calculation as fallback with safety checks
                    future_fcf = []
                    terminal_value = 0
                    
                    # Calculate future cash flows with safety checks
                    current_fcf = float(fcf_per_share) if fcf_per_share is not None else float(fcf) / max(float(shares_outstanding), 1)
                    for year in range(1, years + 1):
                        # Apply declining growth rate with bounds
                        year_growth = float(fcf_growth) * (1 - 0.1 * (year-1)/years) if fcf_growth is not None else 0.1
                        year_growth = max(0.02, min(0.25, year_growth))  # Bound between 2% and 25%
                        
                        current_fcf = current_fcf * (1 + year_growth)
                        present_value = current_fcf / ((1 + float(discount_rate)) ** year)
                        future_fcf.append(present_value)
                    
                    # Terminal value calculation with safety checks
                    if current_fcf > 0 and float(discount_rate) > 0.02:
                        terminal_value = current_fcf * (1 + 0.02) / (float(discount_rate) - 0.02)
                        terminal_value = terminal_value / ((1 + float(discount_rate)) ** years)
                    
                    # Sum all future cash flows and terminal value
                    total_dcf_value = sum(future_fcf) + terminal_value
                    
                    # Adjust for net debt with safety checks
                    if float(shares_outstanding) > 0:
                        enterprise_value = total_dcf_value * float(shares_outstanding)
                        equity_value = enterprise_value - float(net_debt)
                        per_share_value = max(0, equity_value / float(shares_outstanding))  # Ensure non-negative
                    else:
                        per_share_value = 0
                    
                    fcf_valuation = {
                        "intrinsic_value": per_share_value,
                        "estimated_value": per_share_value,
                        "wacc": float(discount_rate),
                        "note": "Used fallback DCF calculation due to enhanced model failure"
                    }
                    
                    logger.info(f"Fallback DCF valuation: {per_share_value:.2f}")
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback DCF also failed: {str(fallback_error)}")
                    # Final fallback: use simple P/E based valuation
                    try:
                        eps = float(eps) if eps is not None else 0
                        eps_multiple = float(eps_multiple) if eps_multiple is not None else 15
                        per_share_value = eps * eps_multiple if eps > 0 else 0
                        fcf_valuation = {
                            "intrinsic_value": per_share_value,
                            "estimated_value": per_share_value,
                            "wacc": float(discount_rate) if discount_rate is not None else 0.1,
                            "note": "Used P/E based fallback due to DCF failures"
                        }
                    except Exception as e:
                        logger.error(f"P/E fallback failed: {str(e)}")
                        fcf_valuation = {"intrinsic_value": 0, "estimated_value": 0}
        
        except Exception as e:
            logger.error(f"Error in FCF valuation: {str(e)}")
            logger.error(f"FCF Value: {fcf}, Growth Rate: {fcf_growth}, Discount Rate: {discount_rate}")
            logger.error(f"Shares Outstanding: {shares_outstanding}, Net Debt: {net_debt}")
            
            # Fallback to basic DCF calculation if the enhanced model fails
            try:
                # Simple DCF calculation as fallback
                future_fcf = []
                terminal_value = 0
                
                # Calculate future cash flows with safety checks
                current_fcf = fcf_per_share if fcf_per_share > 0 else fcf / max(shares_outstanding, 1)
                for year in range(1, years + 1):
                    # Apply declining growth rate with bounds
                    year_growth = fcf_growth * (1 - 0.1 * (year-1)/years) if fcf_growth > 0 else fcf_growth
                    year_growth = max(0.02, min(0.25, year_growth))  # Bound between 2% and 25%
                    
                    current_fcf = current_fcf * (1 + year_growth)
                    present_value = current_fcf / ((1 + discount_rate) ** year)
                    future_fcf.append(present_value)
                
                # Terminal value calculation with safety checks
                if current_fcf > 0 and discount_rate > 0.02:
                    terminal_value = current_fcf * (1 + 0.02) / (discount_rate - 0.02)
                    terminal_value = terminal_value / ((1 + discount_rate) ** years)
                
                # Sum all future cash flows and terminal value
                total_dcf_value = sum(future_fcf) + terminal_value
                
                # Adjust for net debt with safety checks
                if shares_outstanding > 0:
                    enterprise_value = total_dcf_value * shares_outstanding
                    equity_value = enterprise_value - net_debt
                    per_share_value = max(0, equity_value / shares_outstanding)  # Ensure non-negative
                else:
                    per_share_value = 0
                
                fcf_valuation = {
                    "intrinsic_value": per_share_value,
                    "estimated_value": per_share_value,
                    "wacc": discount_rate,
                    "note": "Used fallback DCF calculation due to enhanced model failure"
                }
                
                logger.info(f"Fallback DCF valuation: {per_share_value:.2f}")
                
            except Exception as fallback_error:
                logger.error(f"Fallback DCF also failed: {str(fallback_error)}")
                # Final fallback: use simple P/E based valuation
                try:
                    per_share_value = eps * eps_multiple if eps > 0 else 0
                    fcf_valuation = {
                        "intrinsic_value": per_share_value,
                        "estimated_value": per_share_value,
                        "wacc": discount_rate,
                        "note": "Used P/E based fallback due to DCF failures"
                    }
                except Exception as e:
                    logger.error(f"P/E fallback failed: {str(e)}")
                    fcf_valuation = {"intrinsic_value": 0, "estimated_value": 0}
        
        try:
            # Use the backend PE model
            pe_result = run_async(valuation_service.pe_model.calculate(
                eps=eps,
                growth_rate=eps_growth,
                years=years,
                industry_pe=eps_multiple
            ))
            
            # Create a compatible response format
            eps_valuation = {
                "intrinsic_value": pe_result["fair_value"],
                "estimated_value": pe_result["fair_value"],
                "weighted_value": pe_result["fair_value"],
                "future_eps": pe_result.get("future_eps", 0),
                "future_value": pe_result.get("future_value", 0),
                "target_pe": pe_result.get("target_pe", eps_multiple)
            }
            
            logger.info(f"EPS valuation using PE model from backend: {pe_result['fair_value']:.2f}")
            
        except Exception as e:
            logger.error(f"Error in EPS valuation: {str(e)}")
            eps_valuation = {"intrinsic_value": 0, "estimated_value": 0}
        
        ev_ebitda_valuation = None
        if use_ev_ebitda:
            try:
                ev_ebitda_result = run_async(valuation_service.ev_ebitda_model.calculate(
                    ebitda=ebitda,
                    growth_rate=ebitda_growth,
                    net_debt=net_debt,
                    shares_outstanding=shares_outstanding
                ))
                
                ev_ebitda_valuation = {
                    "intrinsic_value": ev_ebitda_result["per_share_value"],
                    "estimated_value": ev_ebitda_result["per_share_value"]
                }
                
                logger.info(f"EV/EBITDA valuation: {ev_ebitda_result['per_share_value']:.2f}")
                
            except Exception as e:
                logger.error(f"Error in EV/EBITDA valuation: {str(e)}")
                ev_ebitda_valuation = {"intrinsic_value": 0, "estimated_value": 0}
        
        # Calculate weighted average
        valuations = []
        weights = []
        
        if fcf_valuation['intrinsic_value'] > 0:
            valuations.append(fcf_valuation['intrinsic_value'])
            weights.append(fcf_weight)
        
        if eps_valuation['intrinsic_value'] > 0:
            valuations.append(eps_valuation['intrinsic_value'])
            weights.append(eps_weight)
        
        if use_ev_ebitda and ev_ebitda_valuation and ev_ebitda_valuation['intrinsic_value'] > 0:
            valuations.append(ev_ebitda_valuation['intrinsic_value'])
            weights.append(ev_ebitda_weight)
        
        # Calculate weighted average
        weighted_value = 0
        if sum(weights) > 0:
            weighted_value = sum(v * w for v, w in zip(valuations, weights)) / sum(weights)
        
        # Create weighted valuation result
        weighted_valuation = {
            "intrinsic_value": weighted_value,
            "estimated_value": weighted_value,
            "weighted_value": weighted_value
        }
        
        # Prepare valuation results for response
        valuation_results = {
            "fcf_based": fcf_valuation["intrinsic_value"],
            "eps_based": eps_valuation["intrinsic_value"],
            "ev_ebitda_based": ev_ebitda_valuation["intrinsic_value"] if ev_ebitda_valuation else 0,
            "weighted_average": weighted_value,
            "upside_potential": (weighted_value / current_price - 1) * 100 if current_price > 0 else 0,
            "wacc": fcf_valuation.get("wacc", discount_rate)
        }
        
        # Generate projections for each growth model
        projections_response = {
            "fcf": [],
            "eps": [],
            "ebitda": [] if use_ev_ebitda else None
        }
        
        # Get current year for projections
        current_year = datetime.now().year
        

        # FCF Projections
        base_fcf = fcf_per_share
        previous_fcf = base_fcf
        for year in range(1, projection_years + 1):
            # Calculate tapering growth rate that declines over time
            # For very high growth rates (>50%), we taper more aggressively
            taper_factor = year / projection_years
            if fcf_growth > 0.5:  # 50%
                taper_factor = taper_factor * 1.5  # More aggressive tapering for high growth
            
            # Terminal growth rate of 2-3%
            terminal_growth = 0.02 + (0.01 * (1 - taper_factor))
            
            # Taper the growth rate towards terminal growth
            growth_rate_year = fcf_growth * (1 - taper_factor) + terminal_growth * taper_factor
            
            # Apply the growth rate to previous year's FCF instead of compounding from base
            projected_fcf = previous_fcf * (1 + growth_rate_year)
            previous_fcf = projected_fcf
            
            projections_response["fcf"].append({
                "year": str(current_year + year),
                "value": round(projected_fcf, 2),
                "growth": round(growth_rate_year * 100, 1)
            })
        
        # EPS Projections
        base_eps = eps
        for year in range(1, projection_years + 1):
            projected_eps = base_eps * (1 + eps_growth) ** year
            projections_response["eps"].append({
                "year": str(current_year + year),  # Convert to string to ensure proper formatting
                "value": round(projected_eps, 2),  # Round to 2 decimal places
                "growth": round(eps_growth * 100, 1)  # Round growth to 1 decimal place
            })
        
        # EBITDA Projections
        if use_ev_ebitda:
            base_ebitda = ebitda / shares_outstanding if shares_outstanding > 0 else 0
            for year in range(1, projection_years + 1):
                projected_ebitda = base_ebitda * (1 + ebitda_growth) ** year
                projections_response["ebitda"].append({
                    "year": str(current_year + year),  # Convert to string to ensure proper formatting
                    "value": round(projected_ebitda, 2),  # Round to 2 decimal places
                    "growth": round(ebitda_growth * 100, 1)  # Round growth to 1 decimal place
                })
        
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
                        
                    # Use enhanced DCF model
                    dcf_result = run_async(valuation_service.dcf_model.calculate(
                        fcf=fcf,
                        growth_rate=growth / 100,
                        discount_rate=discount_rate,
                        years=years,
                        terminal_growth=0.02,
                        net_debt=net_debt,
                        shares_outstanding=shares_outstanding,
                        historical_fcf=historical_fcf,
                        analyst_growth_estimate=growth / 100,
                        industry_growth=industry_growth,
                        beta=beta,
                        risk_free_rate=risk_free_rate,
                        debt_to_equity=debt_to_equity,
                        cost_of_debt=cost_of_debt
                    ))
                    
                    fcf_growth_sensitivity[str(growth)][str(yield_val)] = dcf_result['per_share_value']
            
            # EPS Growth sensitivity
            eps_growth_sensitivity = {}
            for growth in range(int(eps_growth * 100) - 10, int(eps_growth * 100) + 15, 5):
                if growth < 0:
                    continue
                    
                eps_growth_sensitivity[str(growth)] = {}
                for pe in range(int(eps_multiple) - 5, int(eps_multiple) + 6, 2):
                    if pe <= 0:
                        continue
                        
                    # Use the backend PE model
                    pe_result = run_async(valuation_service.pe_model.calculate(
                        eps=eps,
                        growth_rate=growth / 100,
                        years=years,
                        industry_pe=pe
                    ))
                    
                    eps_growth_sensitivity[str(growth)][str(pe)] = pe_result['fair_value']
            
            # FCF Yield sensitivity
            fcf_yield_sensitivity = {}
            for yield_val in range(int(fcf_yield * 100) - 2, int(fcf_yield * 100) + 3):
                if yield_val <= 0:
                    continue
                    
                fcf_yield_sensitivity[str(yield_val)] = {}
                for growth in range(int(fcf_growth * 100) - 10, int(fcf_growth * 100) + 15, 5):
                    if growth < 0:
                        continue
                        
                    # Use enhanced DCF model with different yield (affects terminal value)
                    dcf_result = run_async(valuation_service.dcf_model.calculate(
                        fcf=fcf,
                        growth_rate=growth / 100,
                        discount_rate=yield_val / 100,  # Use yield as discount rate for sensitivity
                        years=years,
                        terminal_growth=0.02,
                        net_debt=net_debt,
                        shares_outstanding=shares_outstanding,
                        historical_fcf=historical_fcf,
                        analyst_growth_estimate=growth / 100,
                        industry_growth=industry_growth,
                        beta=beta,
                        risk_free_rate=risk_free_rate,
                        debt_to_equity=debt_to_equity,
                        cost_of_debt=cost_of_debt
                    ))
                    
                    fcf_yield_sensitivity[str(yield_val)][str(growth)] = dcf_result['per_share_value']
            
            # Terminal P/E sensitivity
            terminal_pe_sensitivity = {}
            for pe in range(int(eps_multiple) - 5, int(eps_multiple) + 6, 2):
                if pe <= 0:
                    continue
                    
                terminal_pe_sensitivity[str(pe)] = {}
                for growth in range(int(eps_growth * 100) - 10, int(eps_growth * 100) + 15, 5):
                    if growth < 0:
                        continue
                        
                    # Use the backend PE model
                    pe_result = run_async(valuation_service.pe_model.calculate(
                        eps=eps,
                        growth_rate=growth / 100,
                        years=years,
                        industry_pe=pe
                    ))
                    
                    terminal_pe_sensitivity[str(pe)][str(growth)] = pe_result['fair_value']
            
            # Discount Rate sensitivity (for EV/EBITDA)
            discount_rate_sensitivity = {}
            if use_ev_ebitda:
                # Use fixed discount rates for sensitivity
                for rate in range(8, 16, 1):  # 8% to 15%
                    discount_rate_value = rate / 100
                        
                    discount_rate_sensitivity[str(rate)] = {}
                    for growth in range(int(ebitda_growth * 100) - 10, int(ebitda_growth * 100) + 15, 5):
                        if growth < 0:
                            continue
                            
                        # Use the EV/EBITDA model
                        ev_ebitda_result = run_async(valuation_service.ev_ebitda_model.calculate(
                            ebitda=ebitda,
                            growth_rate=growth / 100,
                            net_debt=net_debt,
                            shares_outstanding=shares_outstanding
                        ))
                        
                        discount_rate_sensitivity[str(rate)][str(growth)] = ev_ebitda_result['per_share_value']
            
            # WACC sensitivity
            wacc_sensitivity = {}
            # Generate sensitivity across different beta values (risk levels)
            for beta_value in [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]:
                wacc_sensitivity[str(beta_value)] = {}
                
                for rfr in [0.03, 0.035, 0.04, 0.045, 0.05]:  # 3% to 5% risk-free rate
                    # Use enhanced DCF model with different beta and risk-free rate
                    dcf_result = run_async(valuation_service.dcf_model.calculate(
                        fcf=fcf,
                        growth_rate=fcf_growth,
                        discount_rate=discount_rate,
                        years=years,
                        terminal_growth=0.02,
                        net_debt=net_debt,
                        shares_outstanding=shares_outstanding,
                        historical_fcf=historical_fcf,
                        analyst_growth_estimate=fcf_growth,
                        industry_growth=industry_growth,
                        beta=beta_value,
                        risk_free_rate=rfr,
                        debt_to_equity=debt_to_equity,
                        cost_of_debt=cost_of_debt
                    ))
                    
                    calculated_wacc = dcf_result.get('wacc', discount_rate)
                    wacc_sensitivity[str(beta_value)][str(int(rfr * 100))] = calculated_wacc * 100  # Store as percentage
            
            
            sensitivity_analysis = {
                "fcf_growth": fcf_growth_sensitivity,
                "eps_growth": eps_growth_sensitivity,
                "fcf_yield": fcf_yield_sensitivity,
                "terminal_pe": terminal_pe_sensitivity,
                "wacc": wacc_sensitivity  # Add new WACC sensitivity
            }
            
            if use_ev_ebitda:
                sensitivity_analysis["discount_rate"] = discount_rate_sensitivity
        
        # Prepare scenario analysis (best, base, worst case)
        scenarios = {
            "base_case": weighted_value,
            "best_case": weighted_value * 1.3,  # 30% upside
            "worst_case": weighted_value * 0.7,  # 30% downside
            "confidence": "medium"  # Default confidence
        }
        
        # Prepare final response
        response = {
            "market_data": market_data_response,
            "valuation_results": valuation_results,
            "projections": projections_response,
            "scenarios": scenarios,  # Add scenario analysis
            "wacc_components": {  # Add WACC components
                "beta": beta,
                "risk_free_rate": risk_free_rate,
                "debt_to_equity": debt_to_equity,
                "cost_of_debt": cost_of_debt,
                "calculated_wacc": fcf_valuation.get("wacc", discount_rate)
            }
        }
        
        if include_sensitivity:
            response["sensitivity_analysis"] = sensitivity_analysis
        
        logger.info(f"Completed valuation for {symbol}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error performing valuation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/market_data/<symbol>', methods=['GET'])
def get_market_data(symbol):
    """Fetch market data for a specific stock symbol."""
    try:
        # Get the current price
        current_price = run_async(market_data_service.get_current_price(symbol))
        
        # Get financial data
        financial_data = run_async(market_data_service.get_financial_data(symbol))
        
        # Get historical data for valuation history
        historical_data = run_async(market_data_service.get_historical_data(symbol, period="5y"))
        historical_fcf = run_async(market_data_service.get_historical_fcf(symbol))
        historical_metrics = run_async(market_data_service.get_historical_metrics(symbol))
        
        # Calculate historical intrinsic values
        dates = []
        prices = []
        fcf_values = []
        pe_values = []
        ebitda_values = []
        intrinsic_values = []
        
        # Get shares outstanding and financial metrics
        shares_outstanding = financial_data.get('sharesOutstanding', 0)
        if shares_outstanding <= 0:
            market_cap = financial_data.get('marketCap', 0)
            shares_outstanding = market_cap / current_price if current_price > 0 else 0
        
        # Define conservative multiples
        FCF_MULTIPLE = 15
        PE_MULTIPLE = 15
        EBITDA_MULTIPLE = 10
        
        # Process historical data
        sorted_dates = sorted(historical_data.keys())
        for date in sorted_dates:
            price = historical_data[date]['close']
            
            # Add to price history
            dates.append(date)
            prices.append(price)
            
            # Get historical metrics for this date
            metrics = historical_metrics.get(date, {})
            historical_shares = metrics.get('sharesOutstanding', shares_outstanding)
            if historical_shares is None or historical_shares <= 0:
                historical_shares = shares_outstanding
            
            # Calculate FCF-based value
            fcf_value = None
            if historical_fcf and len(historical_fcf) > 0:
                # Find the closest FCF data point
                fcf_date = min(historical_fcf.keys(), key=lambda x: abs(datetime.strptime(x, '%Y-%m-%d') - datetime.strptime(date, '%Y-%m-%d')))
                fcf = historical_fcf[fcf_date]
                if fcf and fcf > 0 and historical_shares > 0:
                    fcf_per_share = fcf / historical_shares
                    fcf_value = fcf_per_share * FCF_MULTIPLE
            fcf_values.append(fcf_value)
            
            # Calculate P/E-based value
            pe_value = None
            net_income = metrics.get('netIncome')
            if net_income is not None and net_income > 0 and historical_shares > 0:
                eps = net_income / historical_shares
                if eps > 0:
                    pe_value = eps * PE_MULTIPLE
            pe_values.append(pe_value)
            
            # Calculate EBITDA-based value
            ebitda_value = None
            ebitda = metrics.get('ebitda')
            total_debt = metrics.get('totalDebt', 0)
            cash = metrics.get('cashAndEquivalents', 0)
            
            # Handle None values
            total_debt = 0 if total_debt is None else total_debt
            cash = 0 if cash is None else cash
            net_debt = total_debt - cash
            
            if ebitda is not None and ebitda > 0 and historical_shares > 0:
                enterprise_value = ebitda * EBITDA_MULTIPLE
                equity_value = enterprise_value - net_debt
                ebitda_value = equity_value / historical_shares if historical_shares > 0 else None
            ebitda_values.append(ebitda_value)
            
            # Calculate combined intrinsic value
            valid_values = []
            intrinsic_value = None  # Initialize with None
            
            # Add FCF value with 50% weight if available
            if fcf_value is not None and fcf_value > 0:
                valid_values.append(('fcf', fcf_value, 0.5))  # 50% weight
            
            # Calculate average of P/E and EBITDA for the other 50%
            pe_ebitda_values = []
            if pe_value is not None and pe_value > 0:
                pe_ebitda_values.append(pe_value)
            if ebitda_value is not None and ebitda_value > 0:
                pe_ebitda_values.append(ebitda_value)
            
            if pe_ebitda_values:
                avg_pe_ebitda = sum(pe_ebitda_values) / len(pe_ebitda_values)
                valid_values.append(('pe_ebitda', avg_pe_ebitda, 0.5))  # 50% weight
            
            if valid_values:
                # Calculate weighted average
                weighted_sum = sum(value * weight for _, value, weight in valid_values)
                total_weight = sum(weight for _, _, weight in valid_values)
                if total_weight > 0:
                    intrinsic_value = weighted_sum / total_weight
            
            # If no valid fundamental values or calculation failed, use moving average
            if intrinsic_value is None:
                # Fallback to moving average if no valid multiples
                window = min(30, len(prices))
                if window > 0:
                    intrinsic_value = sum(prices[-window:]) / window
                else:
                    intrinsic_value = price  # Final fallback to current price
            
            intrinsic_values.append(intrinsic_value)
        
        # Calculate average overvaluation
        if prices and intrinsic_values:
            # Calculate overvaluation percentages for historical average
            overvaluation_percentages = []
            for p, iv in zip(prices, intrinsic_values):
                if iv > 0:
                    # Calculate as (fair_value - price) / price * 100 to match chart display
                    overvaluation_percentages.append(((iv - p) / p) * 100)
            
            # Calculate historical average overvaluation
            average_overvaluation = sum(overvaluation_percentages) / len(overvaluation_percentages) if overvaluation_percentages else 0
            
            # Calculate current overvaluation using the most recent values
            current_price = prices[-1]
            current_iv = intrinsic_values[-1]
            # Use the same formula: (fair_value - price) / price * 100
            current_overvaluation = ((current_iv - current_price) / current_price) * 100 if current_price > 0 else 0
            
            # Add debug logging
            logger.info(f"Current price: {current_price}")
            logger.info(f"Current fair value: {current_iv}")
            logger.info(f"Calculated overvaluation: {current_overvaluation}%")
        else:
            average_overvaluation = 0
            current_overvaluation = 0
        
        # Calculate IV CAGR
        if len(intrinsic_values) > 1 and intrinsic_values[0] > 0 and intrinsic_values[-1] > 0:
            years = len(intrinsic_values) / 252  # Assuming daily data
            iv_cagr = (pow(intrinsic_values[-1] / intrinsic_values[0], 1/years) - 1) * 100
        else:
            iv_cagr = 0
        
        # Prepare response
        response = {
            "symbol": symbol.upper(),
            "price": current_price,
            "sharesOutstanding": shares_outstanding,
            "freeCashFlow": financial_data.get('freeCashFlow', 0),
            "netIncome": financial_data.get('netIncome', 0),
            "ebitda": financial_data.get('ebitda', 0),
            "totalDebt": financial_data.get('totalDebt', 0),
            "cashAndEquivalents": financial_data.get('cashAndEquivalents', 0),
            "beta": financial_data.get('beta', 1.0),
            "valuation_history": {
                "symbol": symbol.upper(),
                "dates": dates,
                "prices": prices,
                "intrinsic_values": intrinsic_values,
                "average_overvaluation": average_overvaluation,
                "current_overvaluation": current_overvaluation,
                "iv_cagr": iv_cagr,
                "current_price": prices[-1],
                "current_fair_value": intrinsic_values[-1]
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/historical_valuation', methods=['POST'])
def perform_historical_valuation():
    """Perform historical-based valuation analysis."""
    try:
        # Get request data
        data = request.json
        symbol = data.get('symbol', 'AAPL').upper()
        
        logger.info(f"Performing historical valuation for symbol: {symbol}")
        
        # Extract parameters with defaults
        years = int(data.get('years', 5))
        discount_rate = float(data.get('discount_rate', 10)) / 100  # Convert to decimal
        terminal_growth = float(data.get('terminal_growth', 2)) / 100  # Convert to decimal
        
        # Calculate historical valuation
        result = run_async(valuation_service.calculate_historical_valuation(
            symbol=symbol,
            years=years,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth
        ))
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error in historical valuation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 