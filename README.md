# Boom-Bust Sentinel

An automated financial market monitoring system that tracks key indicators and sends alerts when significant market conditions are detected.

## Project Structure

```
boom-bust-sentinel/
├── scrapers/           # Data scraper implementations
│   ├── __init__.py
│   └── base.py        # Base scraper interface
├── services/          # Core services
│   ├── __init__.py
│   ├── state_store.py # Data persistence
│   ├── alert_service.py # Alert notifications
│   └── metrics_service.py # Monitoring metrics
├── models/            # Data models
│   ├── __init__.py
│   └── core.py       # Core data structures
├── config/           # Configuration
│   ├── __init__.py
│   └── settings.py   # Application settings
├── tests/            # Test suite
│   ├── __init__.py
│   └── test_base_scraper.py
├── main.py           # Main entry point
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Features

- **Bond Issuance Monitoring**: Track weekly investment-grade tech bond issuance
- **BDC Discount Tracking**: Monitor Business Development Company discount-to-NAV ratios
- **Credit Fund Analysis**: Watch private credit fund asset marks for stress signals
- **Bank Provisioning**: Track bank provisions for non-bank financial exposures
- **Multi-channel Alerts**: Email, SMS, and Telegram notifications
- **Web Dashboard**: Real-time monitoring interface
- **Serverless Architecture**: Low-ops deployment on AWS Lambda/Google Cloud Functions

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (see config/settings.py for required variables)

## Usage

```bash
python main.py
```

## Testing

Run the test suite:
```bash
pytest tests/
```

## Development Status

This project is currently under development. Core interfaces and structure are in place.

## License

MIT License