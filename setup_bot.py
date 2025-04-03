#!/usr/bin/env python3
"""
Amazon Bot Setup Script

This script helps set up the Amazon Bot as a system service.
It creates necessary directories, verifies dependencies, and provides
instructions for setting up a systemd service for the bot.
"""

import os
import sys
import subprocess
import getpass
import platform
import random
import string

def generate_password(length=16):
    """Generate a secure random password"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*()-_=+'
    return ''.join(random.choice(chars) for _ in range(length))

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'sqlite3', 'requests', 'bs4', 
        'fake_useragent', 'schedule', 'lxml', 'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if package == 'sqlite3':  # sqlite3 is built into Python
            continue
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def create_systemd_service(script_path, username):
    """Create a systemd service file for the bot"""
    service_content = f"""[Unit]
Description=Amazon.sa Bot Service
After=network.target

[Service]
User={username}
WorkingDirectory={os.path.dirname(script_path)}
Environment="BOT_PASSWORD={generate_password()}"
ExecStart=/usr/bin/python3 {os.path.join(script_path, 'bot_scheduler_direct.py')}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_path = os.path.join(script_path, 'amazon_bot.service')
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    return service_path

def make_scripts_executable(script_path):
    """Make the bot scripts executable"""
    scripts = [
        'amazon_bot_direct.py',
        'bot_scheduler_direct.py',
        'setup_bot.py'
    ]
    
    for script in scripts:
        script_file = os.path.join(script_path, script)
        if os.path.exists(script_file):
            try:
                # Change file mode to executable (equivalent to chmod +x)
                current_mode = os.stat(script_file).st_mode
                executable_mode = current_mode | 0o111  # Add executable bit for user, group, others
                os.chmod(script_file, executable_mode)
                print(f"Made {script} executable ✓")
            except Exception as e:
                print(f"Error making {script} executable: {str(e)}")

def main():
    """Main setup function"""
    print("=======================================")
    print("Amazon.sa Bot Setup")
    print("=======================================")
    
    # 1. Check Python version
    python_version = platform.python_version_tuple()
    if int(python_version[0]) < 3 or (int(python_version[0]) == 3 and int(python_version[1]) < 6):
        print("Error: Python 3.6 or higher is required.")
        sys.exit(1)
    
    print(f"Python version: {platform.python_version()} ✓")
    
    # 2. Check dependencies
    print("\nChecking required packages...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print("The following packages are missing and need to be installed:")
        for package in missing_packages:
            print(f"- {package}")
        
        print("\nPlease install them using:")
        print(f"pip install {' '.join(missing_packages)}")
        print("Or run: pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("All required packages are installed ✓")
    
    # 3. Verify bot script exists
    script_path = os.path.dirname(os.path.abspath(__file__))
    amazon_bot_path = os.path.join(script_path, 'amazon_bot_direct.py')
    bot_scheduler_path = os.path.join(script_path, 'bot_scheduler_direct.py')
    
    if not os.path.exists(amazon_bot_path) or not os.path.exists(bot_scheduler_path):
        print("Error: Bot scripts not found. Make sure both amazon_bot_direct.py and bot_scheduler_direct.py are in the same directory.")
        sys.exit(1)
    
    print("Bot scripts found ✓")
    
    # 4. Check if database exists
    db_path = os.path.join(script_path, 'instance', 'amazon_tracker.db')
    if not os.path.exists(db_path):
        print(f"Warning: Database not found at {db_path}")
        print("Make sure your Amazon Tracker application is set up correctly before running the bot.")
    else:
        print("Database found ✓")
    
    # 5. Make scripts executable
    print("\nMaking scripts executable...")
    make_scripts_executable(script_path)
    
    # 6. Create systemd service file
    print("\nCreating systemd service file...")
    username = getpass.getuser()
    service_path = create_systemd_service(script_path, username)
    print(f"Service file created at: {service_path} ✓")
    
    # 7. Print installation instructions
    print("\n=======================================")
    print("Installation Instructions")
    print("=======================================")
    print(f"1. Copy the service file to systemd directory:")
    print(f"   sudo cp {service_path} /etc/systemd/system/")
    print("\n2. Reload systemd daemon:")
    print("   sudo systemctl daemon-reload")
    print("\n3. Enable the service to start on boot:")
    print("   sudo systemctl enable amazon_bot.service")
    print("\n4. Start the service:")
    print("   sudo systemctl start amazon_bot.service")
    print("\n5. Check status:")
    print("   sudo systemctl status amazon_bot.service")
    print("\nThe bot is configured to run daily at 9:00 AM to find and add")
    print("the top 10 products with discounts of 10% or more from Amazon.sa.")
    print("\nLogs will be available at:")
    print(f"- {os.path.join(script_path, 'logs/amazon_bot.log')}")
    print(f"- {os.path.join(script_path, 'logs/bot_scheduler.log')}")
    print("\nTo test the bot immediately, run:")
    print(f"   python {amazon_bot_path}")
    print("=======================================")

if __name__ == "__main__":
    main() 