# Qualtrim Backend

A robust financial analysis and valuation API with advanced features.

## Project Structure

```
qualtrim_backend/
│
├── api/                    # API Layer
│   ├── __init__.py
│   ├── app.py              # FastAPI application
│   ├── routes/             # API endpoints
│   │   ├── __init__.py
│   │   ├── valuation.py    
│   │   ├── market_data.py  
│   │   └── options.py      
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py         # Authentication
│       └── rate_limit.py   # Rate limiting
│
├── services/               # Business Logic Layer
│   ├── __init__.py
│   ├── market_data/        # Market Data Service
│   │   ├── __init__.py
│   │   ├── service.py      
│   │   └── providers/      # Multiple data sources
│   │       ├── __init__.py
│   │       ├── yahoo.py    
│   │       ├── alpha_vantage.py
│   │       └── finnhub.py  
│   │
│   ├── valuation/          # Valuation Engine
│   │   ├── __init__.py
│   │   ├── service.py      
│   │   └── models/         
│   │       ├── __init__.py
│   │       ├── dcf.py      
│   │       ├── pe.py       
│   │       └── ev_ebitda.py
│   │
│   └── analytics/          # Analytics Engine
│       ├── __init__.py
│       ├── service.py      
│       ├── fft/            # FFT analysis
│   │   ├── __init__.py
│   │   ├── option_pricing.py
│   │   └── market_cycles.py
│   │
│   └── ml/             # Machine learning
│       ├── __init__.py
│       └── growth_prediction.py
│
├── database/               # Data Layer
│   ├── __init__.py
│   ├── models.py           # Database models
│   ├── time_series.py      # Time series database
│   └── cache.py            # Cache database
│
├── utils/                  # Utilities
│   ├── __init__.py
│   ├── logging.py          
│   └── error_handling.py   
│
├── config/                 # Configuration
│   ├── __init__.py
│   └── settings.py         
│
└── docker/                 # Containerization
    ├── Dockerfile
    └── docker-compose.yml
```

## Features

- **Market Data Service**: Multi-provider support with fallback strategy
- **Valuation Engine**: Multiple valuation models with customizable weights
- **Analytics Engine**: FFT-based option pricing and market cycle detection
- **API Layer**: RESTful endpoints with authentication and rate limiting
- **Database Layer**: PostgreSQL, TimescaleDB, and Redis for caching

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis
- TimescaleDB (optional)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   cp .env.example .env
   ```
4. Run the application:
   ```
   uvicorn api.app:app --reload
   ```

### Docker

To run with Docker:

```
docker-compose up -d
```

## API Documentation

API documentation is available at `/docs` when the server is running.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 