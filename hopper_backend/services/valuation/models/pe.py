import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PEBasedModel:
    """
    Price-to-Earnings (P/E) based valuation model.
    
    Calculates the intrinsic value of a company based on its earnings
    and an appropriate P/E multiple derived from growth expectations.
    """
    
    async def calculate(
        self,
        eps: float,
        growth_rate: float,
        industry_pe: Optional[float] = None,
        peg_ratio: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate intrinsic value using the P/E model.
        
        Args:
            eps: Earnings Per Share (current or forward)
            growth_rate: Expected annual growth rate (decimal)
            industry_pe: Optional industry average P/E ratio
            peg_ratio: Price/Earnings to Growth ratio (default 1.0)
            
        Returns:
            Dict: P/E calculation results
        """
        # Validate inputs
        if eps <= 0:
            logger.warning("Invalid EPS for P/E calculation")
            return {
                'target_pe': None,
                'fair_value': None,
                'error': "Invalid EPS"
            }
        
        try:
            # Calculate target P/E ratio based on growth rate
            # Using the PEG ratio method: P/E = Growth Rate * PEG
            growth_percent = growth_rate * 100  # Convert to percentage
            target_pe = growth_percent * peg_ratio
            
            # Apply reasonable bounds to the P/E ratio
            target_pe = max(min(target_pe, 50), 5)  # Cap between 5 and 50
            
            # If industry P/E is provided, use a weighted average
            if industry_pe is not None and industry_pe > 0:
                target_pe = (target_pe * 0.7) + (industry_pe * 0.3)
            
            # Calculate fair value
            fair_value = eps * target_pe
            
            # Return the results
            return {
                'target_pe': target_pe,
                'fair_value': fair_value,
                'growth_rate': growth_rate,
                'peg_ratio': peg_ratio,
                'industry_pe': industry_pe
            }
        except Exception as e:
            logger.error(f"Error in P/E calculation: {str(e)}")
            return {
                'target_pe': None,
                'fair_value': None,
                'error': str(e)
            } 