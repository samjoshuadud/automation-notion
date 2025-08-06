#!/usr/bin/env python3
"""
Setup script for Moodle Assignment Fetcher
"""

import os
import subprocess
import sys

def check_python_version():
    """Check if Python 3.6+ is available"""
    if sys.version_info < (3, 6):
        print("❌ Python 3.6 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your credentials")
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("ℹ️  .env file already exists")
    return True

def make_scripts_executable():
    """Make shell scripts executable"""
    scripts = ['daily_check.sh']
    for script in scripts:
        if os.path.exists(script):
            os.chmod(script, 0o755)
            print(f"✅ Made {script} executable")

def test_import():
    """Test if all imports work"""
    print("🧪 Testing imports...")
    try:
        import imaplib
        import email
        import re
        import json
        import os
        from datetime import datetime, timedelta
        from typing import List, Dict, Optional, Tuple
        print("✅ All core modules imported successfully")
        
        try:
            from dotenv import load_dotenv
            print("✅ python-dotenv imported successfully")
        except ImportError:
            print("❌ python-dotenv not available")
            return False
        
        try:
            import requests
            print("✅ requests imported successfully")
        except ImportError:
            print("❌ requests not available")
            return False
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Moodle Assignment Fetcher...")
    print("=" * 50)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if success and not install_dependencies():
        success = False
    
    # Test imports
    if success and not test_import():
        success = False
    
    # Create .env file
    if success and not create_env_file():
        success = False
    
    # Make scripts executable
    if success:
        make_scripts_executable()
    
    print("=" * 50)
    
    if success:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your Gmail credentials")
        print("2. Test connection: python3 run_fetcher.py --test")
        print("3. Run manual check: python3 run_fetcher.py")
        print("4. Set up cron job for daily checks")
        print("\nSee README.md for detailed instructions.")
    else:
        print("❌ Setup failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
