#!/usr/bin/env python3
"""
Manual SSO Error Capture

This script opens your Moodle SSO and lets you manually trigger 
authentication errors while it captures the DOM elements and error states.

This is more reliable than automation since Google blocks automated testing.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright not available")

from moodle_direct_scraper import MoodleSession


def capture_current_state(page, scenario_name: str):
    """Capture the current page state"""
    timestamp = datetime.now().strftime('%H%M%S')
    
    print(f"\n📸 Capturing: {scenario_name}")
    print(f"   🌐 URL: {page.url}")
    print(f"   📄 Title: {page.title()}")
    
    # Capture screenshots directory
    screenshot_dir = Path(__file__).parent / "manual_captures"
    screenshot_dir.mkdir(exist_ok=True)
    
    # Take screenshot
    screenshot_path = screenshot_dir / f"{scenario_name}_{timestamp}.png"
    page.screenshot(path=str(screenshot_path))
    print(f"   📸 Screenshot: {screenshot_path}")
    
    # Capture page data
    error_info = {
        "scenario": scenario_name,
        "url": page.url,
        "title": page.title(),
        "timestamp": datetime.now().isoformat(),
        "page_text": "",
        "error_elements": [],
        "form_elements": []
    }
    
    try:
        # Get page text
        error_info["page_text"] = page.evaluate("document.body.innerText")
        
        # Look for error elements
        error_selectors = [
            '[role="alert"]',
            '.alert', '.alert-error', '.alert-danger',
            '.error', '.warning', '.message',
            '#error-message', '.form-error', '.login-error',
            '[class*="error"]', '[class*="alert"]',
            '.Ekjuhf', '#identifierId_error', '#password_error',
            '[jsname="B34EJ"]', '.dEOOab'
        ]
        
        for selector in error_selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    if elem.is_visible():
                        text = elem.inner_text().strip()
                        if text and len(text) > 2:
                            error_info["error_elements"].append({
                                "selector": selector,
                                "text": text,
                                "html": elem.inner_html()[:300]
                            })
                            print(f"   ❗ Error element: {text[:50]}...")
            except:
                continue
        
        # Look for form elements
        form_selectors = [
            'input[type="email"]', 'input[type="password"]',
            'input[name="identifier"]', 'input[id="identifierId"]',
            'input[name="username"]', 'input[name="password"]'
        ]
        
        for selector in form_selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    if elem.is_visible():
                        error_info["form_elements"].append({
                            "selector": selector,
                            "placeholder": elem.get_attribute("placeholder") or "",
                            "type": elem.get_attribute("type") or "",
                            "enabled": elem.is_enabled()
                        })
            except:
                continue
                
    except Exception as e:
        print(f"   ⚠️  Error capturing data: {e}")
    
    # Save JSON data
    json_path = screenshot_dir / f"{scenario_name}_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(error_info, f, indent=2)
    print(f"   💾 Data: {json_path}")
    
    return error_info


def analyze_captured_text(text: str) -> dict:
    """Analyze captured text for error patterns"""
    text_lower = text.lower()
    
    # Current patterns from your scraper
    email_patterns = [
        "couldn't find your google account",
        "couldn't find an account", 
        "email doesn't exist",
        "no account found",
        "enter a valid email",
        "wrong email",
        "invalid email address",
        "couldn't find your account"
    ]
    
    password_patterns = [
        "wrong password",
        "incorrect password",
        "invalid password", 
        "password is incorrect",
        "try again",
        "sign-in error"
    ]
    
    found_patterns = {
        "email_errors": [],
        "password_errors": [],
        "other_errors": []
    }
    
    for pattern in email_patterns:
        if pattern in text_lower:
            found_patterns["email_errors"].append(pattern)
    
    for pattern in password_patterns:
        if pattern in text_lower:
            found_patterns["password_errors"].append(pattern)
    
    # Look for other potential error patterns
    other_error_words = [
        "error", "failed", "invalid", "incorrect", "denied", 
        "unable", "cannot", "forbidden", "unauthorized"
    ]
    
    sentences = text.split('.')
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        if any(word in sentence_lower for word in other_error_words):
            if len(sentence.strip()) > 10 and len(sentence.strip()) < 200:
                found_patterns["other_errors"].append(sentence.strip())
    
    return found_patterns


def main():
    print("🔍 Manual SSO Error Capture Tool")
    print("=" * 50)
    print("""
This tool will:
1. Open your Moodle SSO login
2. Let you manually test authentication errors
3. Capture error states and DOM elements
4. Help improve error detection patterns

You'll manually enter invalid emails/passwords while the tool captures data.
""")
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright required but not available")
        return
    
    moodle_url = "https://tbl.umak.edu.ph"
    
    # Create session
    session = MoodleSession(
        moodle_url=moodle_url,
        headless=False  # Keep visible for manual testing
    )
    
    try:
        # Start browser
        if not session.start_browser():
            print("❌ Failed to start browser")
            return
        
        print("✅ Browser started")
        
        # Open login page
        if not session.open_login_page():
            print("❌ Failed to open login page")
            return
        
        print("✅ Opened Moodle login page")
        
        # Capture initial state
        capture_current_state(session.page, "01_moodle_initial")
        
        print("\n" + "=" * 60)
        print("📋 MANUAL TESTING INSTRUCTIONS")
        print("=" * 60)
        print("""
Now you can manually test authentication errors:

1. INVALID EMAIL TEST:
   - Click on the Google SSO button in the browser
   - Enter an invalid email (like: fake.email.test@gmail.com)
   - Click Next
   - Wait for error to appear
   - Press ENTER here to capture the error state

2. WRONG PASSWORD TEST:
   - Enter a valid email
   - Click Next  
   - Enter a wrong password
   - Click Sign in
   - Wait for error to appear
   - Press ENTER here to capture the error state

3. When done, type 'done' to finish
""")
        
        step = 1
        while True:
            user_input = input(f"\n[Step {step}] Press ENTER to capture current state, or 'done' to finish: ").strip()
            
            if user_input.lower() == 'done':
                break
            
            # Capture current state
            state = capture_current_state(session.page, f"{step:02d}_manual_capture")
            
            # Analyze the captured text
            if state.get("page_text"):
                analysis = analyze_captured_text(state["page_text"])
                
                if analysis["email_errors"]:
                    print(f"   🔍 Found email error patterns: {analysis['email_errors']}")
                
                if analysis["password_errors"]:
                    print(f"   🔍 Found password error patterns: {analysis['password_errors']}")
                
                if analysis["other_errors"]:
                    print(f"   🔍 Found other potential errors:")
                    for error in analysis["other_errors"][:3]:  # Show first 3
                        print(f"     • {error}")
                
                if not any([analysis["email_errors"], analysis["password_errors"], analysis["other_errors"]]):
                    print("   ℹ️  No obvious error patterns detected in current state")
            
            step += 1
        
        print("\n✅ Manual capture completed!")
        
        # Analyze all captured data
        captures_dir = Path(__file__).parent / "manual_captures"
        json_files = list(captures_dir.glob("*.json"))
        
        print(f"\n📊 Analysis of {len(json_files)} captured states:")
        
        all_error_elements = []
        all_error_patterns = []
        
        for json_file in sorted(json_files):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                
                scenario = data.get("scenario", "unknown")
                error_elements = data.get("error_elements", [])
                
                if error_elements:
                    print(f"\n   📄 {scenario}:")
                    for elem in error_elements:
                        print(f"     🎯 {elem['selector']}: {elem['text'][:80]}...")
                        all_error_elements.append(elem)
                
                # Analyze text
                page_text = data.get("page_text", "")
                if page_text:
                    analysis = analyze_captured_text(page_text)
                    for category, patterns in analysis.items():
                        if patterns:
                            all_error_patterns.extend(patterns)
                            
            except Exception as e:
                print(f"   ❌ Failed to analyze {json_file}: {e}")
        
        # Generate suggestions
        print("\n" + "=" * 60)
        print("💡 SUGGESTIONS FOR IMPROVING ERROR DETECTION")
        print("=" * 60)
        
        if all_error_elements:
            unique_selectors = set(elem['selector'] for elem in all_error_elements)
            print(f"\n🎯 Working error selectors found ({len(unique_selectors)}):")
            for selector in sorted(unique_selectors):
                print(f"   • {selector}")
        
        if all_error_patterns:
            unique_patterns = set(all_error_patterns)
            print(f"\n📝 Error patterns detected ({len(unique_patterns)}):")
            for pattern in sorted(unique_patterns):
                print(f"   • {pattern}")
        
        print(f"\n📁 All capture data saved in: {captures_dir}")
        
    except KeyboardInterrupt:
        print("\n\n👋 Manual testing interrupted")
    
    except Exception as e:
        print(f"\n❌ Error during manual testing: {e}")
    
    finally:
        # Close session
        try:
            session.close()
        except:
            pass


if __name__ == "__main__":
    main()
