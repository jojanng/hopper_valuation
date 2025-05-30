This is a python project for financial analysis and valuation of stocks. 

## Features

- **Market Data Service**: Yahoo Finance API with fallback strategy
- **Manual Valuation Engine**: Multiple valuation models with customizable weights
- **Historical Valuation**: Historical comparison between stock price and fair value

## Getting Started


### Installation 

1. Clone the repository
2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Unix or MacOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```
   cp .env.example .env
   ```
5. Run the application:
   ```
   python app.py
   ```   

## Disclaimer

The information provided is for general informational and educational purposes only. It should not be construed as financial, investment, or legal advice. Always do your own research and consult with a certified financial advisor before making any investment decisions. I am not responsible for any financial losses you may incur.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 