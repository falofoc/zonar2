# Amazon Price Tracker (ZONAR - زونار)

A Flask web application that tracks Amazon Saudi Arabia product prices and notifies users when prices change or reach their target price.

## Features

- Track Amazon Saudi Arabia product prices
- Set target prices for products
- Receive notifications for price changes
- Support for both Arabic and English languages
- Light/Dark theme support
- Price history tracking
- User authentication system

## Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/amazonsa2.git
cd amazonsa2
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```
FLASK_APP=app.py
FLASK_ENV=development
AMAZON_REFERRAL_CODE=your_referral_code
```

5. Run the application:
```bash
python app.py
```

The application will be available at http://localhost:8080

## Requirements

- Python 3.8+
- Flask
- SQLAlchemy
- APScheduler
- Other dependencies listed in requirements.txt

## License

MIT License # zonar2
