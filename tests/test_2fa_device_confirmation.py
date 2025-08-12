
#!/usr/bin/env python3
"""
Test script for debugging 2FA device confirmation detection
Run this when you encounter the 2FA device confirmation issue
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_debug_logging():
    """Enable comprehensive debug logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('tests/debug_2fa_detection.log')
        ]
    )

def test_device_confirmation_detection():
    """Test device confirmation detection with detailed debugging"""
    
    print("🔍 2FA Device Confirmation Detection Test")
    print("=" * 50)
    
    # Enable debug mode
    os.environ['MOODLE_SCRAPE_DEBUG'] = '1'
    setup_debug_logging()
    
    try:
        # Import here to avoid import issues if dependencies missing
        from moodle_direct_scraper import MoodleDirectScraper
        
        # Initialize scraper
        scraper = MoodleDirectScraper(headless=False)  # Use non-headless for debugging
        
        print("🌐 Starting browser session...")
        if not scraper.session.start_browser():
            print("❌ Failed to start browser")
            return False
        
        print("🔗 Opening Moodle login page...")
        if not scraper.session.open_login_page():
            print("❌ Failed to open login page")
            return False
        
        print("\n📱 MANUAL TEST INSTRUCTIONS:")
        print("1. Complete the login process in the browser")
        print("2. When you reach the 2FA device confirmation page:")
        print("   - DO NOT approve on your device yet")
        print("   - Come back to this terminal and press Enter")
        print("3. This will test the detection logic")
        
        input("\nPress Enter when you see the device confirmation page...")
        
        # Test the detection
        page = scraper.session.page
        if not page:
            print("❌ Browser page not available")
            return False
        
        print("\n🔍 Testing device confirmation detection...")
        
        # Get current page info
        current_url = page.url
        page_title = page.title()
        page_text = page.content().lower()
        
        print(f"📄 Current URL: {current_url}")
        print(f"📄 Page Title: {page_title}")
        print(f"📄 Page Text Length: {len(page_text)} characters")
        
        # Test our detection method
        detected = scraper.session._detect_and_handle_2fa(page)
        
        print(f"\n🎯 Detection Result: {'✅ DETECTED' if detected else '❌ NOT DETECTED'}")
        
        if detected:
            print("✅ Device confirmation was properly detected!")
            print("📱 You can now approve the sign-in on your device")
        else:
            print("❌ Device confirmation was NOT detected")
            print("🔍 Debug information has been saved to help troubleshoot")
            
            # Save additional debug info
            debug_dir = Path('data/moodle_session/2fa_debug')
            debug_dir.mkdir(exist_ok=True, parents=True)
            
            # Extract key phrases for analysis
            key_phrases = [
                'check your', 'tap yes', 'notification', 'approve', 'device',
                'google sent', 'verify', '2-step', 'confirm it\'s you',
                'we sent a notification', 'sent a notification to',
                'approve this sign-in', 'confirm your identity'
            ]
            
            print("\n🔍 Page Content Analysis:")
            found_phrases = []
            for phrase in key_phrases:
                if phrase in page_text:
                    found_phrases.append(phrase)
                    print(f"  ✅ Found: '{phrase}'")
                else:
                    print(f"  ❌ Missing: '{phrase}'")
            
            # Check for specific elements
            print("\n🔍 Element Detection Test:")
            element_selectors = [
                'h1:has-text("2-Step Verification")',
                'h2:has-text("Check your")',
                'span:has-text("Check your")',
                'div:has-text("Google sent a notification")',
                'div:has-text("We sent a notification")',
                'span:has-text("Tap Yes")',
                'div:has-text("approve this sign-in")'
            ]
            
            found_elements = []
            for selector in element_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=1000):
                        found_elements.append(selector)
                        print(f"  ✅ Element found: {selector}")
                    else:
                        print(f"  ❌ Element not visible: {selector}")
                except Exception as e:
                    print(f"  ❌ Element error: {selector} - {e}")
            
            if found_phrases:
                print(f"\n📝 Found {len(found_phrases)} device confirmation phrases")
                print("This suggests the page IS a device confirmation page")
                print("The detection logic may need adjustment")
            elif found_elements:
                print(f"\n📝 Found {len(found_elements)} device confirmation elements")
                print("This suggests the page IS a device confirmation page")
                print("The detection logic may need adjustment")
            else:
                print("\n📝 No device confirmation phrases or elements found")
                print("This may not be a device confirmation page")
                
            # Save raw page content for manual inspection
            debug_file = debug_dir / f"manual_test_{int(time.time())}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page.content())
            print(f"\n💾 Page content saved to: {debug_file}")
        
        # Wait for completion if detected
        if detected:
            print("\n⏳ Waiting for login completion...")
            start_time = time.time()
            while time.time() - start_time < 300:  # 5 minute timeout
                if scraper.session._check_login_status():
                    print("✅ Login completed successfully!")
                    break
                time.sleep(2)
            else:
                print("⏰ Timeout waiting for login completion")
        
        return detected
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you have playwright or selenium installed")
        print("💡 Run: pip install playwright selenium")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            if 'scraper' in locals():
                scraper.close()
        except:
            pass

def quick_2fa_test():
    """Quick test to check if 2FA detection components are working"""
    print("🧪 Quick 2FA Detection Component Test")
    print("=" * 40)
    
    try:
        from moodle_direct_scraper import MoodleSession
        
        # Test basic session creation
        session = MoodleSession()
        print("✅ MoodleSession created successfully")
        
        # Test if browser can start
        if session.start_browser():
            print("✅ Browser started successfully")
            session.close()
        else:
            print("❌ Browser failed to start")
            return False
            
        print("✅ All components working")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

if __name__ == "__main__":
    print("2FA Device Confirmation Test Suite")
    print("=" * 50)
    
    # Run quick test first
    if not quick_2fa_test():
        print("\n❌ Quick component test failed")
        print("💡 Fix component issues before running full test")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    choice = input("Run full 2FA detection test? (y/N): ").strip().lower()
    if choice in ['y', 'yes']:
        success = test_device_confirmation_detection()
        
        print("\n" + "=" * 50)
        if success:
            print("✅ Test completed - Device confirmation was detected")
        else:
            print("❌ Test completed - Device confirmation was NOT detected")
            print("📋 Check the debug logs and saved HTML files for troubleshooting")
            print("📁 Debug files location: data/moodle_session/2fa_debug/")
        
        print("\n💡 Tips for troubleshooting:")
        print("1. Check tests/debug_2fa_detection.log for detailed logs")
        print("2. Review saved HTML files in data/moodle_session/2fa_debug/")
        print("3. Look for new text patterns in the actual Google 2FA page")
        print("4. Run with MOODLE_SCRAPE_DEBUG=1 for maximum detail")
    else:
        print("👋 Test cancelled")
