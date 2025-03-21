import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DiscountedCashFlowModel:
    """
    Discounted Cash Flow (DCF) valuation model.
    
    Calculates the intrinsic value of a company based on the present value
    of its projected future cash flows plus a terminal value.
    """
    
    async def calculate(
        self,
        fcf: float,
        growth_rate: float,
        discount_rate: float,
        years: int = 10,
        terminal_growth: float = 0.02,
        net_debt: float = 0,
        shares_outstanding: float = 1
    ) -> Dict[str, Any]:
        """
        Calculate intrinsic value using the DCF model.
        
        Args:
            fcf: Current Free Cash Flow
            growth_rate: Expected annual growth rate (decimal)
            discount_rate: Required rate of return (decimal)
            years: Projection years (default 10)
            terminal_growth: Terminal growth rate (default 2%)
            net_debt: Total debt minus cash and cash equivalents
            shares_outstanding: Number of shares outstanding
            
        Returns:
            Dict: DCF calculation results
        """
        # Validate inputs
        if fcf <= 0 or shares_outstanding <= 0:
            logger.warning("Invalid FCF or shares outstanding for DCF calculation")
            return {
                'enterprise_value': 0,
                'equity_value': 0,
                'per_share_value': 0
            }
        
        try:
            # Calculate future cash flows
            future_cash_flows = [fcf * (1 + growth_rate) ** year for year in range(1, years + 1)]
            
            # Discount future cash flows to present value
            discounted_fcf = [fcf / ((1 + discount_rate) ** year) for year, fcf in enumerate(future_cash_flows, 1)]
            
            # Calculate terminal value
            terminal_value = (future_cash_flows[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            
            # Discount terminal value to present value
            terminal_value_discounted = terminal_value / ((1 + discount_rate) ** years)
            
            # Calculate enterprise value
            enterprise_value = sum(discounted_fcf) + terminal_value_discounted
            
            # Calculate equity value
            equity_value = enterprise_value - net_debt
            
            # Calculate per share value
            per_share_value = equity_value / shares_outstanding
            
            # Return the results
            return {
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'per_share_value': per_share_value,
                'future_cash_flows': future_cash_flows,
                'discounted_cash_flows': discounted_fcf,
                'terminal_value': terminal_value,
                'terminal_value_discounted': terminal_value_discounted
            }
        except Exception as e:
            logger.error(f"Error in DCF calculation: {str(e)}")
            return {
                'enterprise_value': 0,
                'equity_value': 0,
                'per_share_value': 0,
                'error': str(e)
            } 