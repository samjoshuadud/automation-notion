#!/usr/bin/env python3
"""
Debug script to test 2FA detection with the actual HTML from selectors.html
"""

import logging
logging.basicConfig(level=logging.DEBUG)

def test_device_confirmation_detection():
    """Test device confirmation detection with the actual HTML"""
    
    # Sample HTML from selectors.html
    html_content = '''
    <h1 class="vAV9bf" data-a11y-title-piece="" id="headingText" jsname="r4nke"><span jsslot="">2-Step Verification</span></h1>

    <section class="Em2Ord  S7S4N" jscontroller="Tbb4sb" jsname="CjGfSd" jsshadow=""><header class="vYeFie" jsname="tJHJj"><div class="ozEFYb" role="presentation" jsname="NjaE2c"><h2 class="x9zgF TrZEUc"><span jsslot="" jsname="Ud7fr">Check your Galaxy Tab S9</span></h2><div class="osxBFb" jsname="HSrbLb" aria-hidden="true"></div></div></header><div class="yTaH4c" jsname="MZArnb"><div jsslot=""><div class="dMNVAe" jsname="NhJ5Dd">Google sent a notification to your Galaxy Tab S9. Tap <strong>Yes</strong> on the notification to verify it's you.<div class="dMNVAe">Or open the Gmail app on your iPhone to verify it's you from there.</div></div></div></div></section>

    <span jsname="V67aGc" class="VfPpkd-vQzf8d">Resend it</span>

    <span jsname="V67aGc" class="VfPpkd-vQzf8d">Try another way</span>
    '''
    
    page_text = html_content.lower()
    
    # Test text-based detection
    device_confirmation_phrases = [
        'check your', 'tap yes', 'confirm', 'approve', 
        'device notification', 'push notification', 'phone notification',
        'galaxy tab', 'ipad', 'tablet', 'android device', 'iphone',
        'your phone', 'your device', 'notification to verify',
        'gmail app', 'tap yes on your', 'google sent a notification'
    ]
    
    text_detected = any(phrase in page_text for phrase in device_confirmation_phrases)
    print(f"Text-based detection: {text_detected}")
    
    # Test specific patterns
    for phrase in device_confirmation_phrases:
        if phrase in page_text:
            print(f"  Found: '{phrase}'")
    
    # Test 2FA general detection
    tfa_patterns = [
        '2-step', 'two-step', '2fa', 'two-factor', 'verification', 
        'verify', 'code', 'authenticator', 'device', 'confirm'
    ]
    
    tfa_detected = any(phrase in page_text for phrase in tfa_patterns)
    print(f"General 2FA detection: {tfa_detected}")
    
    for phrase in tfa_patterns:
        if phrase in page_text:
            print(f"  Found: '{phrase}'")

if __name__ == "__main__":
    test_device_confirmation_detection()
