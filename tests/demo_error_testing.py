#!/usr/bin/env python3
"""
Demo script showing how to test Gmail authentication errors

This script demonstrates how to use the error testing tools to improve
Gmail authentication error detection in the Moodle scraper.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and show its output"""
    print(f"\n🚀 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Command completed successfully")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print("❌ Command failed")
            if result.stderr:
                print("Error:")
                print(result.stderr)
        
    except Exception as e:
        print(f"❌ Failed to run command: {e}")

def main():
    print("🧪 Gmail Authentication Error Testing Demo")
    print("="*60)
    print("""
This demo shows how to test and improve Gmail authentication error detection.

STEP 1: Test current error detection
STEP 2: Capture error elements when authentication fails  
STEP 3: Analyze captured data to improve error patterns
STEP 4: Apply improvements to the scraper

Let's start!
""")
    
    # Check if required dependencies are available
    print("🔍 Checking dependencies...")
    
    try:
        import playwright
        print("✅ Playwright is available")
    except ImportError:
        print("❌ Playwright not available")
        print("Install with: pip install playwright && playwright install chromium")
        return
    
    # Show available test scripts
    test_dir = Path(__file__).parent
    scripts = [
        ("quick_gmail_error_test.py", "Quick test for Gmail authentication errors"),
        ("test_gmail_auth_errors.py", "Comprehensive authentication error testing"),
        ("enhance_error_detection.py", "Analyze results and generate improvements")
    ]
    
    print(f"\n📁 Available test scripts in {test_dir}:")
    for script, description in scripts:
        script_path = test_dir / script
        exists = "✅" if script_path.exists() else "❌"
        print(f"   {exists} {script} - {description}")
    
    # Interactive menu
    print("\n" + "="*60)
    print("Choose what to do:")
    print("1. Run quick Gmail error test (recommended first)")
    print("2. Run comprehensive error testing")
    print("3. Analyze captured error data")
    print("4. Show current error detection patterns")
    print("0. Exit")
    
    try:
        choice = input("\nEnter your choice (0-4): ").strip()
        
        if choice == "1":
            print("\n🧪 Running Quick Gmail Error Test...")
            print("This will test invalid email and wrong password scenarios.")
            
            headless = input("Run in headless mode? (y/N): ").strip().lower() == 'y'
            cmd = [sys.executable, "quick_gmail_error_test.py"]
            if headless:
                cmd.append("--headless")
            
            run_command(cmd, "Quick Gmail Error Test")
            
        elif choice == "2":
            print("\n🧪 Running Comprehensive Error Testing...")
            
            # Get parameters
            moodle_url = input("Enter Moodle URL (optional): ").strip()
            test_email = input("Enter test email for wrong password tests (optional): ").strip()
            headless = input("Run in headless mode? (y/N): ").strip().lower() == 'y'
            
            cmd = [sys.executable, "test_gmail_auth_errors.py"]
            if headless:
                cmd.append("--headless")
            if moodle_url:
                cmd.extend(["--moodle-url", moodle_url])
            if test_email:
                cmd.extend(["--test-email", test_email])
            
            run_command(cmd, "Comprehensive Authentication Error Testing")
            
        elif choice == "3":
            print("\n🔍 Analyzing Captured Error Data...")
            run_command([sys.executable, "enhance_error_detection.py"], "Error Data Analysis")
            
        elif choice == "4":
            print("\n📋 Current Error Detection Patterns:")
            show_current_patterns()
            
        elif choice == "0":
            print("👋 Goodbye!")
            
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

def show_current_patterns():
    """Show the current error detection patterns from the scraper"""
    try:
        # Read the current patterns from moodle_direct_scraper.py
        scraper_path = Path(__file__).parent.parent / "moodle_direct_scraper.py"
        
        if not scraper_path.exists():
            print("❌ Could not find moodle_direct_scraper.py")
            return
        
        with open(scraper_path, 'r') as f:
            content = f.read()
        
        # Extract error patterns (simple regex would be better, but this works)
        lines = content.split('\n')
        in_email_patterns = False
        in_password_patterns = False
        
        email_patterns = []
        password_patterns = []
        
        for line in lines:
            line = line.strip()
            
            if 'email_error_patterns = [' in line:
                in_email_patterns = True
                continue
            elif 'password_error_patterns = [' in line:
                in_password_patterns = True
                continue
            elif line == ']' and (in_email_patterns or in_password_patterns):
                in_email_patterns = False
                in_password_patterns = False
                continue
            
            if in_email_patterns and line.startswith('"') and line.endswith('",'):
                email_patterns.append(line[1:-2])  # Remove quotes and comma
            elif in_password_patterns and line.startswith('"') and line.endswith('",'):
                password_patterns.append(line[1:-2])  # Remove quotes and comma
        
        print("\n📧 Current Email Error Patterns:")
        for pattern in email_patterns:
            print(f"   • {pattern}")
        
        print("\n🔒 Current Password Error Patterns:")
        for pattern in password_patterns:
            print(f"   • {pattern}")
            
        print(f"\n📊 Total patterns: {len(email_patterns)} email + {len(password_patterns)} password")
        
    except Exception as e:
        print(f"❌ Failed to read current patterns: {e}")

if __name__ == "__main__":
    main()
