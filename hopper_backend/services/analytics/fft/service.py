import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from scipy.fft import fft, ifft
from scipy.stats import norm

logger = logging.getLogger(__name__)

class FFTAnalysisService:
    """
    Service for performing FFT-based financial analysis.
    
    Includes advanced option pricing, market cycle detection,
    volatility term structure analysis, and noise filtering.
    """
    
    def __init__(self, market_data_service, cache_service=None, config=None):
        """
        Initialize the FFT Analysis service.
        
        Args:
            market_data_service: Service for fetching market data
            cache_service: Optional cache service
            config: Optional configuration dictionary
        """
        self.market_data_service = market_data_service
        self.cache_service = cache_service
        self.config = config or {}
    
    async def option_pricing(
        self,
        symbol: str,
        strike_price: float,
        time_to_maturity: float,
        use_real_world: bool = False,
        real_world_return: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate option prices using FFT method with characteristic function.
        
        Args:
            symbol: Stock symbol
            strike_price: Option strike price
            time_to_maturity: Time to maturity in years
            use_real_world: Whether to use real-world drift instead of risk-free rate
            real_world_return: Optional real-world expected return (if use_real_world=True)
            
        Returns:
            Dict: Option pricing results
        """
        cache_key = f"option_price:{symbol}:{strike_price}:{time_to_maturity}:{use_real_world}:{real_world_return or 'default'}"
        
        if self.cache_service:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        try:
            # Get market parameters
            current_price = await self.market_data_service.get_current_price(symbol)
            volatility = await self.market_data_service.get_historical_volatility(symbol)
            
            # Fixed parameters (could also fetch these)
            risk_free_rate = 0.0425  # Risk-free rate
            
            # Get dividend yield
            financial_data = await self.market_data_service.get_financial_data(symbol)
            dividend_yield = financial_data.get('dividendYield', 0.0) / 100.0 if financial_data.get('dividendYield') else 0.0
            
            # Set mu (expected return) based on mode
            mu = real_world_return if use_real_world and real_world_return is not None else risk_free_rate
            
            # Perform FFT-based option pricing
            call_price, put_price, prob_above_strike = self._char_function_fft(
                S0=current_price,
                K=strike_price,
                T=time_to_maturity,
                r=risk_free_rate,
                mu=mu,
                q=dividend_yield,
                sigma=volatility,
                use_real_world=use_real_world
            )
            
            # Calculate expected stock price
            expected_price = current_price * np.exp((mu - dividend_yield) * time_to_maturity)
            
            result = {
                'symbol': symbol,
                'current_price': current_price,
                'strike_price': strike_price,
                'time_to_maturity': time_to_maturity,
                'volatility': volatility,
                'risk_free_rate': risk_free_rate,
                'dividend_yield': dividend_yield,
                'expected_return': mu if use_real_world else risk_free_rate,
                'call_price': call_price,
                'put_price': put_price,
                'probability_above_strike': prob_above_strike,
                'expected_price': expected_price,
                'pricing_model': "Real-World Expected Return" if use_real_world else "Risk-Neutral (Risk-Free Rate)"
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.set(cache_key, result, expire=1800)  # 30 minute TTL
                
            return result
        except Exception as e:
            logger.error(f"Error calculating option prices for {symbol}: {str(e)}")
            raise ValueError(f"Error calculating option prices for {symbol}: {str(e)}")
    
    def _char_function_fft(
        self,
        S0: float,
        K: float,
        T: float,
        r: float,
        mu: float,
        q: float,
        sigma: float,
        use_real_world: bool = False
    ) -> Tuple[float, float, float]:
        """
        Calculate option prices using FFT method with characteristic function.
        
        Args:
            S0: Current stock price
            K: Strike price
            T: Time to maturity
            r: Risk-free rate
            mu: Real-world expected return
            q: Dividend yield
            sigma: Volatility
            use_real_world: Whether to use real-world drift
            
        Returns:
            Tuple[float, float, float]: Call price, put price, probability above strike
        """
        # Set drift based on pricing model
        drift = mu if use_real_world else r
        
        # FFT parameters
        N = 2**12  # Number of points
        alpha = 1.5  # Damping factor
        eta = 0.25  # Grid spacing
        lambda_ = 2 * np.pi / (N * eta)  # Grid spacing in log strike
        
        # Grid points
        k = np.arange(-N/2, N/2) * lambda_
        v = np.arange(-N/2, N/2) * eta
        
        # Characteristic function
        def char_func(v):
            return np.exp(1j * v * (np.log(S0) + (drift - q - 0.5 * sigma**2) * T) - 
                         0.5 * sigma**2 * T * v**2)
        
        # Calculate characteristic function values
        char_values = char_func(v)
        
        # Apply damping factor
        damped_char = np.exp(-alpha * k) * np.real(fft(char_values * np.exp(-1j * v * np.log(K))))
        
        # Normalize and extract option prices
        call_price = damped_char[N//2] / np.pi
        put_price = call_price - S0 * np.exp(-q * T) + K * np.exp(-r * T)
        
        # Calculate probability of stock price being above strike
        d1 = (np.log(S0/K) + (drift - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        prob_ST_above_K = 1 - norm.cdf(-d1)
        
        return call_price, put_price, prob_ST_above_K
    
    async def option_pricing_surface(
        self,
        symbol: str,
        strike_range: List[float],
        maturity_range: List[float],
        use_real_world: bool = False,
        real_world_return: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate option prices for multiple strikes and maturities.
        
        Args:
            symbol: Stock symbol
            strike_range: List of strike prices
            maturity_range: List of maturities in years
            use_real_world: Whether to use real-world drift
            real_world_return: Optional real-world expected return
            
        Returns:
            Dict: Option price surface results
        """
        cache_key = (
            f"option_surface:{symbol}:"
            f"{'-'.join([str(s) for s in strike_range])}:"
            f"{'-'.join([str(m) for m in maturity_range])}:"
            f"{use_real_world}:{real_world_return or 'default'}"
        )
        
        if self.cache_service:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        try:
            # Get market parameters
            current_price = await self.market_data_service.get_current_price(symbol)
            volatility = await self.market_data_service.get_historical_volatility(symbol)
            
            # Fixed parameters
            risk_free_rate = 0.0425  # Risk-free rate
            
            # Get dividend yield
            financial_data = await self.market_data_service.get_financial_data(symbol)
            dividend_yield = financial_data.get('dividendYield', 0.0) / 100.0 if financial_data.get('dividendYield') else 0.0
            
            # Set mu (expected return) based on mode
            mu = real_world_return if use_real_world and real_world_return is not None else risk_free_rate
            
            # Create matrices for call and put prices
            call_matrix = []
            put_matrix = []
            prob_matrix = []
            
            for maturity in maturity_range:
                call_row = []
                put_row = []
                prob_row = []
                
                for strike in strike_range:
                    call_price, put_price, prob = self._char_function_fft(
                        S0=current_price,
                        K=strike,
                        T=maturity,
                        r=risk_free_rate,
                        mu=mu,
                        q=dividend_yield,
                        sigma=volatility,
                        use_real_world=use_real_world
                    )
                    
                    call_row.append(call_price)
                    put_row.append(put_price)
                    prob_row.append(prob)
                
                call_matrix.append(call_row)
                put_matrix.append(put_row)
                prob_matrix.append(prob_row)
            
            result = {
                'symbol': symbol,
                'current_price': current_price,
                'strike_range': strike_range,
                'maturity_range': maturity_range,
                'volatility': volatility,
                'risk_free_rate': risk_free_rate,
                'dividend_yield': dividend_yield,
                'expected_return': mu if use_real_world else risk_free_rate,
                'call_price_matrix': call_matrix,
                'put_price_matrix': put_matrix,
                'probability_matrix': prob_matrix,
                'pricing_model': "Real-World Expected Return" if use_real_world else "Risk-Neutral (Risk-Free Rate)"
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.set(cache_key, result, expire=1800)  # 30 minute TTL
                
            return result
        except Exception as e:
            logger.error(f"Error calculating option price surface for {symbol}: {str(e)}")
            raise ValueError(f"Error calculating option price surface for {symbol}: {str(e)}")
    
    async def detect_market_cycles(
        self,
        symbol: str,
        period: str = "5y",
        max_cycle_years: float = 5.0
    ) -> Dict[str, Any]:
        """
        Detect market cycles using FFT.
        
        Args:
            symbol: Stock symbol
            period: Historical data period (e.g., 1y, 2y, 5y)
            max_cycle_years: Maximum cycle period to consider in years
            
        Returns:
            Dict: Market cycle analysis results
        """
        cache_key = f"market_cycles:{symbol}:{period}:{max_cycle_years}"
        
        if self.cache_service:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        try:
            # Get historical price data
            historical_data = await self.market_data_service.get_historical_data(symbol, period=period)
            
            # Extract closing prices
            dates = [entry['date'] for entry in historical_data]
            prices = np.array([entry['close'] for entry in historical_data])
            
            # Calculate returns
            returns = np.diff(np.log(prices))
            
            # Perform FFT on returns
            fft_values = fft(returns)
            
            # Get power spectrum (absolute values squared)
            power = np.abs(fft_values) ** 2
            
            # Calculate frequencies (in cycles per day)
            n = len(returns)
            sampling_rate = 252  # Trading days per year
            freqs = np.fft.fftfreq(n, 1/sampling_rate)
            
            # Consider only positive frequencies up to max_cycle_years
            mask = (freqs > 0) & (freqs < 1/max_cycle_years)
            periods = 1/freqs[mask]  # Convert to periods in years
            power_filtered = power[mask]
            
            # Find peaks in the power spectrum
            # Note: In a full implementation, you'd use a peak finding algorithm
            # Here we'll just take the top N peaks
            indices = np.argsort(power_filtered)[::-1][:5]  # Top 5 peaks
            top_periods = periods[indices]
            top_powers = power_filtered[indices]
            
            # Normalize powers
            normalized_powers = top_powers / np.max(top_powers)
            
            # Construct result
            cycles = []
            for i, (period, power) in enumerate(zip(top_periods, normalized_powers)):
                cycles.append({
                    'period_years': float(period),
                    'period_days': float(period * 252),
                    'strength': float(power),
                    'rank': i + 1
                })
            
            result = {
                'symbol': symbol,
                'lookback_period': period,
                'cycles': cycles,
                'data_points': len(prices),
                'sampling_rate': sampling_rate,
                'current_price': prices[-1]
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.set(cache_key, result, expire=86400)  # 24 hour TTL
                
            return result
        except Exception as e:
            logger.error(f"Error detecting market cycles for {symbol}: {str(e)}")
            raise ValueError(f"Error detecting market cycles for {symbol}: {str(e)}")
    
    async def filter_market_noise(
        self,
        symbol: str,
        period: str = "1y",
        cutoff_percent: float = 10.0
    ) -> Dict[str, Any]:
        """
        Filter market noise using FFT-based filtering.
        
        Args:
            symbol: Stock symbol
            period: Historical data period
            cutoff_percent: Percentage of high-frequency components to filter out
            
        Returns:
            Dict: Filtered price data
        """
        cache_key = f"filtered_prices:{symbol}:{period}:{cutoff_percent}"
        
        if self.cache_service:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        try:
            # Get historical price data
            historical_data = await self.market_data_service.get_historical_data(symbol, period=period)
            
            # Extract dates and closing prices
            dates = [entry['date'] for entry in historical_data]
            prices = np.array([entry['close'] for entry in historical_data])
            
            # Calculate returns
            returns = np.diff(np.log(prices))
            
            # Compute FFT of returns
            fft_values = fft(returns)
            
            # Create a filter that keeps low frequencies and removes high frequencies
            n = len(fft_values)
            cutoff = int(n * (1 - cutoff_percent/100) / 2)
            
            # Filter in frequency domain (set high frequencies to zero)
            filter_mask = np.ones(n, dtype=bool)
            filter_mask[cutoff:-cutoff] = False
            filtered_fft = np.where(filter_mask, fft_values, 0)
            
            # Inverse FFT to get filtered returns
            filtered_returns = ifft(filtered_fft).real
            
            # Reconstruct prices from filtered returns
            filtered_prices = np.zeros(len(prices))
            filtered_prices[0] = prices[0]
            for i in range(1, len(filtered_prices)):
                filtered_prices[i] = filtered_prices[i-1] * np.exp(filtered_returns[i-1])
            
            # Construct result with both original and filtered prices
            result = {
                'symbol': symbol,
                'period': period,
                'cutoff_percent': cutoff_percent,
                'dates': dates,
                'original_prices': prices.tolist(),
                'filtered_prices': filtered_prices.tolist()
            }
            
            # Cache the result
            if self.cache_service:
                await self.cache_service.set(cache_key, result, expire=3600)  # 1 hour TTL
                
            return result
        except Exception as e:
            logger.error(f"Error filtering market noise for {symbol}: {str(e)}")
            raise ValueError(f"Error filtering market noise for {symbol}: {str(e)}") 