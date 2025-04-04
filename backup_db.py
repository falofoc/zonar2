#!/usr/bin/env python
import os
import sys
import json
import datetime
import traceback
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def backup_database():
    """
    Create a backup of the PostgreSQL database
    
    This script uses pg_dump to create a backup of the database.
    It can be run manually or scheduled with cron.
    
    Returns:
        0 on success, 1 on failure
    """
    try:
        # Get DATABASE_URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("Error: DATABASE_URL not set. Cannot backup database.")
            return 1
            
        # Parse the DATABASE_URL to get connection details
        # Format: postgresql://username:password@host:port/database
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            
        # Skip backup for SQLite
        if database_url.startswith('sqlite:'):
            print("SQLite database detected. Skipping backup (not needed for local development).")
            return 0
            
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate timestamp for backup filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')
        
        # Extract database connection info from URL
        # Note: This assumes the standard PostgreSQL URL format
        try:
            # postgresql://username:password@host:port/database
            url_parts = database_url.replace('postgresql://', '').split('@')
            auth = url_parts[0].split(':')
            host_parts = url_parts[1].split('/')
            
            username = auth[0]
            password = auth[1] if len(auth) > 1 else None
            host_port = host_parts[0].split(':')
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            database = host_parts[1]
            
            # Set PGPASSWORD environment variable for pg_dump
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
                
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', database,
                '-F', 'p',  # plain text format
                '-f', backup_file
            ]
            
            # Run pg_dump
            print(f"Creating database backup to {backup_file}...")
            subprocess.run(cmd, env=env, check=True)
            
            # Create backup metadata file
            metadata = {
                'timestamp': timestamp,
                'date': datetime.datetime.now().isoformat(),
                'database': database,
                'host': host,
                'backup_file': backup_file,
                'size_bytes': os.path.getsize(backup_file)
            }
            
            with open(f"{backup_file}.meta.json", 'w') as f:
                json.dump(metadata, f, indent=2)
                
            print(f"Backup completed successfully: {backup_file}")
            print(f"Backup size: {metadata['size_bytes'] / 1024 / 1024:.2f} MB")
            
            # Cleanup old backups (keep last 5)
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql')]
            backup_files.sort(reverse=True)  # Most recent first
            
            if len(backup_files) > 5:
                for old_file in backup_files[5:]:
                    old_path = os.path.join(backup_dir, old_file)
                    meta_path = f"{old_path}.meta.json"
                    
                    # Remove old backup and its metadata
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    if os.path.exists(meta_path):
                        os.remove(meta_path)
                        
                print(f"Removed {len(backup_files) - 5} old backups, keeping the 5 most recent.")
                
            return 0
                
        except Exception as parse_error:
            print(f"Error parsing DATABASE_URL: {parse_error}")
            print("Please make sure the DATABASE_URL is in the format: postgresql://username:password@host:port/database")
            return 1
            
    except subprocess.CalledProcessError as e:
        print(f"Error executing pg_dump: {e}")
        return 1
        
    except Exception as e:
        print(f"Error backing up database: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(backup_database()) 