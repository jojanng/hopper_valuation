from flask import Flask, request, jsonify, render_template
from algorithms import market_data as mkdata
from algorithms import pricing as prc
import yfinance as yf

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/stock-data', methods=['GET'])
def get_stock_data():
    symbol = request.args.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"error": "Stock symbol is required"}), 400

    try:
        S0, sigma, r, q = get_market_parameters(symbol)
        return jsonify({
            "symbol": symbol,
            "current_price": S0,
            "historical_volatility": sigma,
            "risk_free_rate": r,
            "dividend_yield": q
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_market_parameters(symbol):
    """Fetch market parameters"""
    S0 = mkdata.get_current_price(symbol)
    sigma = mkdata.get_historical_volatility(symbol)
    r = 0.0425  # Risk-free rate
    div = yf.Ticker(symbol).info.get('dividendYield', 0.0) or 0.0
    q = div / 100
    return S0, sigma, r, q

@app.route('/pricing', methods=['GET'])
def get_pricing():
    symbol = request.args.get('symbol', '').upper()
    K = float(request.args.get('strike_price', 0))
    T = float(request.args.get('time_to_maturity', 1))
    use_real_world = request.args.get('real_world', 'false').lower() == 'true'
    cagr = float(request.args.get('cagr', 10)) / 100  

    if not symbol:
        return jsonify({"error": "Stock symbol is required"}), 400

    try:
        # Get market parameters
        S0, sigma, r, q = get_market_parameters(symbol)
        mu = cagr if use_real_world else None
        rate = None if use_real_world else r

        # Calculate option prices
        call_price, put_price, prob_ST_above_K, _, _ = prc.char_function_fft(S0, K, T, rate, mu, q, sigma, use_real_world)
        expected_price = prc.stock_price_algo(S0, T, rate, mu, q, use_real_world)

        # Get intrinsic value data
        fcf, growth_rate, terminal_growth_rate, discount_rate, pe_ratio, earnings_growth = mkdata.get_intrinsic_value_data(symbol)
        intrinsic_value = prc.discounted_cash_flow(fcf, growth_rate, discount_rate, terminal_growth=terminal_growth_rate)

        # Get shares outstanding
        stock = yf.Ticker(symbol)
        shares_outstanding = stock.info.get("sharesOutstanding", 0)  # Avoid division by 0

        

        # Calculate Intrinsic Value Per Share
        intrinsic_value_per_share = intrinsic_value / shares_outstanding

        # Calculate PEG ratio
        peg_ratio = prc.peg_ratio(pe_ratio, earnings_growth) if earnings_growth > 0 else None

        return jsonify({
            "symbol": symbol,
            "current_price": S0,
            "historical_volatility": sigma,
            "risk_free_rate": r,
            "dividend_yield": q,
            "expected_return": mu if use_real_world else None,

            "call_price": call_price,
            "put_price": put_price,
            "probability_above_strike": prob_ST_above_K,
            "expected_price": expected_price,

            "intrinsic_value_per_share": intrinsic_value_per_share,
            "fcf": fcf / 1e9,
            "growth_rate": growth_rate,
            "terminal_growth_rate": terminal_growth_rate,
            "discount_rate": discount_rate,
            "pe_ratio": pe_ratio,
            "earnings_growth": earnings_growth,
            "peg_ratio": peg_ratio
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
