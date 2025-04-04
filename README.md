# Zonar - Product Price Tracker

Zonar is a web application that allows users to track product prices from Amazon and other online retailers. Get notified when prices drop, analyze price history, and make informed purchasing decisions.

## Features

- Track prices of products from Amazon and other retailers
- Receive notifications when prices drop
- View price history charts
- Set target prices for alerts
- User authentication and profile management
- Responsive design for desktop and mobile

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **Hosting**: Render

## Setting Up on Render

Zonar is designed to be easily deployed on Render with PostgreSQL for data persistence.

### 1. Create a PostgreSQL Database on Render

1. Log in to your Render dashboard
2. Go to "New" → "PostgreSQL"
3. Configure the database:
   - Name: `zonar-db` (or your preferred name)
   - Database: `zonar` (or your preferred name)
   - User: `zonar_user` (or your preferred name)
   - Region: Choose the closest to your users
   - Plan: Select your preferred plan
4. Click "Create Database"
5. After creation, copy the "Internal Database URL" for use in the next step

### 2. Create a Web Service on Render

1. Go to "New" → "Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - Name: `zonar` (or your preferred name)
   - Runtime: Python 3
   - Build Command: `./build.sh`
   - Start Command: `gunicorn app:app`
   - Instance Type: Select your preferred plan
4. Add the following environment variables:
   - `DATABASE_URL`: Paste the PostgreSQL Internal Database URL from step 1
   - `SECRET_KEY`: Generate a random string for security (e.g., `openssl rand -hex 32`)
   - `ADMIN_EMAIL`: Email address for the admin user
   - `ADMIN_PASSWORD`: Password for the admin user
   - `RENDER`: Set to `true` to indicate production environment
5. Click "Create Web Service"

### 3. Set Up Scheduled Database Backups (Optional)

To preserve your data, you can set up a scheduled job to run periodic database backups:

1. Go to "New" → "Cron Job"
2. Configure the job:
   - Name: `zonar-db-backup`
   - Command: `python backup_db.py`
   - Schedule: `0 0 * * *` (daily at midnight)
3. Add the same `DATABASE_URL` environment variable as used in the web service
4. Click "Create Cron Job"

## Development Setup

### Prerequisites

- Python 3.8+
- pip
- PostgreSQL (or SQLite for local development)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/falofoc/zonar2.git
   cd zonar2
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/zonar
   SECRET_KEY=your_secret_key
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=strong_password
   ```

5. Initialize the database:
   ```
   python setup_db.py
   ```

6. Run the application:
   ```
   flask run
   ```

7. Access the application at http://localhost:5000

## Data Migration and Recovery

The application includes tools for database migration and recovery:

- **Migrations**: The app uses Flask-Migrate to handle database schema changes. When you make model changes, run:
  ```
  flask db migrate -m "Description of changes"
  flask db upgrade
  ```

- **Backups**: Run `python backup_db.py` to manually create a database backup. Backups are stored in the `backups` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For support or inquiries, please contact:
- Email: info@zonar.com
- Twitter: @zonarapp
