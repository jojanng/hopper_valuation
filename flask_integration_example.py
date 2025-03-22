"""
Flask Integration Example

This script demonstrates how to integrate the new Hopper backend architecture
with your existing Flask application.
"""

from flask import Flask, request, jsonify, render_template
import asyncio
import logging

# Import services from the new architecture
from hopper_backend.services.market_data.service import MarketDataService
from hopper_backend.services.valuation.service import ValuationService
from hopper_backend.services.analytics.fft.service import FFTAnalysisService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize services
market_data_service = MarketDataService()
valuation_service = ValuationService(market_data_service)
fft_service = FFTAnalysisService(market_data_service)

# Helper function to run async code in Flask
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Routes
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/stock-data', methods=['GET'])
def get_stock_data():
    symbol = request.args.get('symbol', '').upper()
    
    if not symbol:
        return jsonify({"error": "Stock symbol is required"}), 400

    try:
        # Use the new market data service
        current_price = run_async(market_data_service.get_current_price(symbol))
        volatility = run_async(market_data_service.get_historical_volatility(symbol))
        
        # Get financial data for dividend yield
        financial_data = run_async(market_data_service.get_financial_data(symbol))
        dividend_yield = financial_data.get('dividendYield', 0.0) / 100.0 if financial_data.get('dividendYield') else 0.0
        
        # Get FCF for reference
        fcf = financial_data.get('freeCashFlow', 0)
        
        return jsonify({
            "symbol": symbol,
            "current_price": current_price,
            "historical_volatility": volatility,
            "risk_free_rate": 0.0425,  # Fixed value for now
            "dividend_yield": dividend_yield,
            "annual_fcf": fcf / 1e9  # Convert to billions for display
        })
    except Exception as e:
        logger.error(f"Error fetching stock data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/valuation', methods=['GET'])
def get_valuation():
    symbol = request.args.get('symbol', '').upper()
    custom_growth = request.args.get('growth_rate')
    
    if custom_growth:
        try:
            custom_growth = float(custom_growth)
        except ValueError:
            return jsonify({"error": "Invalid growth rate"}), 400
    else:
        custom_growth = None
    
    if not symbol:
        return jsonify({"error": "Stock symbol is required"}), 400

    try:
        # Use the new valuation service
        valuation_result = run_async(valuation_service.calculate_intrinsic_value(
            symbol=symbol,
            custom_dcf_growth=custom_growth
        ))
        
        return jsonify(valuation_result)
    except Exception as e:
        logger.error(f"Error calculating valuation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/options', methods=['GET'])
def get_options():
    symbol = request.args.get('symbol', '').upper()
    strike_price = request.args.get('strike')
    time_to_maturity = request.args.get('maturity')
    use_real_world = request.args.get('real_world', 'false').lower() == 'true'
    
    if not symbol:
        return jsonify({"error": "Stock symbol is required"}), 400
    
    try:
        strike_price = float(strike_price) if strike_price else None
        time_to_maturity = float(time_to_maturity) if time_to_maturity else 0.25  # Default to 3 months
        
        if not strike_price:
            # If strike price not provided, use current price
            current_price = run_async(market_data_service.get_current_price(symbol))
            strike_price = current_price  # At-the-money
        
        # Use the new FFT service
        option_result = run_async(fft_service.option_pricing(
            symbol=symbol,
            strike_price=strike_price,
            time_to_maturity=time_to_maturity,
            use_real_world=use_real_world
        ))
        
        return jsonify(option_result)
    except Exception as e:
        logger.error(f"Error calculating option prices: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/market-cycles', methods=['GET'])
def get_market_cycles():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '5y')
    
    if not symbol:
        return jsonify({"error": "Stock symbol is required"}), 400

    try:
        # Use the new FFT service
        cycles_result = run_async(fft_service.detect_market_cycles(
            symbol=symbol,
            period=period
        ))
        
        return jsonify(cycles_result)
    except Exception as e:
        logger.error(f"Error detecting market cycles: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 