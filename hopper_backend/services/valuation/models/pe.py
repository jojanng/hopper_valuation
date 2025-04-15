import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PEBasedModel:
    """
    Price-to-Earnings (P/E) based valuation model using DCF-style approach.
    
    Calculates the intrinsic value of a company based on discounting projected future earnings
    with a terminal P/E multiple. Combines traditional P/E multiples with a DCF approach.
    """
    
    async def calculate(
        self,
        eps: float,
        growth_rate: float,
        industry_pe: Optional[float] = None,
        peg_ratio: float = 1.0,
        years: int = 5,
        discount_rate: float = 0.10
    ) -> Dict[str, Any]:
        """
        Calculate intrinsic value using EPS projection and DCF approach.
        
        Args:
            eps: Earnings Per Share (current)
            growth_rate: Expected annual growth rate (decimal)
            industry_pe: Optional industry average P/E ratio (for terminal value)
            peg_ratio: Price/Earnings to Growth ratio (default 1.0)
            years: Number of years to project earnings (default 5)
            discount_rate: Required rate of return (default 10%)
            
        Returns:
            Dict: P/E calculation results
        """
        # Validate inputs
        if eps <= 0 or years <= 0 or discount_rate <= 0:
            logger.warning("Invalid inputs for P/E calculation")
            return {
                'target_pe': None,
                'fair_value': None,
                'error': "Invalid inputs"
            }
        
        try:
            # Determine terminal P/E multiple
            # Option 1: Use provided industry P/E
            # Option 2: Calculate based on PEG ratio and growth rate
            growth_percent = growth_rate * 100  # Convert to percentage
            calculated_pe = growth_percent * peg_ratio
            
            # Apply reasonable bounds to the P/E ratio
            calculated_pe = max(min(calculated_pe, 50), 5)  # Cap between 5 and 50
            
            # Use industry_pe if provided, otherwise use calculated PE
            terminal_pe = industry_pe if industry_pe is not None and industry_pe > 0 else calculated_pe
            
            # Calculate future EPS
            future_eps = eps * (1 + growth_rate) ** years
            
            # Calculate future value (target price)
            future_value = future_eps * terminal_pe
            
            # Calculate intrinsic value (present value of future value)
            fair_value = future_value / (1 + discount_rate) ** years
            
            # Calculate implied return based on current price (if provided)
            implied_return = None
            
            # Generate projected EPS values
            projected_eps = []
            for year in range(years + 1):
                year_eps = eps * (1 + growth_rate) ** year
                projected_eps.append(year_eps)
            
            # Return the results
            return {
                'target_pe': terminal_pe,
                'fair_value': fair_value,
                'future_eps': future_eps,
                'future_value': future_value,
                'growth_rate': growth_rate,
                'years': years,
                'discount_rate': discount_rate,
                'projected_eps': projected_eps
            }
        except Exception as e:
            logger.error(f"Error in P/E calculation: {str(e)}")
            return {
                'target_pe': None,
                'fair_value': None,
                'error': str(e)
            } 