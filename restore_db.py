#!/usr/bin/env python3
"""
Database backup and restore script for Render.com deployments.
This script helps maintain persistent data between deployments by:
1. Creating a backup of the database before each deployment
2. Restoring from backup if the database is empty after a new deployment
"""

import os
import sys
import shutil
import datetime
import sqlite3
import traceback

def backup_database():
    """Create a backup of the database to a persistent location"""
    try:
        # Paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.join(base_dir, 'instance')
        db_file = os.path.join(db_dir, 'amazon_tracker.db')
        
        # For Render deployment, check if we're using /tmp
        tmp_db_file = '/tmp/amazon_tracker.db'
        if os.path.exists(tmp_db_file):
            db_file = tmp_db_file
            print(f"Using production database path: {db_file}")
        
        # Backup location
        backup_dir = '/opt/render/project/src/.backup'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create timestamped backup
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'amazon_tracker_{timestamp}.db')
        
        if os.path.exists(db_file):
            print(f"Backing up database from {db_file} to {backup_file}")
            shutil.copy2(db_file, backup_file)
            
            # Also keep a latest version
            latest_backup = os.path.join(backup_dir, 'amazon_tracker_latest.db')
            shutil.copy2(db_file, latest_backup)
            
            # Test that the backup is valid
            conn = sqlite3.connect(backup_file)
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM sqlite_master")
            tables = cursor.fetchone()[0]
            conn.close()
            
            print(f"Backup completed successfully. Backup contains {tables} tables.")
            return True
        else:
            print(f"Database file {db_file} does not exist. No backup created.")
            return False
            
    except Exception as e:
        print(f"Error backing up database: {str(e)}")
        traceback.print_exc()
        return False

def restore_database():
    """Restore the database from the latest backup if needed"""
    try:
        # Paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.join(base_dir, 'instance')
        db_file = os.path.join(db_dir, 'amazon_tracker.db')
        
        # For Render deployment
        is_production = os.environ.get('RENDER', False)
        if is_production:
            db_file = '/tmp/amazon_tracker.db'
            print(f"Using production database path: {db_file}")
        
        # Create db directory if it doesn't exist
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        
        # Backup location
        backup_dir = '/opt/render/project/src/.backup'
        latest_backup = os.path.join(backup_dir, 'amazon_tracker_latest.db')
        
        # Check if database exists and has tables
        db_empty = True
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = cursor.fetchall()
                db_empty = len(tables) == 0
                conn.close()
                
                if not db_empty:
                    print(f"Existing database has {len(tables)} tables. No restore needed.")
                    return True
                else:
                    print("Existing database is empty. Restore needed.")
            except Exception as e:
                print(f"Error checking database: {str(e)}")
                # Assume empty if error
                db_empty = True
        
        # Restore if needed
        if db_empty and os.path.exists(latest_backup):
            print(f"Restoring database from {latest_backup} to {db_file}")
            shutil.copy2(latest_backup, db_file)
            
            # Verify restoration
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()
            conn.close()
            
            print(f"Database restored successfully. Found {len(tables)} tables.")
            return True
        elif not os.path.exists(latest_backup):
            print("No backup found for restoration.")
            return False
        
        return True
            
    except Exception as e:
        print(f"Error restoring database: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else None
    
    if action == 'backup':
        success = backup_database()
    elif action == 'restore':
        success = restore_database()
    else:
        print("Usage: python restore_db.py [backup|restore]")
        success = False
    
    sys.exit(0 if success else 1) 