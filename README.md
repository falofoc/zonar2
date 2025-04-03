# Amazon SA Price Tracker

A web application that tracks prices of products on Amazon Saudi Arabia. Get notified when prices drop or change on your favorite items.

## Features

- Track product prices from Amazon Saudi Arabia
- Receive notifications for price drops and changes
- Customizable target price alerts
- Mobile-responsive design
- Bilingual support (English/Arabic)
- Dark/Light theme
- Price history visualization
- Easy product management

## Tech Stack

- Python/Flask
- SQLAlchemy
- Bootstrap 5
- JavaScript
- SQLite

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/amazonsa2.git
cd amazonsa2
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and add:
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your_secret_key
MAIL_SERVER=your_mail_server
MAIL_PORT=your_mail_port
MAIL_USERNAME=your_mail_username
MAIL_PASSWORD=your_mail_password
MAIL_USE_TLS=True
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Usage

1. Sign up for an account
2. Add Amazon SA products by pasting their URLs
3. Set target prices (optional)
4. Enable tracking for products you want to monitor
5. Get notified when prices change

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
