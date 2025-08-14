#!/usr/bin/env python3
"""
Quick Gmail Error Testing Script

A simplified script to quickly test Gmail authentication errors and capture 
the exact elements and error messages that appear when:
1. Email is incorrect/not found
2. Password is wrong

This helps improve the error detection patterns in moodle_direct_scraper.py

Usage:
    python quick_gmail_error_test.py
    python quick_gmail_error_test.py --headless
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright not available. Install with: pip install playwright")


def capture_error_state(page, scenario_name: str):
    """Capture the current page state focusing on error elements"""
    print(f"\n📸 Capturing state for: {scenario_name}")
    
    try:
        # Get basic page info
        url = page.url
        title = page.title()
        page_text = page.content()
        
        print(f"   🌐 URL: {url}")
        print(f"   📄 Title: {title}")
        
        # Look for error elements with specific selectors
        error_info = {
            "scenario": scenario_name,
            "url": url,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "errors_found": [],
            "visible_text": []
        }
        
        # Google-specific error selectors
        google_error_selectors = [
            '[role="alert"]',
            '.Ekjuhf',  # Google error message class
            '#identifierId_error',  # Email field error
            '#password_error',  # Password field error
            '[jsname="B34EJ"]',  # Google error container
            '.dEOOab',  # Google error text
            '[data-error]',
            '.error-msg',
            '.warning-msg'
        ]
        
        print("   🔍 Checking for error elements...")
        for selector in google_error_selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    if elem.is_visible():
                        text = elem.inner_text().strip()
                        if text:
                            error_info["errors_found"].append({
                                "selector": selector,
                                "text": text,
                                "html": elem.inner_html()
                            })
                            print(f"   ❗ Found error: {text}")
            except Exception as e:
                print(f"   ⚠️  Selector {selector} failed: {e}")
        
        # Look for any visible text that might indicate errors
        try:
            # Get all text content and look for error keywords
            all_text = page.evaluate("document.body.innerText").lower()
            
            error_keywords = [
                "couldn't find your google account",
                "couldn't find an account",
                "email doesn't exist", 
                "no account found",
                "enter a valid email",
                "wrong email",
                "invalid email address",
                "couldn't find your account",
                "wrong password",
                "incorrect password", 
                "invalid password",
                "password is incorrect",
                "try again",
                "sign-in error",
                "verify it's you",
                "account not found"
            ]
            
            found_keywords = []
            for keyword in error_keywords:
                if keyword in all_text:
                    found_keywords.append(keyword)
                    print(f"   🔍 Found keyword: '{keyword}'")
            
            error_info["found_keywords"] = found_keywords
            
        except Exception as e:
            print(f"   ⚠️  Failed to extract text: {e}")
        
        # Take screenshot
        screenshot_dir = Path(__file__).parent / "error_screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        screenshot_path = screenshot_dir / f"{scenario_name}_{datetime.now().strftime('%H%M%S')}.png"
        page.screenshot(path=str(screenshot_path))
        error_info["screenshot"] = str(screenshot_path)
        print(f"   📸 Screenshot saved: {screenshot_path}")
        
        # Save JSON data
        json_dir = Path(__file__).parent / "error_data"
        json_dir.mkdir(exist_ok=True)
        json_path = json_dir / f"{scenario_name}_{datetime.now().strftime('%H%M%S')}.json"
        with open(json_path, 'w') as f:
            json.dump(error_info, f, indent=2)
        print(f"   💾 Data saved: {json_path}")
        
        return error_info
        
    except Exception as e:
        print(f"   ❌ Failed to capture state: {e}")
        return {"error": str(e)}


def test_invalid_email(page):
    """Test with an invalid email address"""
    print("\n🧪 Testing Invalid Email Scenario")
    
    invalid_email = "nonexistent.test.email.12345@gmail.com"
    print(f"   📧 Using email: {invalid_email}")
    
    try:
        # Go to Google sign-in
        print("   🌐 Navigating to Google sign-in...")
        page.goto("https://accounts.google.com/signin", wait_until='domcontentloaded')
        time.sleep(2)
        
        # Find email input
        email_selectors = [
            'input[type="email"]',
            'input[name="identifier"]',
            'input[id="identifierId"]'
        ]
        
        email_input = None
        for selector in email_selectors:
            try:
                email_input = page.wait_for_selector(selector, timeout=5000)
                if email_input and email_input.is_visible():
                    print(f"   ✅ Found email input: {selector}")
                    break
            except:
                continue
        
        if not email_input:
            print("   ❌ Could not find email input field")
            return False
        
        # Enter invalid email
        print("   ⌨️  Entering invalid email...")
        email_input.fill("")
        time.sleep(0.5)
        email_input.type(invalid_email)
        time.sleep(1)
        
        # Capture state before submission
        capture_error_state(page, "invalid_email_before_submit")
        
        # Click Next or press Enter
        print("   👆 Submitting email...")
        try:
            next_button = page.query_selector('#identifierNext')
            if next_button and next_button.is_visible():
                next_button.click()
            else:
                email_input.press("Enter")
        except:
            email_input.press("Enter")
        
        # Wait for response
        print("   ⏳ Waiting for response...")
        time.sleep(4)
        
        # Capture state after submission
        error_info = capture_error_state(page, "invalid_email_after_submit")
        
        # Check if we found any errors
        if error_info.get("errors_found") or error_info.get("found_keywords"):
            print("   ✅ Error detection successful!")
            return True
        else:
            print("   ⚠️  No clear error detected - may need better patterns")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False


def test_wrong_password(page):
    """Test with a valid email but wrong password"""
    print("\n🧪 Testing Wrong Password Scenario")
    
    # Note: Using a common email that's likely to exist but with wrong password
    test_email = input("Enter a valid Gmail address to test wrong password (or press Enter to skip): ").strip()
    
    if not test_email:
        print("   ⏭️  Skipping wrong password test")
        return False
    
    wrong_password = "definitely_wrong_password_12345"
    print(f"   📧 Using email: {test_email}")
    print(f"   🔒 Using wrong password: {'*' * len(wrong_password)}")
    
    try:
        # Go to Google sign-in
        print("   🌐 Navigating to Google sign-in...")
        page.goto("https://accounts.google.com/signin", wait_until='domcontentloaded')
        time.sleep(2)
        
        # Enter email
        email_input = page.wait_for_selector('input[type="email"], input[name="identifier"], input[id="identifierId"]', timeout=5000)
        if email_input:
            print("   ⌨️  Entering email...")
            email_input.fill("")
            email_input.type(test_email)
            time.sleep(1)
            
            # Click Next
            try:
                next_button = page.query_selector('#identifierNext')
                if next_button:
                    next_button.click()
                else:
                    email_input.press("Enter")
            except:
                email_input.press("Enter")
            
            # Wait for password field
            print("   ⏳ Waiting for password field...")
            time.sleep(3)
            
            # Enter wrong password
            password_input = page.wait_for_selector('input[type="password"]', timeout=10000)
            if password_input:
                print("   ⌨️  Entering wrong password...")
                password_input.fill("")
                password_input.type(wrong_password)
                time.sleep(1)
                
                # Capture state before submission
                capture_error_state(page, "wrong_password_before_submit")
                
                # Click Sign in
                print("   👆 Submitting password...")
                try:
                    signin_button = page.query_selector('#passwordNext')
                    if signin_button and signin_button.is_visible():
                        signin_button.click()
                    else:
                        password_input.press("Enter")
                except:
                    password_input.press("Enter")
                
                # Wait for response
                print("   ⏳ Waiting for response...")
                time.sleep(4)
                
                # Capture state after submission
                error_info = capture_error_state(page, "wrong_password_after_submit")
                
                # Check if we found any errors
                if error_info.get("errors_found") or error_info.get("found_keywords"):
                    print("   ✅ Password error detection successful!")
                    return True
                else:
                    print("   ⚠️  No clear password error detected")
                    return False
            else:
                print("   ❌ Could not find password field")
                return False
        else:
            print("   ❌ Could not find email field")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Quick Gmail error testing")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()
    
    print("🧪 Quick Gmail Authentication Error Testing")
    print("=" * 50)
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright is required but not installed.")
        print("Install with: pip install playwright && playwright install chromium")
        return
    
    # Create output directories
    Path(__file__).parent.joinpath("error_screenshots").mkdir(exist_ok=True)
    Path(__file__).parent.joinpath("error_data").mkdir(exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        try:
            # Test 1: Invalid email
            invalid_email_success = test_invalid_email(page)
            
            # Test 2: Wrong password
            wrong_password_success = test_wrong_password(page)
            
            print("\n" + "="*50)
            print("📊 RESULTS SUMMARY")
            print("="*50)
            print(f"❗ Invalid email test: {'✅ PASS' if invalid_email_success else '❌ FAIL'}")
            print(f"🔒 Wrong password test: {'✅ PASS' if wrong_password_success else '❌ FAIL'}")
            
            print(f"\n📁 Screenshots saved in: {Path(__file__).parent / 'error_screenshots'}")
            print(f"📄 JSON data saved in: {Path(__file__).parent / 'error_data'}")
            print("\n💡 Use this data to improve error detection patterns in moodle_direct_scraper.py")
            
        finally:
            browser.close()


if __name__ == "__main__":
    main()
