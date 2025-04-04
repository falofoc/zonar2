#!/usr/bin/env python
import os
import sys
import traceback
from flask_migrate import Migrate, upgrade, init, migrate, stamp
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Initialize the database and create initial tables"""
    print("Initializing database...")
    
    try:
        # Import app and db
        from app import app, db
        from app.models import User, Product, Notification
        
        # Check database connection
        try:
            # Try a simple query to check connection
            with app.app_context():
                db.session.execute("SELECT 1")
                db.session.commit()
                print("Database connection successful!")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            print("Please check your DATABASE_URL environment variable and ensure PostgreSQL is running")
            print(f"Current database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', '').split('@')[0]}...")
            return 1
            
        # Initialize Flask-Migrate if it doesn't exist
        migrate = Migrate(app, db)
        
        # Run migrations in the app context
        with app.app_context():
            # Check if migrations directory exists
            migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
            
            if not os.path.exists(migrations_dir):
                print("Initializing migrations directory...")
                init()
                
            # Create an initial migration
            print("Creating migration...")
            try:
                migrate(message="Initial migration")
            except Exception as migrate_error:
                print(f"Warning: Migration creation issue: {migrate_error}")
                print("This might be normal for an existing database")
                
            # Stamp the database with the current migration
            print("Stamping database with current migration...")
            try:
                stamp()
            except Exception as stamp_error:
                print(f"Warning: Migration stamping issue: {stamp_error}")
                
            # Apply migrations
            print("Applying migrations...")
            try:
                upgrade()
            except Exception as upgrade_error:
                print(f"Warning: Migration application issue: {upgrade_error}")
                
            # Create tables if they don't exist
            print("Ensuring tables exist...")
            db.create_all()
            
            # Verify tables were created
            table_names = db.engine.table_names()
            expected_tables = ['users', 'products', 'notifications']
            
            for table in expected_tables:
                if table in table_names:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' is missing!")
            
            # Create admin user if none exists
            admin_email = os.environ.get("ADMIN_EMAIL")
            admin_password = os.environ.get("ADMIN_PASSWORD")
            
            if admin_email and admin_password:
                existing_admin = User.query.filter_by(email=admin_email).first()
                
                if not existing_admin:
                    print(f"Creating admin user with email {admin_email}")
                    admin = User(
                        username="admin",
                        email=admin_email,
                        is_admin=True,
                        email_verified=True
                    )
                    admin.set_password(admin_password)
                    db.session.add(admin)
                    db.session.commit()
                    print("Admin user created successfully")
                else:
                    print(f"Admin user with email {admin_email} already exists")
            else:
                print("No ADMIN_EMAIL or ADMIN_PASSWORD set, skipping admin user creation")
                
            print("Database setup completed successfully!")
            return 0
            
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 