import numpy as np
from scipy.stats import norm

def risk_neutral_pricing(u, S0, rate, q, sigma, T):
    """
    Calculates risk-neutral pricing function (used for option pricing prediction) for log(S_T) 
        Consistent price growth due to risk-free & no need to estimate arbitrage
        Ensure fair pricing based on current market data = better for options prediction
    """
    i = complex(0, 1)
    return np.exp(i * u * (np.log(S0) + (rate - q - 0.5 * sigma**2) * T) - 0.5 * sigma**2 * u**2 * T)

def real_world_pricing(u, S0, mu, q, sigma, T):
    """
    Calculates real-world pricing function (used for stocks pricing prediction) for log(S_T)
        Inconsistent price growth due to risk premium
        Ensure accurate pricing based on current market data = better for stocks prediction
    """
    i = complex(0, 1)
    return np.exp(i * u * (np.log(S0) + (mu - q - 0.5 * sigma**2) * T) - 0.5 * sigma**2 * u**2 * T)

def char_function_fft(S0, K, T, rate, mu, q, sigma, use_real_world=False, N=4096, alpha=1.5, eta=0.25):
    """
    Carr-Madan FFT characteristic function for option pricing & stocks price modeling
    Allows switching between risk-neutral (rate) and real-world (mu) pricing
    """
    lambda_ = 2 * np.pi / (N * eta)
    b = lambda_ * N / 2
    
    u = eta * np.arange(N)
    k = -b + lambda_ * np.arange(N)
    v = u - (alpha + 1) * 1j

    if use_real_world:
        psi = np.exp(-mu * T) * real_world_pricing(v, S0, mu, q, sigma, T) / (alpha**2 + alpha - u**2 + 1j * (2 * alpha + 1) * u)
    else:
        psi = np.exp(-rate * T) * risk_neutral_pricing(v, S0, rate, q, sigma, T) / (alpha**2 + alpha - u**2 + 1j * (2 * alpha + 1) * u)
    
    x = np.exp(1j * b * u) * psi * eta
    z = np.fft.fft(x)
    
    call_prices = np.exp(-alpha * k) / np.pi * np.real(z)
    
    k_index = np.abs(np.exp(k) - K).argmin()
    call_price = call_prices[k_index]
    put_price = call_price - S0 * np.exp(-q * T) + K * np.exp(-((rate if rate is not None else mu) * T))

    """
    The 1 (PDF) tells us where the stock prices (ST) are likely to end up and the 2 tells us its probability of ST
    being above the targeted strike price (K) given X maturity by integrating PDF from K to infinity 
    """

    # 1 Probability Density Function (how likely different stock prices are at maturity)
    s_vals = np.linspace(S0 * 0.5, S0 * 2, 1000)
    log_returns = np.log(s_vals/S0)

    if use_real_world:
        density = (1/(s_vals * sigma * np.sqrt(2 * np.pi * T))) * \
                 np.exp(-(log_returns - (mu - q - 0.5 * sigma**2) * T)**2 / (2 * sigma**2 * T))
    else:
        density = (1/(s_vals * sigma * np.sqrt(2 * np.pi * T))) * \
                 np.exp(-(log_returns - (rate - q - 0.5 * sigma**2) * T)**2 / (2 * sigma**2 * T))

    # 2 Probability of stock price at maturity > strike price (% of when u i the green)
    d1 = (np.log(S0/K) + ((mu if use_real_world else rate) - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    prob_ST_above_K = 1 - norm.cdf(-d1)

    return max(0, call_price), max(0, put_price), prob_ST_above_K, s_vals, density

def stock_price_algo(S0, T, rate, mu, q, use_real_world):
    """ 
    Predicts the expected stock price in X years
    """
    if use_real_world:
        expected_price = S0 * np.exp((mu - q) * T) 
    else:
        expected_price = S0 * np.exp((rate - q) * T) # maybe remove using risk free rate
    return expected_price    

def discounted_cash_flow(fcf, growth_rate, discount_rate, years=10, terminal_growth=0.02):
    """
    Calculates the intrinsic value using the Discounted Cash Flow (DCF) model
        fcf: Current Free Cash Flow (float)
        growth_rate: Expected annual growth rate (float, in decimal form)
        discount_rate: Required rate of return (float, in decimal form)
        years: Projection years (int, default 10)
        terminal_growth: Terminal growth rate after forecast period (float, default 2%)
    """
    future_cash_flows = [fcf * (1 + growth_rate) ** year for year in range(1, years + 1)]
    discounted_fcf = [fcf / ((1 + discount_rate) ** year) for year, fcf in enumerate(future_cash_flows, 1)]
    terminal_value = (future_cash_flows[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    terminal_value_discounted = terminal_value / ((1 + discount_rate) ** years)
    
    intrinsic_value = sum(discounted_fcf) + terminal_value_discounted
    return intrinsic_value

def peg_ratio(pe_ratio, earnings_growth):
    """
    Calculates PEG Ratio for valuation
        pe_ratio: Price-to-Earnings ratio (float)
        earnings_growth: Expected growth rate in decimal form (float)
    """
    if earnings_growth == 0:
        return None  
    return pe_ratio / (earnings_growth * 100)  # in percentage growth
