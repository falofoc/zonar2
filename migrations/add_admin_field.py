#!/usr/bin/env python3
"""
Migration script to add is_admin field to existing users.
This is needed for older database instances that don't have this field.
"""

import os
from app import app, db
from sqlalchemy import Column, Boolean
from sqlalchemy.ext.declarative import declarative_base

def migrate_database():
    try:
        print("Starting migration to add is_admin field...")
        
        # Check if the field already exists
        with app.app_context():
            from app.models import User
            
            # Try to access the field to see if it exists
            try:
                test_user = User.query.first()
                if test_user:
                    # Access the field to check if it exists
                    admin_status = test_user.is_admin
                    print("is_admin field already exists, no migration needed.")
                    return True
            except Exception as e:
                # Field doesn't exist, need to add it
                print(f"is_admin field not found: {e}")
                print("Adding is_admin field to User model...")
            
            # Add the field
            Base = declarative_base()
            engine = db.engine
            
            # Get the actual table name
            table_name = User.__tablename__
            
            from sqlalchemy import MetaData, Table, Column, Boolean
            
            # Add the column
            metadata = MetaData()
            metadata.bind = engine
            
            # Get the table
            user_table = Table(table_name, metadata, autoload=True)
            
            # Check if column already exists
            if 'is_admin' not in user_table.columns:
                # Add the column
                from alembic import op
                with op.batch_alter_table(table_name) as batch_op:
                    batch_op.add_column(Column('is_admin', Boolean(), server_default='0'))
                
                print("Successfully added is_admin field to User model")
                
                # Commit the changes
                db.session.commit()
            else:
                print("is_admin column already exists")
            
            return True
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Create migrations directory if it doesn't exist
    if not os.path.exists('migrations'):
        os.makedirs('migrations')
        
    success = migrate_database()
    
    if success:
        print("Migration completed successfully")
    else:
        print("Migration failed")
        exit(1) 