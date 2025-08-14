#!/usr/bin/env python3
"""
Moodle SSO Gmail Authentication Error Testing

Tests authentication errors through the actual Moodle SSO flow
instead of directly on Google accounts (which blocks automation).

This tests the real user flow that the moodle_direct_scraper.py uses.
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
    print("❌ Playwright not available")

from moodle_direct_scraper import MoodleSession


def capture_moodle_sso_state(page, scenario_name: str):
    """Capture page state during Moodle SSO authentication"""
    print(f"\n📸 Capturing Moodle SSO state: {scenario_name}")
    
    try:
        url = page.url
        title = page.title()
        
        print(f"   🌐 URL: {url}")
        print(f"   📄 Title: {title}")
        
        error_info = {
            "scenario": scenario_name,
            "url": url,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "errors_found": [],
            "form_elements": [],
            "found_keywords": []
        }
        
        # Look for error elements (both Moodle and Google)
        error_selectors = [
            # Google SSO error selectors
            '[role="alert"]',
            '.Ekjuhf',
            '#identifierId_error',
            '#password_error',
            '[jsname="B34EJ"]',
            '.dEOOab',
            '[data-error]',
            
            # Moodle error selectors
            '.alert',
            '.alert-error',
            '.alert-danger',
            '.error',
            '.warning',
            '#error-message',
            '.form-error',
            '.login-error',
            '[class*="error"]',
            '[class*="alert"]'
        ]
        
        print("   🔍 Checking for error elements...")
        for selector in error_selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    if elem.is_visible():
                        text = elem.inner_text().strip()
                        if text and len(text) > 2:  # Ignore empty or very short text
                            error_info["errors_found"].append({
                                "selector": selector,
                                "text": text,
                                "html": elem.inner_html()[:200]  # Limit HTML length
                            })
                            print(f"   ❗ Found error: {text}")
            except Exception as e:
                print(f"   ⚠️  Selector {selector} failed: {e}")
        
        # Capture form elements
        form_selectors = [
            'input[type="email"]',
            'input[type="password"]',
            'input[name="identifier"]',
            'input[id="identifierId"]',
            'input[name="username"]',
            'input[name="password"]'
        ]
        
        for selector in form_selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    if elem.is_visible():
                        error_info["form_elements"].append({
                            "selector": selector,
                            "placeholder": elem.get_attribute("placeholder") or "",
                            "value": elem.input_value() if hasattr(elem, 'input_value') else "",
                            "enabled": elem.is_enabled()
                        })
            except:
                continue
        
        # Look for error keywords in page text
        try:
            all_text = page.evaluate("document.body.innerText").lower()
            
            error_keywords = [
                # Email errors
                "couldn't find your google account",
                "couldn't find an account",
                "email doesn't exist",
                "no account found",
                "enter a valid email",
                "wrong email",
                "invalid email address",
                "couldn't find your account",
                
                # Password errors
                "wrong password",
                "incorrect password",
                "invalid password",
                "password is incorrect",
                "try again",
                "sign-in error",
                
                # Moodle specific errors
                "login failed",
                "authentication failed",
                "invalid credentials",
                "access denied",
                "unable to log in",
                "login error"
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
        screenshot_dir = Path(__file__).parent / "moodle_sso_screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%H%M%S')
        screenshot_path = screenshot_dir / f"{scenario_name}_{timestamp}.png"
        page.screenshot(path=str(screenshot_path))
        error_info["screenshot"] = str(screenshot_path)
        print(f"   📸 Screenshot saved: {screenshot_path}")
        
        # Save JSON data
        json_dir = Path(__file__).parent / "moodle_sso_data"
        json_dir.mkdir(exist_ok=True)
        json_path = json_dir / f"{scenario_name}_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(error_info, f, indent=2)
        print(f"   💾 Data saved: {json_path}")
        
        return error_info
        
    except Exception as e:
        print(f"   ❌ Failed to capture state: {e}")
        return {"error": str(e)}


def test_moodle_sso_invalid_email(moodle_url: str):
    """Test invalid email through Moodle SSO"""
    print("\n🧪 Testing Invalid Email through Moodle SSO")
    print(f"   🌐 Moodle URL: {moodle_url}")
    
    invalid_email = "invalid.test.email.123@gmail.com"
    invalid_password = "wrong_password_123"
    
    print(f"   📧 Using invalid email: {invalid_email}")
    
    try:
        # Create MoodleSession with invalid credentials
        session = MoodleSession(
            moodle_url=moodle_url,
            headless=False,  # Keep visible to see what happens
            google_email=invalid_email,
            google_password=invalid_password
        )
        
        # Start browser
        if not session.start_browser():
            print("   ❌ Failed to start browser")
            return False
        
        print("   ✅ Browser started")
        
        # Open Moodle login page
        if not session.open_login_page():
            print("   ❌ Failed to open Moodle login page")
            return False
        
        print("   ✅ Opened Moodle login page")
        
        # Capture initial state
        initial_state = capture_moodle_sso_state(session.page, "moodle_sso_initial")
        
        # Try automated Google login (this should fail)
        print("   🔄 Attempting automated Google login with invalid email...")
        
        # Set a shorter timeout since we expect this to fail
        login_success = session.automated_google_login(timeout_minutes=2)
        
        print(f"   📊 Login result: {'✅ Success' if login_success else '❌ Failed (expected)'}")
        
        # Capture final state
        final_state = capture_moodle_sso_state(session.page, "moodle_sso_invalid_email_final")
        
        # Wait a bit to see the error state
        print("   ⏳ Waiting to capture error state...")
        time.sleep(3)
        
        # Capture error state
        error_state = capture_moodle_sso_state(session.page, "moodle_sso_invalid_email_error")
        
        # Analyze what we captured
        has_errors = (
            len(error_state.get("errors_found", [])) > 0 or 
            len(error_state.get("found_keywords", [])) > 0
        )
        
        print(f"   📊 Error detection: {'✅ Found errors' if has_errors else '❌ No errors detected'}")
        
        # Close session
        session.close()
        
        return has_errors
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False


def test_moodle_sso_wrong_password(moodle_url: str, test_email: str):
    """Test wrong password through Moodle SSO"""
    print(f"\n🧪 Testing Wrong Password through Moodle SSO")
    print(f"   🌐 Moodle URL: {moodle_url}")
    print(f"   📧 Using email: {test_email}")
    
    wrong_password = "definitely_wrong_password_123"
    
    try:
        # Create MoodleSession with wrong password
        session = MoodleSession(
            moodle_url=moodle_url,
            headless=False,
            google_email=test_email,
            google_password=wrong_password
        )
        
        # Start browser
        if not session.start_browser():
            print("   ❌ Failed to start browser")
            return False
        
        # Open Moodle login page
        if not session.open_login_page():
            print("   ❌ Failed to open Moodle login page")
            return False
        
        # Capture initial state
        initial_state = capture_moodle_sso_state(session.page, "moodle_sso_wrong_password_initial")
        
        # Try automated Google login
        print("   🔄 Attempting automated Google login with wrong password...")
        login_success = session.automated_google_login(timeout_minutes=2)
        
        print(f"   📊 Login result: {'✅ Success' if login_success else '❌ Failed (expected)'}")
        
        # Capture final state
        final_state = capture_moodle_sso_state(session.page, "moodle_sso_wrong_password_final")
        
        # Wait for error to appear
        time.sleep(3)
        
        # Capture error state
        error_state = capture_moodle_sso_state(session.page, "moodle_sso_wrong_password_error")
        
        # Analyze errors
        has_errors = (
            len(error_state.get("errors_found", [])) > 0 or 
            len(error_state.get("found_keywords", [])) > 0
        )
        
        print(f"   📊 Error detection: {'✅ Found errors' if has_errors else '❌ No errors detected'}")
        
        # Close session
        session.close()
        
        return has_errors
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Moodle SSO authentication errors")
    parser.add_argument("--moodle-url", default="https://tbl.umak.edu.ph", 
                       help="Moodle URL to test")
    parser.add_argument("--test-email", 
                       help="Valid email for wrong password test")
    
    args = parser.parse_args()
    
    print("🧪 Moodle SSO Gmail Authentication Error Testing")
    print("=" * 60)
    print(f"🌐 Testing Moodle URL: {args.moodle_url}")
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright is required but not installed.")
        return
    
    # Create output directories
    Path(__file__).parent.joinpath("moodle_sso_screenshots").mkdir(exist_ok=True)
    Path(__file__).parent.joinpath("moodle_sso_data").mkdir(exist_ok=True)
    
    # Test 1: Invalid email
    print("\n" + "=" * 40)
    invalid_email_success = test_moodle_sso_invalid_email(args.moodle_url)
    
    # Test 2: Wrong password (if email provided)
    wrong_password_success = False
    if args.test_email:
        print("\n" + "=" * 40)
        wrong_password_success = test_moodle_sso_wrong_password(args.moodle_url, args.test_email)
    else:
        print("\n⏭️  Skipping wrong password test - no test email provided")
        print("   Use --test-email your@gmail.com to test wrong password scenarios")
    
    # Results summary
    print("\n" + "=" * 60)
    print("📊 MOODLE SSO ERROR TESTING RESULTS")
    print("=" * 60)
    print(f"❗ Invalid email test: {'✅ DETECTED ERRORS' if invalid_email_success else '❌ NO ERRORS FOUND'}")
    print(f"🔒 Wrong password test: {'✅ DETECTED ERRORS' if wrong_password_success else '❌ NO ERRORS FOUND' if args.test_email else '⏭️ SKIPPED'}")
    
    print(f"\n📁 Screenshots: {Path(__file__).parent / 'moodle_sso_screenshots'}")
    print(f"📄 Data files: {Path(__file__).parent / 'moodle_sso_data'}")
    
    if invalid_email_success or wrong_password_success:
        print("\n✅ Error detection working! Check captured data for patterns.")
    else:
        print("\n⚠️  No errors detected. Check screenshots to see what's happening.")
        print("   The error detection patterns may need improvement.")
    
    print("\n💡 Next step: Run 'python enhance_error_detection.py' to analyze results")


if __name__ == "__main__":
    main()
