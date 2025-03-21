import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EVEBITDAModel:
    """
    Enterprise Value to EBITDA (EV/EBITDA) valuation model.
    
    Calculates the intrinsic value of a company based on its EBITDA
    and an appropriate EV/EBITDA multiple derived from growth expectations.
    """
    
    async def calculate(
        self,
        ebitda: float,
        growth_rate: float,
        industry_multiple: Optional[float] = None,
        net_debt: float = 0,
        shares_outstanding: float = 1
    ) -> Dict[str, Any]:
        """
        Calculate intrinsic value using the EV/EBITDA model.
        
        Args:
            ebitda: Earnings Before Interest, Taxes, Depreciation, and Amortization
            growth_rate: Expected annual growth rate (decimal)
            industry_multiple: Optional industry average EV/EBITDA multiple
            net_debt: Total debt minus cash and cash equivalents
            shares_outstanding: Number of shares outstanding
            
        Returns:
            Dict: EV/EBITDA calculation results
        """
        # Validate inputs
        if ebitda <= 0 or shares_outstanding <= 0:
            logger.warning("Invalid EBITDA or shares outstanding for EV/EBITDA calculation")
            return {
                'ev_ebitda_multiple': None,
                'enterprise_value': 0,
                'equity_value': 0,
                'per_share_value': 0,
                'error': "Invalid inputs"
            }
        
        try:
            # Calculate target EV/EBITDA multiple based on growth rate
            # Higher growth rates justify higher multiples
            base_multiple = 6.0  # Base multiple for zero growth
            growth_factor = 10.0  # Multiple increase per 10% growth
            
            growth_percent = growth_rate * 100  # Convert to percentage
            target_multiple = base_multiple + (growth_percent / 10.0) * growth_factor
            
            # Apply reasonable bounds to the multiple
            target_multiple = max(min(target_multiple, 25), 4)  # Cap between 4 and 25
            
            # If industry multiple is provided, use a weighted average
            if industry_multiple is not None and industry_multiple > 0:
                target_multiple = (target_multiple * 0.7) + (industry_multiple * 0.3)
            
            # Calculate enterprise value
            enterprise_value = ebitda * target_multiple
            
            # Calculate equity value
            equity_value = enterprise_value - net_debt
            
            # Calculate per share value
            per_share_value = equity_value / shares_outstanding
            
            # Return the results
            return {
                'ev_ebitda_multiple': target_multiple,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'per_share_value': per_share_value,
                'growth_rate': growth_rate,
                'industry_multiple': industry_multiple
            }
        except Exception as e:
            logger.error(f"Error in EV/EBITDA calculation: {str(e)}")
            return {
                'ev_ebitda_multiple': None,
                'enterprise_value': 0,
                'equity_value': 0,
                'per_share_value': 0,
                'error': str(e)
            } 