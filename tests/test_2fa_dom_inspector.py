#!/usr/bin/env python3
"""
2FA DOM Inspector - Inspect and save HTML/screenshots for different 2FA scenarios
This helps debug detection issues by examining the actual DOM structure
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from moodle_direct_scraper import MoodleSession
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/2fa_dom_inspection.log')
    ]
)
logger = logging.getLogger(__name__)

class TwoFADOMInspector:
    def __init__(self):
        self.session = MoodleSession(
            moodle_url=os.getenv('MOODLE_URL', 'https://tbl.umak.edu.ph'),
            headless=False,  # We want to see the browser
            google_email=os.getenv('GOOGLE_EMAIL'),
            google_password=os.getenv('GOOGLE_PASSWORD')
        )
        
        # Create output directory
        self.output_dir = Path('data/2fa_dom_captures')
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def save_dom_snapshot(self, page, scenario_name: str, description: str = ""):
        """Save HTML, screenshot, and analysis for current page"""
        try:
            timestamp = int(time.time())
            base_name = f"{scenario_name}_{timestamp}"
            
            # Save HTML
            html_file = self.output_dir / f"{base_name}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page.content())
            
            # Save screenshot
            screenshot_file = self.output_dir / f"{base_name}.png"
            page.screenshot(path=str(screenshot_file))
            
            # Save page analysis
            analysis_file = self.output_dir / f"{base_name}_analysis.txt"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(f"2FA DOM Analysis - {scenario_name}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Description: {description}\n")
                f.write(f"URL: {page.url}\n")
                f.write(f"Title: {page.title()}\n")
                f.write("="*60 + "\n\n")
                
                # Extract key information
                page_text = page.content().lower()
                
                # Check for key phrases
                key_phrases = [
                    "2-step verification", "check your device", "choose how you want to sign in",
                    "try another way", "tap yes", "notification", "sms", "text message",
                    "authenticator", "backup code", "verification code", "google sent",
                    "approve this sign-in", "confirm it's you"
                ]
                
                f.write("Key phrases found:\n")
                for phrase in key_phrases:
                    if phrase in page_text:
                        f.write(f"  ✓ {phrase}\n")
                    else:
                        f.write(f"  ✗ {phrase}\n")
                
                f.write("\n" + "="*60 + "\n\n")
                
                # Check for key elements
                key_selectors = [
                    'h1', 'h2', 'h3',
                    'div[data-challengetype]',
                    'div[data-challenge-ui]',
                    '[data-action]',
                    'span[jsname]',
                    'button', 'input[type="submit"]',
                    '.l5PPKe',  # Common Google text element
                    '[role="link"]'
                ]
                
                f.write("Elements found:\n")
                for selector in key_selectors:
                    try:
                        elements = page.locator(selector).all()
                        if elements:
                            f.write(f"  {selector}: {len(elements)} found\n")
                            for i, element in enumerate(elements[:5]):  # Show first 5
                                try:
                                    text = element.text_content()[:100] if element.text_content() else ""
                                    attrs = element.get_attribute('class') or ""
                                    data_attrs = []
                                    for attr in ['data-challengetype', 'data-challenge-ui', 'data-action', 'jsname']:
                                        val = element.get_attribute(attr)
                                        if val:
                                            data_attrs.append(f"{attr}='{val}'")
                                    f.write(f"    [{i+1}] Text: {text}\n")
                                    if attrs:
                                        f.write(f"    [{i+1}] Class: {attrs}\n")
                                    if data_attrs:
                                        f.write(f"    [{i+1}] Data: {', '.join(data_attrs)}\n")
                                    f.write("\n")
                                except Exception as e:
                                    f.write(f"    [{i+1}] Error reading element: {e}\n")
                        else:
                            f.write(f"  {selector}: None found\n")
                    except Exception as e:
                        f.write(f"  {selector}: Error - {e}\n")
                        
                f.write("\n" + "="*60 + "\n\n")
                f.write("Full page text (first 1000 chars):\n")
                f.write(page.locator('body').text_content()[:1000] if page.locator('body').count() > 0 else "No body content")
                f.write("\n\n" + "="*60 + "\n")
                f.write("Raw HTML structure (first 2000 chars):\n")
                f.write(page.content()[:2000])
            
            print(f"✅ Saved DOM snapshot: {base_name}")
            logger.info(f"DOM snapshot saved: {html_file}, {screenshot_file}, {analysis_file}")
            
        except Exception as e:
            print(f"❌ Error saving DOM snapshot: {e}")
            logger.error(f"Error saving DOM snapshot for {scenario_name}: {e}")
    
    def interactive_inspection(self):
        """Interactive mode where user navigates and we capture different scenarios"""
        if not self.session.start_browser():
            print("❌ Failed to start browser")
            return False
            
        page = self.session.page
        print(f"\n🔍 2FA DOM Inspector Started")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🌐 Browser opened - navigate to your 2FA scenarios")
        print("\nCommands:")
        print("  1. Type 'method' - Capture method selection page")
        print("  2. Type 'device' - Capture device confirmation page") 
        print("  3. Type 'sms' - Capture SMS code entry page")
        print("  4. Type 'current' - Capture current page (generic)")
        print("  5. Type 'help' - Show this help")
        print("  6. Type 'quit' - Exit inspector")
        print("="*60)
        
        # Navigate to login page first
        login_url = f"{self.session.moodle_url.rstrip('/')}/login/index.php"
        print(f"\n🔗 Navigating to: {login_url}")
        page.goto(login_url)
        
        while True:
            try:
                command = input(f"\n📍 Current URL: {page.url}\n💬 Enter command: ").strip().lower()
                
                if command == 'quit':
                    print("👋 Exiting DOM inspector")
                    break
                elif command == 'help':
                    print("\nCommands:")
                    print("  method - Capture method selection page")
                    print("  device - Capture device confirmation page") 
                    print("  sms - Capture SMS code entry page")
                    print("  current - Capture current page")
                    print("  quit - Exit")
                elif command == 'method':
                    print("📄 Capturing method selection page...")
                    self.save_dom_snapshot(page, "method_selection", "Choose verification method page")
                elif command == 'device':
                    print("📱 Capturing device confirmation page...")
                    self.save_dom_snapshot(page, "device_confirmation", "Device confirmation/notification page")
                elif command == 'sms':
                    print("📲 Capturing SMS code entry page...")
                    self.save_dom_snapshot(page, "sms_entry", "SMS verification code entry page")
                elif command == 'current':
                    print("📸 Capturing current page...")
                    scenario_name = input("Enter scenario name (or press Enter for 'generic'): ").strip() or "generic"
                    description = input("Enter description (optional): ").strip()
                    self.save_dom_snapshot(page, scenario_name, description)
                else:
                    print(f"❓ Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n\n⏸️ Interrupted - exiting DOM inspector")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"Error in interactive mode: {e}")
        
        self.session.close()
        return True
    
    def automated_inspection(self):
        """Automated mode - try to trigger different 2FA scenarios automatically"""
        print(f"\n🤖 Starting automated 2FA DOM inspection")
        
        if not self.session.start_browser():
            print("❌ Failed to start browser")
            return False
            
        page = self.session.page
        
        try:
            # Step 1: Navigate to login page
            login_url = f"{self.session.moodle_url.rstrip('/')}/login/index.php"
            print(f"🔗 Navigating to login page: {login_url}")
            page.goto(login_url)
            time.sleep(2)
            self.save_dom_snapshot(page, "01_login_page", "Initial Moodle login page")
            
            # Step 2: Try to trigger Google SSO
            print("🔍 Looking for Google SSO button...")
            if self.session._attempt_auto_sso_login():
                print("✅ Clicked Google SSO button")
                time.sleep(3)
                self.save_dom_snapshot(page, "02_google_redirect", "After clicking Google SSO")
            else:
                print("⚠️ No Google SSO button found")
            
            # Step 3: Try automated login if credentials provided
            if self.session.google_email and self.session.google_password:
                print("🔐 Attempting automated Google login...")
                # This will trigger 2FA scenarios
                result = self.session.automated_google_login(timeout_minutes=1)
                print(f"Login result: {result}")
            else:
                print("ℹ️ No Google credentials provided - manual navigation required")
                print("📋 Please manually navigate through the 2FA flow")
                print("🔄 Press Enter after each 2FA page to capture it...")
                
                scenarios = [
                    ("method_selection", "Navigate to method selection and press Enter"),
                    ("device_confirmation", "Navigate to device confirmation and press Enter"),
                    ("sms_entry", "Navigate to SMS entry and press Enter")
                ]
                
                for scenario, instruction in scenarios:
                    input(f"\n{instruction}: ")
                    self.save_dom_snapshot(page, scenario, instruction)
            
        except Exception as e:
            print(f"❌ Error during automated inspection: {e}")
            logger.error(f"Automated inspection error: {e}")
        
        print(f"\n✅ Automated inspection completed")
        print(f"📁 Check output directory: {self.output_dir}")
        
        self.session.close()
        return True

def main():
    print("🔍 2FA DOM Inspector")
    print("This tool helps debug 2FA detection by capturing DOM snapshots")
    print("="*60)
    
    mode = input("Choose mode:\n  1. Interactive (i) - Manual navigation\n  2. Automated (a) - Try auto-login\nEnter choice (i/a): ").strip().lower()
    
    inspector = TwoFADOMInspector()
    
    if mode in ['i', 'interactive', '1']:
        inspector.interactive_inspection()
    elif mode in ['a', 'automated', '2']:
        inspector.automated_inspection()
    else:
        print("❌ Invalid choice. Using interactive mode.")
        inspector.interactive_inspection()

if __name__ == "__main__":
    main()
