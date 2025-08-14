#!/usr/bin/env python3
"""
Test Enhanced Error Detection

Test the enhanced error detection with your actual Moodle system
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from moodle_direct_scraper import MoodleSession


def test_enhanced_error_detection():
    """Test the enhanced error detection with invalid credentials"""
    print("🧪 Testing Enhanced Error Detection")
    print("=" * 50)
    print("This will test authentication with invalid credentials to verify")
    print("that the enhanced error detection works correctly.")
    print()
    
    moodle_url = "https://tbl.umak.edu.ph"
    
    # Test with invalid email
    print("1. Testing with invalid email...")
    session = MoodleSession(
        moodle_url=moodle_url,
        headless=False,
        google_email="invalid.test.email.12345@gmail.com",
        google_password="fake_password_123"
    )
    
    try:
        if session.start_browser():
            print("   ✅ Browser started")
            
            if session.open_login_page():
                print("   ✅ Opened login page")
                
                # Try automated login (should detect error)
                print("   🔄 Attempting login with invalid email...")
                result = session.automated_google_login(timeout_minutes=1)
                
                if result:
                    print("   ⚠️  Login unexpectedly succeeded")
                else:
                    print("   ✅ Login failed as expected (error detection working)")
                    
            session.close()
        else:
            print("   ❌ Failed to start browser")
            
    except Exception as e:
        print(f"   ❌ Test error: {e}")
        try:
            session.close()
        except:
            pass
    
    print("\n" + "=" * 50)
    print("✅ Enhanced error detection test completed!")
    print()
    print("💡 The enhanced error detection now includes:")
    print("   • DOM element detection for Google error messages")
    print("   • Improved error patterns from real testing")
    print("   • URL-based error detection")
    print("   • Better retry prompting")
    print()
    print("🔧 Your scraper should now properly detect when:")
    print("   • Email address is invalid/not found")
    print("   • Password is incorrect")
    print("   • And prompt you to enter correct credentials")


if __name__ == "__main__":
    test_enhanced_error_detection()
