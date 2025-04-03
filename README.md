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
- Supabase integration for database storage

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
SECRET_KEY=your_secret_key

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

5. Set up Supabase:
   - Create a Supabase account at [supabase.com](https://supabase.com)
   - Create a new project and get your API credentials
   - For detailed instructions, see [SUPABASE_SETUP.md](SUPABASE_SETUP.md)

6. Run the application:
```bash
python app.py
```

The application will be available at http://localhost:3000

## Migrating from SQLite to Supabase

If you have an existing SQLite database and want to migrate to Supabase:

```bash
python migrate_to_supabase.py
```

## Requirements

- Python 3.8+
- Flask
- Supabase Python Client
- APScheduler
- Other dependencies listed in requirements.txt

## Deployment

The application can be deployed on Render.com using the provided `render.yaml` configuration file. Make sure to set the Supabase environment variables in your deployment dashboard.

## License

MIT License
