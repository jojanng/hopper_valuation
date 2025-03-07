import yfinance as yf
import numpy as np
from scipy.fft import fft
from scipy.stats import norm
from algorithms.market_data import get_analyst_growth_estimates, get_manual_fcf


def get_financial_data(symbol):
    """Get comprehensive financial data for valuation methods"""
    stock = yf.Ticker(symbol)
    info = stock.info
    
    # Get basic financial data
    market_cap = info.get('marketCap', 0)
    shares_outstanding = info.get('sharesOutstanding', 0)
    current_price = info.get('currentPrice', 0)
    
    # Get balance sheet data
    balance_sheet = stock.balance_sheet
    total_debt = 0
    cash_and_equivalents = 0
    
    if not balance_sheet.empty:
        if 'Total Debt' in balance_sheet.index:
            total_debt = balance_sheet.loc['Total Debt'].iloc[0]
        elif 'Long Term Debt' in balance_sheet.index:
            total_debt = balance_sheet.loc['Long Term Debt'].iloc[0]
        
        if 'Cash And Cash Equivalents' in balance_sheet.index:
            cash_and_equivalents = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
    
    # Get income statement data
    income_stmt = stock.income_stmt
    net_income = 0
    ebitda = 0
    
    if not income_stmt.empty:
        if 'Net Income' in income_stmt.index:
            net_income = income_stmt.loc['Net Income'].iloc[0]
        
        if 'EBITDA' in income_stmt.index:
            ebitda = income_stmt.loc['EBITDA'].iloc[0]
    
    # Get growth rates
    earnings_growth = info.get('earningsGrowth', 0.05)
    revenue_growth = info.get('revenueGrowth', 0.03)
    
    # Calculate enterprise value
    enterprise_value = market_cap + total_debt - cash_and_equivalents
    
    return {
        'market_cap': market_cap,
        'shares_outstanding': shares_outstanding,
        'current_price': current_price,
        'total_debt': total_debt,
        'cash_and_equivalents': cash_and_equivalents,
        'ebitda': ebitda,
        'net_income': net_income,
        'enterprise_value': enterprise_value,
        'earnings_growth': earnings_growth,
        'revenue_growth': revenue_growth,
        'pe_ratio': info.get('trailingPE', None)  # Fetch P/E ratio, use None if not available
    }

def discounted_cash_flow(fcf, growth_rate, discount_rate, years=10, terminal_growth=0.02, net_debt=0, shares_outstanding=1):
    """
    Calculates the intrinsic value using the Discounted Cash Flow (DCF) model
    Parameters:
        fcf: Current Free Cash Flow
        growth_rate: Expected annual growth rate (decimal)
        discount_rate: Required rate of return (decimal)
        years: Projection years (default 10)
        terminal_growth: Terminal growth rate (default 2%)
        net_debt: Total debt minus cash and cash equivalents
        shares_outstanding: Number of shares outstanding
    """
    # Ensure we have valid inputs
    if fcf <= 0 or shares_outstanding <= 0:
        return {
            'enterprise_value': 0,
            'equity_value': 0,
            'per_share_value': 0
        }
    
    # Calculate future cash flows and discount them
    future_cash_flows = [fcf * (1 + growth_rate) ** year for year in range(1, years + 1)]
    discounted_fcf = [fcf / ((1 + discount_rate) ** year) for year, fcf in enumerate(future_cash_flows, 1)]
    
    # Calculate terminal value and discount it
    terminal_value = (future_cash_flows[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    terminal_value_discounted = terminal_value / ((1 + discount_rate) ** years)
    
    # Calculate enterprise value
    enterprise_value = sum(discounted_fcf) + terminal_value_discounted
    
    # Calculate equity value
    equity_value = enterprise_value - net_debt
    
    # Calculate per share value
    per_share_value = equity_value / shares_outstanding
    
    return {
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'per_share_value': per_share_value
    }

def pe_based_valuation(eps, growth_rate, target_pe=None):
    """
    PE-based valuation using PEG ratio and growth
    Returns None if EPS is negative
    """
    if eps <= 0:
        return {
            'target_pe': None,
            'fair_value': None
        }
    
    # If target PE not provided, calculate based on growth rate and company profile
    if target_pe is None:
        # Base PE on growth rate but with more realistic multiples
        growth_rate_percent = growth_rate * 100
        
        if growth_rate <= 0.10:  # Low growth (<=10%)
            target_pe = 15 + growth_rate_percent  # 15-25x PE
        elif growth_rate <= 0.20:  # Medium growth (10-20%)
            target_pe = 20 + growth_rate_percent  # 25-40x PE
        elif growth_rate <= 0.30:  # High growth (20-30%)
            target_pe = 30 + growth_rate_percent  # 40-60x PE
        else:  # Very high growth (>30%)
            target_pe = 40 + (growth_rate_percent * 0.5)  # 40-65x PE
    
    # Limit PE to reasonable range based on growth
    min_pe = max(15, growth_rate_percent)  # Minimum PE is higher of 15 or growth rate
    max_pe = min(65, growth_rate_percent * 3)  # Maximum PE is lower of 65 or 3x growth rate
    target_pe = min(max(target_pe, min_pe), max_pe)
    
    # Calculate fair value based on PE
    fair_value = eps * target_pe
    
    return {
        'target_pe': target_pe,
        'fair_value': fair_value
    }

def peg_ratio(pe_ratio, growth_rate):
    """
    Calculate the Price/Earnings to Growth (PEG) ratio
    
    Parameters:
        pe_ratio (float): The Price/Earnings ratio
        growth_rate (float): The growth rate as a decimal (e.g., 0.15 for 15%)
        
    Returns:
        float: The PEG ratio (PE ratio divided by growth rate percentage)
        
    A PEG ratio of 1 is considered fair value.
    Less than 1 may indicate undervaluation, greater than 1 may indicate overvaluation.
    """
    if pe_ratio is None or growth_rate <= 0:
        return None
    
    # Convert growth rate to percentage for PEG calculation
    growth_rate_percent = growth_rate * 100
    
    # Calculate PEG ratio
    peg = pe_ratio / growth_rate_percent
    
    return peg

def ev_ebitda_valuation(ebitda, growth_rate, net_debt, shares_outstanding):
    """
    Enterprise Value to EBITDA valuation
    Returns None if EBITDA is negative
    """
    if ebitda <= 0 or shares_outstanding <= 0:
        return {
            'ev_ebitda_multiple': None,
            'enterprise_value': None,
            'equity_value': None,
            'per_share_value': None
        }
    
    # Determine appropriate EV/EBITDA multiple based on growth rate
    growth_rate_percent = growth_rate * 100
    
    if growth_rate <= 0.10:  # Low growth (<=10%)
        ev_ebitda_multiple = 10 + growth_rate_percent  # 10-20x
    elif growth_rate <= 0.20:  # Medium growth (10-20%)
        ev_ebitda_multiple = 15 + growth_rate_percent  # 15-35x
    elif growth_rate <= 0.30:  # High growth (20-30%)
        ev_ebitda_multiple = 20 + growth_rate_percent  # 20-50x
    else:  # Very high growth (>30%)
        ev_ebitda_multiple = 25 + (growth_rate_percent * 0.5)  # 25-40x
    
    # Limit multiple to reasonable range based on growth
    min_multiple = max(10, growth_rate_percent)  # Minimum 10x or growth rate
    max_multiple = min(50, growth_rate_percent * 2.5)  # Maximum 50x or 2.5x growth rate
    ev_ebitda_multiple = min(max(ev_ebitda_multiple, min_multiple), max_multiple)
    
    # Calculate enterprise value
    enterprise_value = ebitda * ev_ebitda_multiple
    
    # Calculate equity value
    equity_value = enterprise_value - net_debt
    
    # Calculate per share value
    per_share_value = equity_value / shares_outstanding
    
    return {
        'ev_ebitda_multiple': ev_ebitda_multiple,
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'per_share_value': per_share_value
    }

def weighted_valuation(symbol, custom_dcf_growth=None, custom_earnings_growth=None):
    """
    Calculate weighted valuation using multiple methods:
    1. DCF Valuation (50%)
    2. P/E Based Valuation (30%)
    3. EV/EBITDA Valuation (20%)
    
    Allows for optional custom growth rate overrides for DCF and earnings.
    """
    # Get financial data and free cash flow
    data = get_financial_data(symbol)
    fcf = get_manual_fcf(symbol)  # This is now in billions
    net_debt = data['total_debt'] - data['cash_and_equivalents']
    
    # Get stock info and analyst estimates
    stock = yf.Ticker(symbol)
    info = stock.info

    # Determine earnings growth from analyst estimates (fallback if negative)
    raw_earnings_growth = info.get("earningsGrowth")
    if raw_earnings_growth is None or raw_earnings_growth < 0:
        raw_earnings_growth = get_analyst_growth_estimates(stock)
    
    # Use custom earnings growth if provided, otherwise enforce a minimum of 10% and a cap of 30%
    earnings_growth = custom_earnings_growth if custom_earnings_growth is not None else max(min(raw_earnings_growth, 0.30), 0.10)
    
    # For DCF, you might adjust earnings growth or get a different input.
    # One simple approach is to assume free cash flow grows slightly slower.
    dcf_growth = custom_dcf_growth if custom_dcf_growth is not None else earnings_growth * 0.9

    # Terminal growth from revenue estimates (default to 2% if missing), capped between 1% and 3%
    revenue_growth = info.get("revenueGrowth", 0.02)
    terminal_growth = max(min(revenue_growth if revenue_growth > 0 else 0.02, 0.03), 0.01)
    
    # Calculate valuations with a fixed discount rate (adjust as needed)
    dcf_result = discounted_cash_flow(
        fcf=fcf,  # FCF is already in billions
        growth_rate=dcf_growth,
        discount_rate=0.10,
        terminal_growth=terminal_growth,
        net_debt=net_debt,
        shares_outstanding=data['shares_outstanding']
    )
    
    # For P/E valuation, if EPS is negative, this method is skipped
    eps = data['net_income'] / data['shares_outstanding'] if data['shares_outstanding'] > 0 else 0
    pe_result = pe_based_valuation(eps=eps, growth_rate=earnings_growth)
    
    # For EV/EBITDA valuation, ensure EBITDA is positive
    ev_ebitda_result = ev_ebitda_valuation(
        ebitda=data['ebitda'],
        growth_rate=dcf_growth,
        net_debt=net_debt,
        shares_outstanding=data['shares_outstanding']
    )
    
    # Combine methods, but only include those that return a positive per share value
    total_weight = 0
    weighted_value = 0
    if dcf_result['per_share_value'] > 0:
        weighted_value += dcf_result['per_share_value'] * 0.5
        total_weight += 0.5
    if pe_result['fair_value'] is not None and pe_result['fair_value'] > 0:
        weighted_value += pe_result['fair_value'] * 0.3
        total_weight += 0.3
    if ev_ebitda_result['per_share_value'] is not None and ev_ebitda_result['per_share_value'] > 0:
        weighted_value += ev_ebitda_result['per_share_value'] * 0.2
        total_weight += 0.2
    
    if total_weight > 0:
        weighted_value = weighted_value / total_weight
    else:
        weighted_value = 0

    results = {
        'symbol': symbol,
        'current_price': data['current_price'],
        'weighted_value': weighted_value,
        'upside_potential': (weighted_value / data['current_price'] - 1) * 100 if data['current_price'] > 0 else 0,
        'dcf_value': dcf_result['per_share_value'],
        'pe_value': pe_result['fair_value'],
        'ev_ebitda_value': ev_ebitda_result['per_share_value'],
        'details': {
            'dcf': {
                'enterprise_value': dcf_result['enterprise_value'],
                'equity_value': dcf_result['equity_value'],
                'growth_rate': dcf_growth,
                'weight': 0.5
            },
            'pe': {
                'target_pe': pe_result['target_pe'],
                'eps': eps,
                'growth_rate': earnings_growth,
                'weight': 0.3 if (pe_result['fair_value'] is not None and pe_result['fair_value'] > 0) else 0
            },
            'ev_ebitda': {
                'multiple': ev_ebitda_result['ev_ebitda_multiple'],
                'ebitda': data['ebitda'],
                'enterprise_value': ev_ebitda_result['enterprise_value'],
                'equity_value': ev_ebitda_result['equity_value'],
                'weight': 0.2 if (ev_ebitda_result['per_share_value'] is not None and ev_ebitda_result['per_share_value'] > 0) else 0
            },
            'financial': {
                'market_cap': data['market_cap'],
                'shares_outstanding': data['shares_outstanding'],
                'net_debt': net_debt,
                'fcf': fcf * 1e9,  # Store FCF in actual dollars for display
                'ebitda': data['ebitda'],
                'net_income': data['net_income']
            }
        }
    }
    
    return results

def print_valuation_report(results):
    """Print a formatted valuation report with the results"""
    print("\nComprehensive Valuation Report:")
    print("=" * 50)
    
    # Current price and fair value
    current_price = results.get('current_price', 0)
    weighted_value = results.get('weighted_value', 0)
    
    # Sanity check for weighted value - if it's unreasonably high, it's likely a scaling issue
    if weighted_value > 10000:
        # Attempt to rescale
        scale_factor = 1
        if weighted_value > 1000000:
            scale_factor = 1e6
        elif weighted_value > 1000:
            scale_factor = 1e3
        weighted_value = weighted_value / scale_factor
    
    print(f"Current Market Price: ${current_price:.2f}")
    print(f"Weighted Fair Value: ${weighted_value:.2f}")
    
    # Calculate potential upside/downside
    if weighted_value is not None and current_price is not None and current_price > 0:
        diff_percent = ((weighted_value - current_price) / current_price) * 100
        print(f"Potential {'Upside' if diff_percent > 0 else 'Downside'}: {abs(diff_percent):.1f}%")
    
    # Valuation Methods
    print("\nValuation Methods:")
    dcf_value = results.get('dcf_value', 0)
    pe_value = results.get('pe_value', 0)
    ev_ebitda_value = results.get('ev_ebitda_value', 0)
    details = results.get('details', {})
    
    # Sanity check for DCF value - if it's unreasonably high, it's likely a scaling issue
    if dcf_value > 10000:
        # Attempt to rescale
        scale_factor = 1
        if dcf_value > 1000000:
            scale_factor = 1e6
        elif dcf_value > 1000:
            scale_factor = 1e3
        dcf_value = dcf_value / scale_factor
    
    # Format DCF value properly
    dcf_weight = details.get('dcf', {}).get('weight', 0) * 100
    pe_weight = details.get('pe', {}).get('weight', 0) * 100
    ev_weight = details.get('ev_ebitda', {}).get('weight', 0) * 100
    
    print(f"1. DCF Value: ${dcf_value:.2f} (Weight: {dcf_weight:.0f}%)")
    print(f"2. P/E Based Value: ${pe_value:.2f} (Weight: {pe_weight:.0f}%)")
    print(f"3. EV/EBITDA Value: ${ev_ebitda_value:.2f} (Weight: {ev_weight:.0f}%)")
    
    # Financial Metrics
    print("\nFinancial Metrics:")
    fin = details.get('financial', {})
    market_cap = fin.get('market_cap', 0)
    net_debt = fin.get('net_debt', 0)
    fcf = fin.get('fcf', 0)
    eps = details.get('pe', {}).get('eps', 0)
    ebitda = fin.get('ebitda', 0)
    
    # Convert large numbers to billions for readability
    print(f"Market Cap: ${market_cap/1e9:.2f}B")
    print(f"Net Debt: ${net_debt/1e9:.2f}B")
    print(f"FCF (TTM): ${fcf/1e9:.2f}B")  # Ensure FCF is displayed in billions
    print(f"EPS: ${eps:.2f}")
    print(f"EBITDA: ${ebitda/1e9:.2f}B")
    
    # Growth Assumptions
    print("\nGrowth Assumptions:")
    dcf_growth = details.get('dcf', {}).get('growth_rate', 0)
    earnings_growth = details.get('pe', {}).get('growth_rate', 0)
    print(f"DCF Growth Rate: {dcf_growth*100:.1f}%")
    print(f"Earnings Growth: {earnings_growth*100:.1f}%")
    print("=" * 50)

def char_function_fft(S0, K, T, r, mu, q, sigma, use_real_world=False):
    """
    Calculate option prices using FFT method with characteristic function
    Parameters:
    S0: Current stock price
    K: Strike price
    T: Time to maturity
    r: Risk-free rate (if not using real-world)
    mu: Real-world expected return (if using real-world)
    q: Dividend yield
    sigma: Volatility
    use_real_world: Whether to use real-world drift instead of risk-free rate
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
    prob_ST_above_K = 1 - norm.cdf(d1)
    
    return call_price, put_price, prob_ST_above_K, k, damped_char

def stock_price_algo(S0, T, r, mu, q, use_real_world=False):
    """
    Calculate expected stock price using the appropriate drift
    """
    drift = mu if use_real_world else r
    return S0 * np.exp((drift - q) * T)
