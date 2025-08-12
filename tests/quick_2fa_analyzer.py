#!/usr/bin/env python3
"""
Quick 2FA Analyzer - Simple tool to analyze current 2FA page
"""

import os
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from moodle_direct_scraper import MoodleSession

def analyze_current_page():
    print("🔍 Quick 2FA Page Analyzer")
    print("="*50)
    
    session = MoodleSession(
        moodle_url=os.getenv('MOODLE_URL', 'https://tbl.umak.edu.ph'),
        headless=False
    )
    
    if not session.start_browser():
        print("❌ Failed to start browser")
        return
        
    page = session.page
    
    # Navigate to login
    login_url = f"{session.moodle_url.rstrip('/')}/login/index.php"
    print(f"🔗 Navigating to: {login_url}")
    page.goto(login_url)
    
    print("\n📋 Navigate to any 2FA page, then press Enter to analyze...")
    
    while True:
        try:
            input("Press Enter to analyze current page (Ctrl+C to exit): ")
            
            # Get basic info
            url = page.url
            title = page.title()
            
            print(f"\n📍 **CURRENT PAGE ANALYSIS**")
            print(f"🔗 URL: {url}")
            print(f"📄 Title: {title}")
            
            # URL-based detection
            print(f"\n🔍 **URL PATTERNS:**")
            if 'challenge/selection' in url:
                print("✅ METHOD SELECTION PAGE (challenge/selection)")
            elif 'challenge/ipp' in url or 'challenge/totp' in url:
                print("✅ SMS/CODE ENTRY PAGE (challenge/ipp or challenge/totp)")
            elif 'challenge/az' in url:
                print("✅ DEVICE CONFIRMATION PAGE (challenge/az)")
            else:
                print("❓ UNKNOWN 2FA PAGE TYPE")
            
            # Text content analysis
            try:
                page_text = page.locator('body').text_content().lower()
                
                print(f"\n🔍 **TEXT PATTERNS:**")
                key_phrases = {
                    "Method Selection": ["choose how you want to sign in", "try another way", "more ways to verify"],
                    "Device Confirmation": ["check your device", "tap yes", "notification", "approve this sign-in"],
                    "SMS Entry": ["enter the code", "verification code", "code sent to", "text message"],
                    "General 2FA": ["2-step verification", "verify", "security"]
                }
                
                for category, phrases in key_phrases.items():
                    found = [p for p in phrases if p in page_text]
                    if found:
                        print(f"✅ {category}: {found}")
                    else:
                        print(f"❌ {category}: None found")
            except Exception as e:
                print(f"❌ Error reading page text: {e}")
            
            # Element analysis
            print(f"\n🔍 **KEY ELEMENTS:**")
            
            # Check for challengetype attributes
            try:
                challenge_elements = page.locator('[data-challengetype]').all()
                if challenge_elements:
                    print("✅ Challenge types found:")
                    for elem in challenge_elements:
                        challenge_type = elem.get_attribute('data-challengetype')
                        text = elem.text_content()[:50] if elem.text_content() else ""
                        print(f"   - Type {challenge_type}: {text}")
                else:
                    print("❌ No [data-challengetype] elements found")
            except Exception as e:
                print(f"❌ Error checking challenge types: {e}")
            
            # Check for common button/input elements
            try:
                buttons = page.locator('button, input[type="submit"], [role="button"]').all()
                print(f"🔘 Buttons/inputs found: {len(buttons)}")
                for i, btn in enumerate(buttons[:3]):  # Show first 3
                    text = btn.text_content()[:30] if btn.text_content() else ""
                    print(f"   [{i+1}] {text}")
            except Exception as e:
                print(f"❌ Error checking buttons: {e}")
            
            print("="*50)
            
        except KeyboardInterrupt:
            print("\n👋 Exiting analyzer")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    session.close()

if __name__ == "__main__":
    analyze_current_page()
