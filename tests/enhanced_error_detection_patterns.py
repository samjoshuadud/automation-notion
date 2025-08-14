#!/usr/bin/env python3
"""
Enhanced Error Detection Patterns

Based on real testing with Moodle SSO, this provides the improved
_detect_login_errors method for moodle_direct_scraper.py
"""

def enhanced_detect_login_errors(page) -> dict:
    """
    Enhanced error detection with patterns captured from real Moodle SSO testing
    
    This replaces the existing _detect_login_errors method in MoodleSession
    """
    try:
        page_text = page.content().lower()
        url = page.url.lower()

        error_info = {
            'has_error': False,
            'error_type': None,
            'error_message': '',
            'retry_allowed': False,
            'detected_selectors': []  # Track which selectors found errors
        }

        # ENHANCED: Add DOM element detection first (most reliable)
        # These selectors were captured from real Google SSO errors
        google_error_selectors = [
            '.Ekjuhf',                # Google error message class (confirmed working)
            '[jsname="B34EJ"]',       # Google error container (confirmed working)
            '#identifierId_error',    # Email field error
            '#password_error',        # Password field error  
            '.dEOOab',                # Alternative Google error text
            '[role="alert"]',         # Standard alert role
            '[data-error]',           # Elements with error data
        ]

        # Check DOM elements for visible errors first
        for selector in google_error_selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    if elem.is_visible():
                        error_text = elem.inner_text().strip()
                        if error_text and len(error_text) > 2:
                            error_info['detected_selectors'].append({
                                'selector': selector,
                                'text': error_text
                            })
                            
                            # Determine error type based on content
                            error_text_lower = error_text.lower()
                            
                            # Check for email-related errors
                            if any(pattern in error_text_lower for pattern in [
                                "couldn't find your google account",
                                "couldn't find", "no account", "invalid email", 
                                "account not found", "email doesn't exist"
                            ]):
                                error_info.update({
                                    'has_error': True,
                                    'error_type': 'email',
                                    'error_message': f"Email error (via {selector}): {error_text}",
                                    'retry_allowed': True
                                })
                                return error_info
                            
                            # Check for password-related errors  
                            elif any(pattern in error_text_lower for pattern in [
                                "wrong password", "incorrect password", "password",
                                "try again", "forgot password"
                            ]):
                                error_info.update({
                                    'has_error': True,
                                    'error_type': 'password',
                                    'error_message': f"Password error (via {selector}): {error_text}",
                                    'retry_allowed': True
                                })
                                return error_info
            except Exception:
                continue

        # ENHANCED: Improved email error patterns (based on real testing)
        email_error_patterns = [
            # Confirmed patterns from testing
            "couldn't find your google account",
            "couldn't find your account",
            
            # Existing patterns (keep these)
            "couldn't find an account",
            "email doesn't exist",
            "no account found",
            "enter a valid email",
            "wrong email",
            "invalid email address",
            
            # Additional variations
            "account not found",
            "google account not found",
            "this email address doesn't exist",
            "please check your email",
            "email not recognized"
        ]

        for pattern in email_error_patterns:
            if pattern in page_text:
                error_info.update({
                    'has_error': True,
                    'error_type': 'email',
                    'error_message': f"Email error detected: {pattern}",
                    'retry_allowed': True
                })
                return error_info

        # ENHANCED: Improved password error patterns (based on real testing)
        password_error_patterns = [
            # Confirmed patterns from testing
            "wrong password. try again",
            "wrong password",
            "try again",
            
            # Existing patterns (keep these)
            "incorrect password",
            "invalid password",
            "password is incorrect",
            "sign-in error",
            
            # Additional variations
            "password incorrect",
            "please try again",
            "authentication failed",
            "login failed",
            "forgot password to reset it"
        ]

        for pattern in password_error_patterns:
            if pattern in page_text:
                error_info.update({
                    'has_error': True,
                    'error_type': 'password',
                    'error_message': f"Password error detected: {pattern}",
                    'retry_allowed': True
                })
                return error_info

        # ENHANCED: Check for error indicators in URLs
        # Google shows errors in URL paths
        url_error_indicators = [
            '/signin/rejected',       # Google email rejection URL
            '/signin/challenge',      # Password challenge (not always error)
            'error=',                 # Error parameter
            'invalid',                # Invalid indicator
        ]
        
        for indicator in url_error_indicators:
            if indicator in url:
                if '/signin/rejected' in url:
                    error_info.update({
                        'has_error': True,
                        'error_type': 'email',
                        'error_message': f"Email rejected (URL indicator): {indicator}",
                        'retry_allowed': True
                    })
                    return error_info

        # Keep existing error patterns for other cases
        
        # Phone number errors (existing)
        phone_error_patterns = [
            "invalid phone number",
            "phone number is not valid",
            "enter a valid phone number",
            "this phone number cannot be used"
        ]

        for pattern in phone_error_patterns:
            if pattern in page_text:
                error_info.update({
                    'has_error': True,
                    'error_type': 'phone',
                    'error_message': f"Phone error detected: {pattern}",
                    'retry_allowed': True
                })
                return error_info

        # Account locked/suspended errors (existing)
        account_error_patterns = [
            "account has been disabled",
            "account is suspended", 
            "account has been locked",
            "too many failed attempts",
            "account temporarily unavailable"
        ]

        for pattern in account_error_patterns:
            if pattern in page_text:
                error_info.update({
                    'has_error': True,
                    'error_type': 'account_locked',
                    'error_message': f"Account error detected: {pattern}",
                    'retry_allowed': False
                })
                return error_info

        return error_info

    except Exception as e:
        # Enhanced error handling
        print(f"Error during login error detection: {e}")
        return {
            'has_error': False,
            'error_type': None,
            'error_message': '',
            'retry_allowed': False,
            'detection_error': str(e)
        }


# Test function to validate the enhanced detection
def test_enhanced_detection():
    """Test the enhanced error detection with captured data"""
    
    # Test data from real captures
    test_cases = [
        {
            "name": "Invalid email from Google SSO",
            "page_text": "Couldn't find your Google Account",
            "url": "https://accounts.google.com/v3/signin/identifier",
            "expected_type": "email"
        },
        {
            "name": "Wrong password from Google SSO", 
            "page_text": "Wrong password. Try again or click Forgot password to reset it.",
            "url": "https://accounts.google.com/v3/signin/challenge/pwd",
            "expected_type": "password"
        },
        {
            "name": "Email rejected URL",
            "page_text": "Sign in to Google",
            "url": "https://accounts.google.com/v3/signin/rejected?dsh=123",
            "expected_type": "email"
        }
    ]
    
    print("🧪 Testing Enhanced Error Detection Patterns")
    print("=" * 50)
    
    # Mock page object for testing
    class MockPage:
        def __init__(self, content, url):
            self._content = content
            self._url = url
            
        def content(self):
            return self._content
            
        @property
        def url(self):
            return self._url
            
        def query_selector_all(self, selector):
            return []  # No DOM elements in this simple test
    
    for test_case in test_cases:
        mock_page = MockPage(test_case["page_text"], test_case["url"])
        result = enhanced_detect_login_errors(mock_page)
        
        success = result['has_error'] and result['error_type'] == test_case["expected_type"]
        status = "✅" if success else "❌"
        
        print(f"{status} {test_case['name']}")
        print(f"   Expected: {test_case['expected_type']}")
        print(f"   Got: {result['error_type']} - {result['error_message']}")
        print()


if __name__ == "__main__":
    test_enhanced_detection()
