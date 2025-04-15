import logging
import numpy as np
from typing import Dict, Any, List, Optional
from scipy import stats

logger = logging.getLogger(__name__)

class DiscountedCashFlowModel:
    """
    Advanced Discounted Cash Flow (DCF) valuation model.
    
    Calculates the intrinsic value of a company based on the present value
    of its projected future cash flows plus a terminal value. Uses regression
    analysis, industry benchmarks, and dynamic WACC calculation for more
    accurate projections.
    """
    
    async def calculate(
        self,
        fcf: float,
        growth_rate: float,
        discount_rate: float,
        years: int = 10,
        terminal_growth: float = 0.02,
        net_debt: float = 0,
        shares_outstanding: float = 1,
        historical_fcf: Optional[List[float]] = None,
        historical_revenue: Optional[List[float]] = None,
        analyst_growth_estimate: Optional[float] = None,
        industry_growth: Optional[float] = None,
        beta: Optional[float] = None,
        risk_free_rate: Optional[float] = None,
        market_risk_premium: Optional[float] = 0.05,
        debt_to_equity: Optional[float] = None,
        cost_of_debt: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate intrinsic value using an enhanced DCF model.
        
        Args:
            fcf: Current Free Cash Flow
            growth_rate: Expected annual growth rate (decimal)
            discount_rate: Required rate of return (decimal)
            years: Projection years (default 10)
            terminal_growth: Terminal growth rate (default 2%)
            net_debt: Total debt minus cash and cash equivalents
            shares_outstanding: Number of shares outstanding
            historical_fcf: List of historical FCF values (last 5-10 years)
            historical_revenue: List of historical revenue values
            analyst_growth_estimate: Growth rate estimated by analysts
            industry_growth: Average growth rate for the industry
            beta: Stock beta (volatility compared to market)
            risk_free_rate: Current risk-free interest rate
            market_risk_premium: Market risk premium (default 5%)
            debt_to_equity: Company's debt to equity ratio
            cost_of_debt: Company's cost of debt (interest rate)
            
        Returns:
            Dict: DCF calculation results
        """
        # Validate inputs and apply defaults
        logger.info(f"Starting DCF calculation with FCF: {fcf}, Growth: {growth_rate}, Discount: {discount_rate}")
        
        # Handle negative FCF - for companies with negative FCF, we need a different approach
        negative_fcf_adjustment = False
        if fcf <= 0:
            logger.warning(f"Negative FCF ({fcf}) encountered in DCF calculation")
            # Check historical FCF to see if it's a temporary issue
            if historical_fcf and any(x > 0 for x in historical_fcf):
                # Use the most recent positive FCF value
                positive_values = [x for x in historical_fcf if x > 0]
                if positive_values:
                    fcf = positive_values[-1]
                    logger.info(f"Using historical positive FCF: {fcf}")
                    negative_fcf_adjustment = True
            else:
                # Use a small positive value based on shares outstanding
                fcf = shares_outstanding * 0.1  # $0.10 per share as minimum FCF
                logger.info(f"Using minimum synthetic FCF: {fcf}")
                negative_fcf_adjustment = True
                # Reduce growth expectations for negative FCF companies
                growth_rate = min(growth_rate, 0.05)
        
        # Ensure shares outstanding is positive
        if shares_outstanding <= 0:
            logger.warning(f"Invalid shares outstanding ({shares_outstanding}), using default value")
            shares_outstanding = 1000000
        
        # Ensure discount rate is reasonable
        if discount_rate <= 0.01:
            logger.warning(f"Discount rate too low ({discount_rate}), using 10%")
            discount_rate = 0.1
        elif discount_rate >= 0.3:
            logger.warning(f"Discount rate too high ({discount_rate}), capping at 30%")
            discount_rate = 0.3
        
        # Validate historical FCF
        if historical_fcf is None or not isinstance(historical_fcf, list) or len(historical_fcf) < 2:
            logger.warning("Insufficient historical FCF data, using synthetic data")
            # Create synthetic historical data
            historical_fcf = [fcf * 0.9, fcf * 0.95, fcf]
        
        try:
            # STEP 1: Calculate optimized growth rates using available data
            
            # Start with the provided growth rate as baseline
            projected_growth_rates = [growth_rate] * years
            
            # 1.1: Use regression analysis if historical data is available
            if historical_fcf and len(historical_fcf) >= 3:
                try:
                    # Clean historical data (remove zeros and extreme values)
                    cleaned_historical = []
                    for i in range(len(historical_fcf)):
                        if historical_fcf[i] > 0:
                            # Include the value if it's positive and not extremely different from previous
                            if i == 0 or abs(historical_fcf[i] / historical_fcf[i-1] - 1) < 2.0:
                                cleaned_historical.append(historical_fcf[i])
                    
                    # Only use regression if we have enough clean data
                    if len(cleaned_historical) >= 3:
                        # Calculate historical growth rates
                        historical_growth = []
                        for i in range(1, len(cleaned_historical)):
                            historical_growth.append(cleaned_historical[i] / cleaned_historical[i-1] - 1)
                        
                        # Filter out extreme growth rates
                        filtered_growth = [g for g in historical_growth if abs(g) < 1.0]
                        
                        if len(filtered_growth) >= 2:
                            # Fit linear regression to historical growth rates
                            x = np.array(range(len(filtered_growth)))
                            y = np.array(filtered_growth)
                            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                            
                            # Only use regression if it has statistical significance
                            if p_value < 0.3 and r_value > 0.3:
                                # Project future growth rates with regression, but ensure they're reasonable
                                for i in range(years):
                                    reg_growth = intercept + slope * (len(filtered_growth) + i)
                                    # Cap growth rates to reasonable bounds
                                    reg_growth = max(min(reg_growth, 0.40), -0.10)  # Between -10% and 40%
                                    # Blend with provided growth rate (70% regression, 30% provided)
                                    projected_growth_rates[i] = reg_growth * 0.7 + growth_rate * 0.3
                                    
                                logger.info(f"Using regression growth projection: {projected_growth_rates[:3]}...")
                            else:
                                logger.info(f"Regression not significant (p={p_value:.3f}, r={r_value:.3f}), using provided growth")
                        else:
                            logger.info("Not enough valid historical growth rates for regression")
                    else:
                        logger.info("Not enough clean historical FCF data for regression")
                except Exception as e:
                    logger.warning(f"Error in regression analysis: {str(e)}. Using provided growth rate.")
            
            # 1.2: Incorporate analyst estimates if available
            if analyst_growth_estimate is not None:
                for i in range(years):
                    # Give more weight to analyst estimates in early years
                    analyst_weight = max(0, 0.6 - i * 0.1)  # 0.6 -> 0 over years
                    projected_growth_rates[i] = (projected_growth_rates[i] * (1 - analyst_weight) + 
                                               analyst_growth_estimate * analyst_weight)
                logger.info(f"Incorporated analyst growth estimate: {analyst_growth_estimate}")
            
            # 1.3: Factor in industry growth rates if available
            if industry_growth is not None and industry_growth > -100:  # Avoid extreme negative values
                for i in range(years):
                    # Industry becomes more important in later years (reversion to mean)
                    industry_weight = min(0.5, 0.1 + i * 0.05)  # 0.1 -> 0.5 over years
                    projected_growth_rates[i] = (projected_growth_rates[i] * (1 - industry_weight) + 
                                              industry_growth * industry_weight)
                logger.info(f"Incorporated industry growth rate: {industry_growth}")
            
            # If this is a company with negative FCF, be more conservative with growth
            if negative_fcf_adjustment:
                logger.info("Applying conservative growth adjustment for negative FCF")
                for i in range(years):
                    projected_growth_rates[i] = min(projected_growth_rates[i], 0.15)  # Cap at 15%
            
            # 1.4: Apply tapering to long-term growth (growth slows over time)
            for i in range(years):
                # Linear decline from initial growth to terminal growth
                taper_factor = i / (years - 1) if years > 1 else 1
                projected_growth_rates[i] = (projected_growth_rates[i] * (1 - taper_factor) + 
                                          terminal_growth * taper_factor)
            
            logger.info(f"Final projected growth rates: {projected_growth_rates[:3]}...")
            
            # STEP 2: Calculate optimal discount rate (WACC if data available)
            calculated_discount_rate = discount_rate  # Start with provided rate
            
            # 2.1: Calculate WACC if sufficient data is available
            wacc_calculated = False
            if (beta is not None and beta > 0 and risk_free_rate is not None and risk_free_rate > 0 and 
                debt_to_equity is not None and debt_to_equity >= 0 and cost_of_debt is not None and cost_of_debt > 0):
                try:
                    # Calculate cost of equity using CAPM
                    cost_of_equity = risk_free_rate + beta * market_risk_premium
                    
                    # Calculate WACC
                    equity_weight = 1 / (1 + debt_to_equity)
                    debt_weight = 1 - equity_weight
                    
                    # Apply tax shield to cost of debt (assume 25% corporate tax rate)
                    after_tax_cost_of_debt = cost_of_debt * 0.75
                    
                    # Calculate WACC
                    calculated_discount_rate = (cost_of_equity * equity_weight + 
                                              after_tax_cost_of_debt * debt_weight)
                    
                    # Ensure WACC is within reasonable bounds
                    if calculated_discount_rate < 0.05:
                        calculated_discount_rate = 0.05  # Minimum 5%
                    elif calculated_discount_rate > 0.20:
                        calculated_discount_rate = 0.20  # Maximum 20%
                    
                    wacc_calculated = True
                    logger.info(f"Calculated WACC: {calculated_discount_rate:.2%}")
                except Exception as e:
                    logger.warning(f"Error calculating WACC: {str(e)}. Using provided discount rate.")
            else:
                logger.info(f"Insufficient data for WACC calculation, using discount rate: {discount_rate:.2%}")
            
            # STEP 3: Calculate projected cash flows using dynamic growth rates
            base_fcf = fcf
            future_cash_flows = []
            
            for i in range(years):
                growth = projected_growth_rates[i]
                # For first projected year
                if i == 0:
                    projected_fcf = base_fcf * (1 + growth)
                else:
                    projected_fcf = future_cash_flows[i-1] * (1 + projected_growth_rates[i])
                
                future_cash_flows.append(projected_fcf)
                
                # Debug log for first few years
                if i < 3:
                    logger.info(f"Year {i+1} FCF: {projected_fcf:.2f} (growth: {growth:.2%})")
            
            # STEP 4: Discount projected cash flows
            discount_factors = [(1 + calculated_discount_rate) ** (i+1) for i in range(years)]
            discounted_fcf = [fcf / discount_factor for fcf, discount_factor in zip(future_cash_flows, discount_factors)]
            
            # STEP 5: Calculate terminal value
            # Use Gordon Growth Model with the terminal growth rate
            terminal_value = future_cash_flows[-1] * (1 + terminal_growth) / (calculated_discount_rate - terminal_growth)
            
            # Ensure terminal value multiplier is reasonable
            terminal_fcf_multiple = terminal_value / future_cash_flows[-1]
            if terminal_fcf_multiple > 30:
                logger.warning(f"Terminal FCF multiple too high: {terminal_fcf_multiple:.1f}x, capping at 30x")
                terminal_value = future_cash_flows[-1] * 30
            
            logger.info(f"Terminal value: {terminal_value:.2f} ({terminal_fcf_multiple:.1f}x FCF)")
            
            # Discount terminal value to present value
            terminal_value_discounted = terminal_value / discount_factors[-1]
            
            # STEP 6: Calculate enterprise value
            enterprise_value = sum(discounted_fcf) + terminal_value_discounted
            
            # STEP 7: Calculate equity value
            equity_value = enterprise_value - net_debt
            
            # STEP 8: Calculate per share value
            per_share_value = equity_value / shares_outstanding
            
            logger.info(f"DCF result: Enterprise value={enterprise_value:.2f}, Equity value={equity_value:.2f}, Per share={per_share_value:.2f}")
            
            # Return the results
            return {
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'per_share_value': per_share_value,
                'future_cash_flows': future_cash_flows,
                'discounted_cash_flows': discounted_fcf,
                'terminal_value': terminal_value,
                'terminal_value_discounted': terminal_value_discounted,
                'projected_growth_rates': projected_growth_rates,
                'wacc': calculated_discount_rate if wacc_calculated else None
            }
        except Exception as e:
            logger.error(f"Error in DCF calculation: {str(e)}")
            return {
                'enterprise_value': 0,
                'equity_value': 0,
                'per_share_value': 0,
                'error': str(e)
            } 