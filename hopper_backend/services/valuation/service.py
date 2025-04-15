import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from functools import lru_cache

# Import valuation models
from .models.dcf import DiscountedCashFlowModel
from .models.pe import PEBasedModel
from .models.ev_ebitda import EVEBITDAModel
from .models.historical_valuation import HistoricalValuationModel

logger = logging.getLogger(__name__)

class ValuationService:
    """
    Service for calculating stock valuations using multiple models.
    Combines different valuation methods with customizable weights.
    """
    
    def __init__(self, market_data_service, cache_service=None, config=None):
        """
        Initialize the valuation service.
        
        Args:
            market_data_service: Service for fetching market data
            cache_service: Optional cache service
            config: Optional configuration dictionary
        """
        self.market_data_service = market_data_service
        self.cache_service = cache_service
        self.config = config or {}
        
        # Initialize valuation models
        self.dcf_model = DiscountedCashFlowModel()
        self.pe_model = PEBasedModel()
        self.ev_ebitda_model = EVEBITDAModel()
        self.historical_model = HistoricalValuationModel()
        
        # Default weights for valuation methods
        self.weights = self.config.get("valuation_weights", {
            "dcf": 0.3,
            "pe": 0.2,
            "ev_ebitda": 0.2,
            "historical": 0.3
        })
    
    async def calculate_intrinsic_value(
        self, 
        symbol: str, 
        custom_dcf_growth: Optional[float] = None,
        custom_earnings_growth: Optional[float] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate the intrinsic value of a stock using multiple valuation methods.
        
        Args:
            symbol: Stock symbol
            custom_dcf_growth: Optional custom growth rate for DCF model
            custom_earnings_growth: Optional custom growth rate for earnings-based models
            custom_weights: Optional custom weights for valuation methods
            
        Returns:
            Dict: Valuation results with details
        """
        cache_key = (
            f"valuation:{symbol}:"
            f"{custom_dcf_growth or 'default'}:"
            f"{custom_earnings_growth or 'default'}:"
            f"{'-'.join([f'{k}-{v}' for k, v in (custom_weights or {}).items()])}"
        )
        
        if self.cache_service:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        try:
            # Get necessary financial data
            financial_data = await self.market_data_service.get_financial_data(symbol)
            fcf = financial_data.get('freeCashFlow')
            
            # If FCF is None, try to get it specifically
            if fcf is None:
                fcf = await self.market_data_service.get_free_cash_flow(symbol)
            
            # Calculate net debt
            net_debt = financial_data.get('totalDebt', 0) - financial_data.get('cashAndEquivalents', 0)
            
            # Get growth rates
            raw_earnings_growth = financial_data.get('earningsGrowth')
            
            # If growth rate is invalid, get analyst estimates
            if raw_earnings_growth is None or raw_earnings_growth < 0:
                raw_earnings_growth = await self.market_data_service.get_analyst_growth_estimates(symbol)
            
            # Use custom growth rates if provided
            earnings_growth = custom_earnings_growth if custom_earnings_growth is not None else max(min(raw_earnings_growth or 0.05, 0.30), 0.05)
            dcf_growth = custom_dcf_growth if custom_dcf_growth is not None else earnings_growth * 0.9
            
            # Get terminal growth rate from revenue growth, with reasonable limits
            revenue_growth = financial_data.get('revenueGrowth', 0.02)
            terminal_growth = max(min(revenue_growth if revenue_growth and revenue_growth > 0 else 0.02, 0.03), 0.01)
            
            # Get additional data for enhanced DCF model
            historical_fcf = await self.market_data_service.get_historical_fcf(symbol)
            risk_free_rate = await self.market_data_service.get_risk_free_rate()
            industry_growth = await self.market_data_service.get_industry_growth_rate(symbol)
            debt_to_equity = await self.market_data_service.get_debt_to_equity(symbol)
            cost_of_debt = await self.market_data_service.get_cost_of_debt(symbol)
            beta = financial_data.get('beta', 1.0)
            
            # Calculate DCF valuation with enhanced model
            dcf_result = await self.dcf_model.calculate(
                fcf=fcf,
                growth_rate=dcf_growth,
                discount_rate=0.10,  # Starting point, will be adjusted by model
                terminal_growth=terminal_growth,
                net_debt=net_debt,
                shares_outstanding=financial_data.get('sharesOutstanding', 1),
                # Additional parameters for enhanced model
                historical_fcf=historical_fcf,
                analyst_growth_estimate=earnings_growth,
                industry_growth=industry_growth,
                beta=beta,
                risk_free_rate=risk_free_rate,
                debt_to_equity=debt_to_equity,
                cost_of_debt=cost_of_debt
            )
            
            # Calculate P/E based valuation
            eps = financial_data.get('netIncome', 0) / financial_data.get('sharesOutstanding', 1) if financial_data.get('sharesOutstanding', 0) > 0 else 0
            pe_result = await self.pe_model.calculate(
                eps=eps,
                growth_rate=earnings_growth
            )
            
            # Calculate EV/EBITDA valuation
            ev_ebitda_result = await self.ev_ebitda_model.calculate(
                ebitda=financial_data.get('ebitda', 0),
                growth_rate=dcf_growth,
                net_debt=net_debt,
                shares_outstanding=financial_data.get('sharesOutstanding', 1)
            )
            
            # Use provided weights or defaults
            weights = custom_weights or self.weights
            
            # Combine methods with weights, only including valid results
            total_weight = 0
            weighted_value = 0
            
            if dcf_result['per_share_value'] > 0:
                weighted_value += dcf_result['per_share_value'] * weights['dcf']
                total_weight += weights['dcf']
                
            if pe_result['fair_value'] is not None and pe_result['fair_value'] > 0:
                weighted_value += pe_result['fair_value'] * weights['pe']
                total_weight += weights['pe']
                
            if ev_ebitda_result['per_share_value'] is not None and ev_ebitda_result['per_share_value'] > 0:
                weighted_value += ev_ebitda_result['per_share_value'] * weights['ev_ebitda']
                total_weight += weights['ev_ebitda']
            
            if total_weight > 0:
                weighted_value = weighted_value / total_weight
            else:
                weighted_value = 0
            
            # Construct the result
            result = {
                'symbol': symbol,
                'current_price': financial_data.get('price', 0),
                'weighted_value': weighted_value,
                'upside_potential': (weighted_value / financial_data.get('price', 1) - 1) * 100 if financial_data.get('price', 0) > 0 else 0,
                'dcf_value': dcf_result['per_share_value'],
                'pe_value': pe_result['fair_value'],
                'ev_ebitda_value': ev_ebitda_result['per_share_value'],
                'details': {
                    'dcf': {
                        'enterprise_value': dcf_result['enterprise_value'],
                        'equity_value': dcf_result['equity_value'],
                        'growth_rate': dcf_growth,
                        'terminal_growth': terminal_growth,
                        'discount_rate': dcf_result.get('wacc', 0.10),
                        'weight': weights['dcf'] if dcf_result['per_share_value'] > 0 else 0,
                        'projected_growth_rates': dcf_result.get('projected_growth_rates', []),
                        'historical_fcf': historical_fcf,
                        'industry_growth': industry_growth,
                        'beta': beta,
                        'risk_free_rate': risk_free_rate
                    },
                    'pe': {
                        'target_pe': pe_result['target_pe'],
                        'eps': eps,
                        'growth_rate': earnings_growth,
                        'weight': weights['pe'] if (pe_result['fair_value'] is not None and pe_result['fair_value'] > 0) else 0
                    },
                    'ev_ebitda': {
                        'multiple': ev_ebitda_result['ev_ebitda_multiple'],
                        'ebitda': financial_data.get('ebitda', 0),
                        'enterprise_value': ev_ebitda_result['enterprise_value'],
                        'equity_value': ev_ebitda_result['equity_value'],
                        'weight': weights['ev_ebitda'] if (ev_ebitda_result['per_share_value'] is not None and ev_ebitda_result['per_share_value'] > 0) else 0
                    },
                    'financial': {
                        'market_cap': financial_data.get('marketCap', 0),
                        'shares_outstanding': financial_data.get('sharesOutstanding', 0),
                        'net_debt': net_debt,
                        'fcf': fcf,
                        'ebitda': financial_data.get('ebitda', 0),
                        'net_income': financial_data.get('netIncome', 0),
                        'pe_ratio': financial_data.get('peRatio', None),
                        'debt_to_equity': debt_to_equity,
                        'cost_of_debt': cost_of_debt
                    }
                }
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.set(cache_key, result, expire=3600)  # 1 hour TTL
                
            return result
        except Exception as e:
            logger.error(f"Error calculating valuation for {symbol}: {str(e)}")
            raise ValueError(f"Error calculating valuation for {symbol}: {str(e)}")
    
    async def monte_carlo_valuation(
        self, 
        symbol: str, 
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """
        Perform Monte Carlo simulation for valuation.
        
        Args:
            symbol: Stock symbol
            iterations: Number of Monte Carlo iterations
            
        Returns:
            Dict: Monte Carlo simulation results with percentiles
        """
        cache_key = f"monte_carlo:{symbol}:{iterations}"
        
        if self.cache_service:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        try:
            # Get base financial data
            financial_data = await self.market_data_service.get_financial_data(symbol)
            fcf = financial_data.get('freeCashFlow')
            
            if fcf is None:
                fcf = await self.market_data_service.get_free_cash_flow(symbol)
                
            net_debt = financial_data.get('totalDebt', 0) - financial_data.get('cashAndEquivalents', 0)
            shares_outstanding = financial_data.get('sharesOutstanding', 1)
            
            # Run Monte Carlo simulation
            results = []
            
            for _ in range(iterations):
                # Randomize key parameters within reasonable ranges
                dcf_growth = np.random.uniform(0.05, 0.30)
                discount_rate = np.random.uniform(0.08, 0.15)
                terminal_growth = np.random.uniform(0.01, 0.03)
                
                # Run DCF with randomized parameters
                result = await self.dcf_model.calculate(
                    fcf=fcf,
                    growth_rate=dcf_growth,
                    discount_rate=discount_rate,
                    terminal_growth=terminal_growth,
                    net_debt=net_debt,
                    shares_outstanding=shares_outstanding
                )
                
                results.append(result['per_share_value'])
            
            # Convert to numpy array for calculations
            results_array = np.array(results)
            
            # Calculate statistics
            monte_carlo_result = {
                'symbol': symbol,
                'current_price': financial_data.get('price', 0),
                'mean_value': float(np.mean(results_array)),
                'median_value': float(np.median(results_array)),
                'std_dev': float(np.std(results_array)),
                'min_value': float(np.min(results_array)),
                'max_value': float(np.max(results_array)),
                'percentiles': {
                    '10': float(np.percentile(results_array, 10)),
                    '25': float(np.percentile(results_array, 25)),
                    '50': float(np.percentile(results_array, 50)),
                    '75': float(np.percentile(results_array, 75)),
                    '90': float(np.percentile(results_array, 90))
                },
                'upside_potential': {
                    'mean': (float(np.mean(results_array)) / financial_data.get('price', 1) - 1) * 100 if financial_data.get('price', 0) > 0 else 0,
                    'median': (float(np.median(results_array)) / financial_data.get('price', 1) - 1) * 100 if financial_data.get('price', 0) > 0 else 0
                }
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.set(cache_key, monte_carlo_result, expire=3600)  # 1 hour TTL
                
            return monte_carlo_result
        except Exception as e:
            logger.error(f"Error calculating Monte Carlo valuation for {symbol}: {str(e)}")
            raise ValueError(f"Error calculating Monte Carlo valuation for {symbol}: {str(e)}")
    
    async def sensitivity_analysis(
        self, 
        symbol: str,
        growth_rates: Optional[List[float]] = None,
        discount_rates: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on key valuation parameters.
        
        Args:
            symbol: Stock symbol
            growth_rates: List of growth rates to test
            discount_rates: List of discount rates to test
            
        Returns:
            Dict: Sensitivity analysis results
        """
        # Default values if not provided
        if growth_rates is None:
            growth_rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
        
        if discount_rates is None:
            discount_rates = [0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15]
        
        cache_key = f"sensitivity:{symbol}:{'-'.join([str(g) for g in growth_rates])}:{'-'.join([str(d) for d in discount_rates])}"
        
        if self.cache_service:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        try:
            # Get financial data
            financial_data = await self.market_data_service.get_financial_data(symbol)
            fcf = financial_data.get('freeCashFlow')
            
            if fcf is None:
                fcf = await self.market_data_service.get_free_cash_flow(symbol)
                
            net_debt = financial_data.get('totalDebt', 0) - financial_data.get('cashAndEquivalents', 0)
            shares_outstanding = financial_data.get('sharesOutstanding', 1)
            
            # Terminal growth (kept constant for simplicity)
            terminal_growth = 0.02
            
            # Create sensitivity matrix
            sensitivity_matrix = []
            
            for growth_rate in growth_rates:
                row = []
                
                for discount_rate in discount_rates:
                    # Calculate DCF with these parameters
                    result = await self.dcf_model.calculate(
                        fcf=fcf,
                        growth_rate=growth_rate,
                        discount_rate=discount_rate,
                        terminal_growth=terminal_growth,
                        net_debt=net_debt,
                        shares_outstanding=shares_outstanding
                    )
                    
                    row.append(result['per_share_value'])
                
                sensitivity_matrix.append(row)
            
            # Construct the result
            sensitivity_result = {
                'symbol': symbol,
                'current_price': financial_data.get('price', 0),
                'growth_rates': growth_rates,
                'discount_rates': discount_rates,
                'terminal_growth': terminal_growth,
                'sensitivity_matrix': sensitivity_matrix
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.set(cache_key, sensitivity_result, expire=3600)  # 1 hour TTL
                
            return sensitivity_result
        except Exception as e:
            logger.error(f"Error calculating sensitivity analysis for {symbol}: {str(e)}")
            raise ValueError(f"Error calculating sensitivity analysis for {symbol}: {str(e)}")

    async def calculate(self, fcf, growth_rate, discount_rate, years=10, terminal_growth=0.02, net_debt=0, shares_outstanding=1):
        # Add growth rate validation
        if growth_rate > 0.40:  # Cap at 40%
            logger.warning(f"Growth rate {growth_rate*100}% too high, capping at 40%")
            growth_rate = 0.40
        
        # Adjust terminal growth based on company size
        if fcf > 10_000_000_000:  # $10B FCF
            terminal_growth = min(terminal_growth, 0.02)  # Large companies grow slower
        
        # Adjust discount rate based on size and growth
        size_premium = 0.02 if fcf < 1_000_000_000 else 0
        growth_risk = 0.01 if growth_rate > 0.25 else 0
        adjusted_discount_rate = discount_rate + size_premium + growth_risk

    async def calculate(self, eps, growth_rate, industry_pe=None, peg_ratio=1.0):
        # Adjust PEG ratio based on growth rate
        if growth_rate > 0.25:
            peg_ratio = 0.8  # Higher growth needs more conservative PEG
        elif growth_rate < 0.10:
            peg_ratio = 1.2  # Lower growth can support higher PEG
        
        # Use industry PE more heavily
        if industry_pe:
            target_pe = (target_pe * 0.5) + (industry_pe * 0.5)  # Equal weight 

    async def calculate(self, ebitda, growth_rate, net_debt, shares_outstanding):
        # Use different multiple based on growth and stability
        base_multiple = 8.0  # Starting point
        growth_premium = min(growth_rate * 10, 4.0)  # Growth premium
        size_discount = 0 if ebitda > 1_000_000_000 else -1.0  # Size discount
        
        target_multiple = base_multiple + growth_premium + size_discount 

    async def calculate_scenarios(self, base_value):
        return {
            'best_case': base_value * 1.3,  # 30% upside
            'base_case': base_value,
            'worst_case': base_value * 0.7,  # 30% downside
            'confidence': 'medium'  # Based on volatility and growth
        }

    async def calculate_historical_valuation(
        self,
        symbol: str,
        years: int = 5,
        discount_rate: float = 0.1,
        terminal_growth: float = 0.02
    ) -> Dict[str, Any]:
        """
        Calculate intrinsic value using historical data.
        
        Args:
            symbol: Stock symbol
            years: Number of years for historical analysis
            discount_rate: Discount rate for DCF
            terminal_growth: Terminal growth rate
            
        Returns:
            Dict containing valuation results
        """
        try:
            return await self.historical_model.calculate(
                symbol,
                self.market_data_service,
                years,
                discount_rate,
                terminal_growth
            )
        except Exception as e:
            logger.error(f"Error in historical valuation for {symbol}: {str(e)}")
            raise 