import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class HistoricalValuationModel:
    """
    Valuation model that uses historical data to calculate intrinsic value.
    Uses a weighted approach between DCF and average of P/E + EV/EBITDA.
    """
    
    def __init__(self):
        self.dcf_weight = 0.5
        self.pe_ev_ebitda_weight = 0.5
        
        # Default values for missing data
        self.default_growth_rate = 0.05  # 5% default growth
        self.default_pe_ratio = 15  # Conservative P/E ratio
        self.default_ev_ebitda_ratio = 10  # Conservative EV/EBITDA ratio
    
    async def calculate(
        self,
        symbol: str,
        market_data_service,
        years: int = 5,
        discount_rate: float = 0.1,
        terminal_growth: float = 0.02
    ) -> Dict[str, Any]:
        """
        Calculate intrinsic value using historical data.
        
        Args:
            symbol: Stock symbol
            market_data_service: Market data service instance
            years: Number of years for historical analysis
            discount_rate: Discount rate for DCF
            terminal_growth: Terminal growth rate
            
        Returns:
            Dict containing valuation results
        """
        try:
            # Get historical financial data
            historical_fcf = await market_data_service.get_historical_fcf(symbol, years)
            financial_data = await market_data_service.get_financial_data(symbol)
            
            # Get current price and shares outstanding
            current_price = await market_data_service.get_current_price(symbol)
            shares_outstanding = financial_data.get('sharesOutstanding')
            
            if not shares_outstanding or shares_outstanding <= 0:
                logger.warning(f"Invalid shares outstanding for {symbol}, using market cap / price")
                market_cap = financial_data.get('marketCap')
                if market_cap and current_price:
                    shares_outstanding = market_cap / current_price
                else:
                    raise ValueError(f"Cannot determine shares outstanding for {symbol}")
            
            # Calculate values with fallbacks
            dcf_value = None
            pe_ev_ebitda_value = None
            
            try:
                dcf_value = await self._calculate_dcf(
                    historical_fcf,
                    discount_rate,
                    terminal_growth,
                    shares_outstanding
                )
            except Exception as e:
                logger.warning(f"DCF calculation failed for {symbol}: {str(e)}")
                dcf_value = None
            
            try:
                pe_ev_ebitda_value = await self._calculate_pe_ev_ebitda(
                    financial_data,
                    current_price,
                    shares_outstanding
                )
            except Exception as e:
                logger.warning(f"P/E & EV/EBITDA calculation failed for {symbol}: {str(e)}")
                pe_ev_ebitda_value = None
            
            # If both calculations failed, raise error
            if dcf_value is None and pe_ev_ebitda_value is None:
                raise ValueError(f"Both valuation methods failed for {symbol}")
            
            # Calculate weighted average using available values
            if dcf_value is not None and pe_ev_ebitda_value is not None:
                weighted_value = (
                    dcf_value * self.dcf_weight +
                    pe_ev_ebitda_value * self.pe_ev_ebitda_weight
                )
            elif dcf_value is not None:
                weighted_value = dcf_value
                logger.info(f"Using only DCF value for {symbol}")
            else:
                weighted_value = pe_ev_ebitda_value
                logger.info(f"Using only P/E & EV/EBITDA value for {symbol}")
            
            return {
                'intrinsic_value': weighted_value,
                'dcf_value': dcf_value,
                'pe_ev_ebitda_value': pe_ev_ebitda_value,
                'current_price': current_price,
                'margin_of_safety': (weighted_value - current_price) / current_price * 100 if current_price else None,
                'calculation_notes': self._get_calculation_notes(dcf_value, pe_ev_ebitda_value)
            }
            
        except Exception as e:
            logger.error(f"Error in historical valuation for {symbol}: {str(e)}")
            raise
    
    def _get_calculation_notes(self, dcf_value: Optional[float], pe_ev_ebitda_value: Optional[float]) -> List[str]:
        """Generate notes about which calculations were used."""
        notes = []
        if dcf_value is None:
            notes.append("DCF calculation failed - insufficient historical data")
        if pe_ev_ebitda_value is None:
            notes.append("P/E & EV/EBITDA calculation failed - insufficient market data")
        return notes
    
    async def _calculate_dcf(
        self,
        historical_fcf: List[float],
        discount_rate: float,
        terminal_growth: float,
        shares_outstanding: int
    ) -> float:
        """
        Calculate DCF value using historical FCF data.
        """
        if not historical_fcf:
            raise ValueError("No historical FCF data available")
        
        if len(historical_fcf) < 2:
            # If only one year of data, use default growth
            logger.warning("Insufficient historical FCF data, using default growth rate")
            growth_rates = [self.default_growth_rate]
        else:
            # Calculate historical growth rates
            growth_rates = []
            for i in range(1, len(historical_fcf)):
                if historical_fcf[i-1] != 0:
                    growth_rate = (historical_fcf[i] - historical_fcf[i-1]) / abs(historical_fcf[i-1])
                    # Filter out extreme growth rates
                    if -1 < growth_rate < 2:  # Allow between -100% and +200%
                        growth_rates.append(growth_rate)
        
        # Use average growth rate with fallback
        if growth_rates:
            avg_growth = np.mean(growth_rates)
            # Limit growth rate to reasonable range
            avg_growth = max(min(avg_growth, 0.25), -0.1)  # Between -10% and +25%
        else:
            logger.warning("No valid growth rates found, using default")
            avg_growth = self.default_growth_rate
        
        # Project future FCF
        last_fcf = historical_fcf[-1]
        if last_fcf <= 0:
            # If last FCF is negative, use average of positive FCFs
            positive_fcfs = [fcf for fcf in historical_fcf if fcf > 0]
            if not positive_fcfs:
                raise ValueError("No positive FCF values in historical data")
            last_fcf = np.mean(positive_fcfs)
        
        projected_fcf = []
        for year in range(1, 6):  # 5-year projection
            projected_fcf.append(last_fcf * (1 + avg_growth) ** year)
        
        # Calculate terminal value
        terminal_value = projected_fcf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
        
        # Calculate present value of projected FCF
        pv_fcf = sum(
            fcf / (1 + discount_rate) ** year
            for year, fcf in enumerate(projected_fcf, 1)
        )
        
        # Calculate present value of terminal value
        pv_terminal = terminal_value / (1 + discount_rate) ** 5
        
        # Calculate total value
        total_value = pv_fcf + pv_terminal
        
        # Calculate per-share value
        per_share_value = total_value / shares_outstanding
        
        return per_share_value
    
    async def _calculate_pe_ev_ebitda(
        self,
        financial_data: Dict[str, Any],
        current_price: float,
        shares_outstanding: int
    ) -> float:
        """
        Calculate value using average of P/E and EV/EBITDA multiples.
        """
        # Get required financial data with fallbacks
        eps = financial_data.get('eps')
        ebitda = financial_data.get('ebitda')
        total_debt = financial_data.get('totalDebt', 0)
        cash = financial_data.get('cashAndEquivalents', 0)
        net_debt = total_debt - cash
        
        if not eps or not ebitda:
            raise ValueError("Missing required financial data (EPS or EBITDA)")
        
        if eps <= 0 or ebitda <= 0:
            raise ValueError("Negative or zero EPS or EBITDA")
        
        # Calculate current multiples with sanity checks
        pe_value = None
        ev_ebitda_value = None
        
        try:
            current_pe = current_price / eps
            if 0 < current_pe < 100:  # Reasonable P/E range
                pe_value = self.default_pe_ratio * eps
        except Exception:
            logger.warning("Could not calculate P/E value")
        
        try:
            current_ev = current_price * shares_outstanding + net_debt
            current_ev_ebitda = current_ev / ebitda
            if 0 < current_ev_ebitda < 50:  # Reasonable EV/EBITDA range
                ev_ebitda_value = (self.default_ev_ebitda_ratio * ebitda - net_debt) / shares_outstanding
        except Exception:
            logger.warning("Could not calculate EV/EBITDA value")
        
        # Return average of available values
        if pe_value is not None and ev_ebitda_value is not None:
            return (pe_value + ev_ebitda_value) / 2
        elif pe_value is not None:
            return pe_value
        elif ev_ebitda_value is not None:
            return ev_ebitda_value
        else:
            raise ValueError("Could not calculate either P/E or EV/EBITDA value") 