#!/usr/bin/env python3
"""
Gmail Authentication Error Testing Script

This script tests various Gmail authentication failure scenarios to capture 
DOM elements and improve error detection patterns. It helps identify:
1. Invalid/incorrect email error messages and UI elements
2. Wrong password error messages and UI elements  
3. Account lockout scenarios
4. Network/timeout issues

Usage:
    python test_gmail_auth_errors.py [--headless] [--timeout 10]
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add parent directory to path to import moodle_direct_scraper
sys.path.append(str(Path(__file__).parent.parent))

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright not available. Please install: pip install playwright")

from moodle_direct_scraper import MoodleSession

class GmailAuthErrorTester:
    """Test Gmail authentication errors and capture DOM elements for analysis"""
    
    def __init__(self, headless: bool = False, timeout: int = 10):
        self.headless = headless
        self.timeout = timeout
        self.test_results = []
        self.captured_elements = {}
        
        # Create output directory for captured data
        self.output_dir = Path(__file__).parent / "auth_error_captures"
        self.output_dir.mkdir(exist_ok=True)
        
        # Timestamp for this test session
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log_result(self, test_name: str, success: bool, details: str = "", elements: dict = None):
        """Log test result with captured elements"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "captured_elements": elements or {}
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
        if elements:
            print(f"   📋 Captured {len(elements)} element groups")
    
    def capture_page_state(self, page, scenario_name: str) -> dict:
        """Capture comprehensive page state for analysis"""
        try:
            captured = {
                "url": page.url,
                "title": page.title(),
                "timestamp": datetime.now().isoformat(),
                "scenario": scenario_name
            }
            
            # Capture page content
            captured["page_content"] = page.content()
            
            # Capture error elements
            error_selectors = [
                '[role="alert"]',
                '.error',
                '.warning',
                '.alert',
                '[data-error]',
                '[aria-live="polite"]',
                '[aria-live="assertive"]',
                '.Ekjuhf',  # Google specific error class
                '#identifierId_error',  # Google email error
                '#password_error',  # Google password error
                '[jsname="B34EJ"]',  # Google error container
                '.dEOOab',  # Google error text
            ]
            
            captured["error_elements"] = {}
            for selector in error_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        captured["error_elements"][selector] = []
                        for elem in elements:
                            elem_info = {
                                "text": elem.inner_text().strip(),
                                "html": elem.inner_html(),
                                "visible": elem.is_visible(),
                                "attributes": {}
                            }
                            # Get key attributes
                            for attr in ["class", "id", "role", "aria-label", "data-error"]:
                                try:
                                    value = elem.get_attribute(attr)
                                    if value:
                                        elem_info["attributes"][attr] = value
                                except:
                                    pass
                            captured["error_elements"][selector].append(elem_info)
                except Exception as e:
                    print(f"   Warning: Failed to capture {selector}: {e}")
            
            # Capture form elements
            form_selectors = [
                'input[type="email"]',
                'input[type="password"]',
                'input[name="identifier"]',
                'input[id="identifierId"]',
                '#Email', '#email',
                '#password', '#Password'
            ]
            
            captured["form_elements"] = {}
            for selector in form_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        captured["form_elements"][selector] = []
                        for elem in elements:
                            elem_info = {
                                "visible": elem.is_visible(),
                                "enabled": elem.is_enabled(),
                                "value": elem.input_value() if hasattr(elem, 'input_value') else "",
                                "placeholder": elem.get_attribute("placeholder") or "",
                                "attributes": {}
                            }
                            # Get key attributes
                            for attr in ["class", "id", "name", "type", "autocomplete"]:
                                try:
                                    value = elem.get_attribute(attr)
                                    if value:
                                        elem_info["attributes"][attr] = value
                                except:
                                    pass
                            captured["form_elements"][selector].append(elem_info)
                except Exception as e:
                    print(f"   Warning: Failed to capture {selector}: {e}")
            
            # Capture button elements
            button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                '#identifierNext',
                '#passwordNext',
                'button:has-text("Next")',
                'button:has-text("Sign in")',
                '[role="button"]'
            ]
            
            captured["button_elements"] = {}
            for selector in button_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        captured["button_elements"][selector] = []
                        for elem in elements:
                            elem_info = {
                                "text": elem.inner_text().strip(),
                                "visible": elem.is_visible(),
                                "enabled": elem.is_enabled(),
                                "attributes": {}
                            }
                            # Get key attributes
                            for attr in ["class", "id", "type", "role", "disabled"]:
                                try:
                                    value = elem.get_attribute(attr)
                                    if value:
                                        elem_info["attributes"][attr] = value
                                except:
                                    pass
                            captured["button_elements"][selector].append(elem_info)
                except Exception as e:
                    print(f"   Warning: Failed to capture {selector}: {e}")
            
            # Save screenshot
            screenshot_path = self.output_dir / f"{scenario_name}_{self.session_timestamp}.png"
            page.screenshot(path=str(screenshot_path))
            captured["screenshot_path"] = str(screenshot_path)
            
            return captured
            
        except Exception as e:
            print(f"   ❌ Failed to capture page state: {e}")
            return {"error": str(e), "scenario": scenario_name}
    
    def save_captured_data(self, data: dict, filename: str):
        """Save captured data to JSON file"""
        try:
            filepath = self.output_dir / f"{filename}_{self.session_timestamp}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"   💾 Saved captured data to: {filepath}")
        except Exception as e:
            print(f"   ❌ Failed to save data: {e}")
    
    def test_invalid_email_scenarios(self, page) -> List[dict]:
        """Test various invalid email scenarios"""
        print("\n🧪 Testing Invalid Email Scenarios")
        
        invalid_emails = [
            "nonexistent@gmail.com",
            "invalid.email.that.does.not.exist@gmail.com", 
            "fakeemail123456789@gmail.com",
            "notreal@gmail.com",
            "doesnotexist@googlemail.com",
            "invalid@invalid.invalid"
        ]
        
        results = []
        
        for email in invalid_emails:
            print(f"\n  🔍 Testing email: {email}")
            
            try:
                # Navigate to Google accounts
                page.goto("https://accounts.google.com/signin", wait_until='domcontentloaded')
                time.sleep(2)
                
                # Find and fill email field
                email_selectors = [
                    'input[type="email"]',
                    'input[name="identifier"]', 
                    'input[id="identifierId"]',
                    '#Email', '#email'
                ]
                
                email_input = None
                for selector in email_selectors:
                    try:
                        email_input = page.wait_for_selector(selector, timeout=5000)
                        if email_input and email_input.is_visible():
                            break
                    except:
                        continue
                
                if not email_input:
                    results.append({
                        "email": email,
                        "success": False,
                        "error": "Could not find email input field"
                    })
                    continue
                
                # Clear and enter email
                email_input.fill("")
                time.sleep(0.5)
                email_input.type(email)
                time.sleep(1)
                
                # Capture state after email entry
                pre_submit_state = self.capture_page_state(page, f"invalid_email_pre_submit_{email.split('@')[0]}")
                
                # Click Next/Continue
                next_selectors = [
                    '#identifierNext',
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Next")'
                ]
                
                next_clicked = False
                for selector in next_selectors:
                    try:
                        next_button = page.query_selector(selector)
                        if next_button and next_button.is_visible():
                            next_button.click()
                            next_clicked = True
                            break
                    except:
                        continue
                
                if not next_clicked:
                    # Try Enter key
                    email_input.press("Enter")
                
                # Wait for error to appear
                time.sleep(3)
                
                # Capture state after submission
                post_submit_state = self.capture_page_state(page, f"invalid_email_post_submit_{email.split('@')[0]}")
                
                # Look for error indicators
                error_found = False
                error_text = ""
                
                # Check for error text in page
                page_text = page.content().lower()
                error_patterns = [
                    "couldn't find your google account",
                    "couldn't find an account", 
                    "email doesn't exist",
                    "no account found",
                    "enter a valid email",
                    "wrong email",
                    "invalid email address",
                    "couldn't find your account"
                ]
                
                for pattern in error_patterns:
                    if pattern in page_text:
                        error_found = True
                        error_text = pattern
                        break
                
                result = {
                    "email": email,
                    "success": True,
                    "error_detected": error_found,
                    "error_text": error_text,
                    "pre_submit_state": pre_submit_state,
                    "post_submit_state": post_submit_state
                }
                
                results.append(result)
                
                # Save detailed capture
                self.save_captured_data(result, f"invalid_email_{email.split('@')[0]}")
                
                status = "🔴" if error_found else "🟡"
                print(f"    {status} Error detected: {error_found}")
                if error_text:
                    print(f"    📝 Error text: {error_text}")
                    
            except Exception as e:
                results.append({
                    "email": email,
                    "success": False,
                    "error": str(e)
                })
                print(f"    ❌ Test failed: {e}")
        
        return results
    
    def test_wrong_password_scenarios(self, page, valid_email: str) -> List[dict]:
        """Test wrong password scenarios with a valid email"""
        print(f"\n🧪 Testing Wrong Password Scenarios with email: {valid_email}")
        
        wrong_passwords = [
            "wrongpassword123",
            "incorrect_password",
            "notmypassword",
            "fakepwd123",
            "wrong123456"
        ]
        
        results = []
        
        for password in wrong_passwords:
            print(f"\n  🔍 Testing password: {'*' * len(password)}")
            
            try:
                # Navigate to Google accounts
                page.goto("https://accounts.google.com/signin", wait_until='domcontentloaded')
                time.sleep(2)
                
                # Enter email first
                email_input = None
                email_selectors = [
                    'input[type="email"]',
                    'input[name="identifier"]',
                    'input[id="identifierId"]',
                    '#Email', '#email'
                ]
                
                for selector in email_selectors:
                    try:
                        email_input = page.wait_for_selector(selector, timeout=5000)
                        if email_input and email_input.is_visible():
                            break
                    except:
                        continue
                
                if email_input:
                    email_input.fill("")
                    time.sleep(0.5)
                    email_input.type(valid_email)
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
                    time.sleep(3)
                    
                    password_input = None
                    password_selectors = [
                        'input[type="password"]',
                        'input[name="password"]',
                        '#password', '#Password'
                    ]
                    
                    for selector in password_selectors:
                        try:
                            password_input = page.wait_for_selector(selector, timeout=5000)
                            if password_input and password_input.is_visible():
                                break
                        except:
                            continue
                    
                    if password_input:
                        # Capture state before password entry
                        pre_password_state = self.capture_page_state(page, f"wrong_password_pre_entry_{len(password)}")
                        
                        # Enter wrong password
                        password_input.fill("")
                        time.sleep(0.5)
                        password_input.type(password)
                        time.sleep(1)
                        
                        # Click Sign in
                        signin_selectors = [
                            '#passwordNext',
                            'button[type="submit"]',
                            'input[type="submit"]',
                            'button:has-text("Sign in")'
                        ]
                        
                        signin_clicked = False
                        for selector in signin_selectors:
                            try:
                                signin_button = page.query_selector(selector)
                                if signin_button and signin_button.is_visible():
                                    signin_button.click()
                                    signin_clicked = True
                                    break
                            except:
                                continue
                        
                        if not signin_clicked:
                            password_input.press("Enter")
                        
                        # Wait for error
                        time.sleep(3)
                        
                        # Capture state after password submission
                        post_password_state = self.capture_page_state(page, f"wrong_password_post_submit_{len(password)}")
                        
                        # Check for password errors
                        error_found = False
                        error_text = ""
                        
                        page_text = page.content().lower()
                        password_error_patterns = [
                            "wrong password",
                            "incorrect password",
                            "invalid password", 
                            "password is incorrect",
                            "try again",
                            "sign-in error"
                        ]
                        
                        for pattern in password_error_patterns:
                            if pattern in page_text:
                                error_found = True
                                error_text = pattern
                                break
                        
                        result = {
                            "email": valid_email,
                            "password_length": len(password),
                            "success": True,
                            "error_detected": error_found,
                            "error_text": error_text,
                            "pre_password_state": pre_password_state,
                            "post_password_state": post_password_state
                        }
                        
                        results.append(result)
                        
                        # Save detailed capture
                        self.save_captured_data(result, f"wrong_password_{len(password)}chars")
                        
                        status = "🔴" if error_found else "🟡"
                        print(f"    {status} Password error detected: {error_found}")
                        if error_text:
                            print(f"    📝 Error text: {error_text}")
                    else:
                        results.append({
                            "email": valid_email,
                            "password_length": len(password),
                            "success": False,
                            "error": "Could not find password input field"
                        })
                else:
                    results.append({
                        "email": valid_email, 
                        "password_length": len(password),
                        "success": False,
                        "error": "Could not find email input field"
                    })
                    
            except Exception as e:
                results.append({
                    "email": valid_email,
                    "password_length": len(password),
                    "success": False,
                    "error": str(e)
                })
                print(f"    ❌ Test failed: {e}")
        
        return results
    
    def test_moodle_integration_errors(self, moodle_url: str) -> dict:
        """Test authentication errors through Moodle SSO flow"""
        print(f"\n🧪 Testing Moodle Integration Errors with URL: {moodle_url}")
        
        try:
            # Create MoodleSession with invalid credentials
            session = MoodleSession(
                moodle_url=moodle_url,
                headless=self.headless,
                google_email="invalid.test.email@gmail.com",
                google_password="wrongpassword123"
            )
            
            # Start browser
            if not session.start_browser():
                return {"success": False, "error": "Failed to start browser"}
            
            # Open login page
            if not session.open_login_page():
                return {"success": False, "error": "Failed to open login page"}
            
            # Capture initial state
            initial_state = self.capture_page_state(session.page, "moodle_initial_login")
            
            # Attempt automated login with invalid credentials
            print("  🔍 Attempting automated login with invalid credentials...")
            login_result = session.automated_google_login(timeout_minutes=2)
            
            # Capture final state
            final_state = self.capture_page_state(session.page, "moodle_final_error")
            
            result = {
                "success": True,
                "login_successful": login_result,
                "initial_state": initial_state,
                "final_state": final_state,
                "moodle_url": moodle_url
            }
            
            # Save detailed capture
            self.save_captured_data(result, "moodle_integration_error_test")
            
            # Close session
            session.close()
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_comprehensive_test(self, moodle_url: str = None, test_email: str = None):
        """Run all authentication error tests"""
        print("🚀 Starting Comprehensive Gmail Authentication Error Testing")
        print(f"   📁 Output directory: {self.output_dir}")
        print(f"   🕒 Session timestamp: {self.session_timestamp}")
        print(f"   👁️  Headless mode: {self.headless}")
        
        if not PLAYWRIGHT_AVAILABLE:
            print("❌ Cannot run tests - Playwright not available")
            return
        
        all_results = {
            "session_info": {
                "timestamp": self.session_timestamp,
                "headless": self.headless,
                "timeout": self.timeout
            },
            "tests": {}
        }
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            try:
                # Test 1: Invalid Email Scenarios
                print("\n" + "="*60)
                invalid_email_results = self.test_invalid_email_scenarios(page)
                all_results["tests"]["invalid_emails"] = invalid_email_results
                self.log_result(
                    "Invalid Email Tests", 
                    len(invalid_email_results) > 0,
                    f"Tested {len(invalid_email_results)} invalid emails"
                )
                
                # Test 2: Wrong Password Scenarios (if test email provided)
                if test_email:
                    print("\n" + "="*60)
                    wrong_password_results = self.test_wrong_password_scenarios(page, test_email)
                    all_results["tests"]["wrong_passwords"] = wrong_password_results
                    self.log_result(
                        "Wrong Password Tests",
                        len(wrong_password_results) > 0,
                        f"Tested {len(wrong_password_results)} wrong passwords with {test_email}"
                    )
                else:
                    print("\n⚠️  Skipping wrong password tests - no test email provided")
                
            finally:
                browser.close()
        
        # Test 3: Moodle Integration Errors (if URL provided)
        if moodle_url:
            print("\n" + "="*60)
            moodle_result = self.test_moodle_integration_errors(moodle_url)
            all_results["tests"]["moodle_integration"] = moodle_result
            self.log_result(
                "Moodle Integration Test",
                moodle_result.get("success", False),
                f"Tested SSO flow with {moodle_url}"
            )
        else:
            print("\n⚠️  Skipping Moodle integration tests - no Moodle URL provided")
        
        # Save comprehensive results
        self.save_captured_data(all_results, "comprehensive_test_results")
        
        # Generate summary report
        self.generate_summary_report(all_results)
    
    def generate_summary_report(self, results: dict):
        """Generate a human-readable summary report"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY REPORT")
        print("="*80)
        
        timestamp = results["session_info"]["timestamp"]
        print(f"🕒 Test Session: {timestamp}")
        print(f"📁 Output Directory: {self.output_dir}")
        
        for test_type, test_results in results["tests"].items():
            print(f"\n📋 {test_type.upper().replace('_', ' ')} RESULTS:")
            
            if test_type == "invalid_emails":
                total_tests = len(test_results)
                successful_tests = sum(1 for r in test_results if r.get("success", False))
                error_detected = sum(1 for r in test_results if r.get("error_detected", False))
                
                print(f"   📊 Total tests: {total_tests}")
                print(f"   ✅ Successful tests: {successful_tests}")
                print(f"   🔴 Errors detected: {error_detected}")
                print(f"   📈 Error detection rate: {error_detected/total_tests*100:.1f}%")
                
                print("   📧 Tested emails:")
                for result in test_results:
                    status = "🔴" if result.get("error_detected") else "🟡"
                    print(f"     {status} {result.get('email', 'Unknown')}")
            
            elif test_type == "wrong_passwords":
                total_tests = len(test_results)
                successful_tests = sum(1 for r in test_results if r.get("success", False))
                error_detected = sum(1 for r in test_results if r.get("error_detected", False))
                
                print(f"   📊 Total tests: {total_tests}")
                print(f"   ✅ Successful tests: {successful_tests}")
                print(f"   🔴 Errors detected: {error_detected}")
                print(f"   📈 Error detection rate: {error_detected/total_tests*100:.1f}%")
            
            elif test_type == "moodle_integration":
                success = test_results.get("success", False)
                login_successful = test_results.get("login_successful", False)
                print(f"   📊 Test executed: {'✅' if success else '❌'}")
                print(f"   🔐 Login successful: {'❌' if not login_successful else '✅'}")
        
        print(f"\n💾 All captured data saved to: {self.output_dir}")
        print("🔍 Use the captured JSON files and screenshots to analyze error patterns")
        print("🛠️  Update the _detect_login_errors() method based on findings")


def main():
    parser = argparse.ArgumentParser(description="Test Gmail authentication error scenarios")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in minutes")
    parser.add_argument("--moodle-url", type=str, help="Moodle URL to test SSO integration")
    parser.add_argument("--test-email", type=str, help="Valid email for wrong password tests")
    
    args = parser.parse_args()
    
    print("🧪 Gmail Authentication Error Testing Script")
    print("=" * 50)
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright is required but not installed.")
        print("Please install with: pip install playwright")
        print("Then run: playwright install chromium")
        sys.exit(1)
    
    # Initialize tester
    tester = GmailAuthErrorTester(
        headless=args.headless,
        timeout=args.timeout
    )
    
    # Run comprehensive tests
    tester.run_comprehensive_test(
        moodle_url=args.moodle_url,
        test_email=args.test_email
    )
    
    print("\n🎉 Testing completed!")
    print(f"📁 Check {tester.output_dir} for detailed results")


if __name__ == "__main__":
    main()
