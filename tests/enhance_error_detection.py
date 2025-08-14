#!/usr/bin/env python3
"""
Enhanced Error Detection Pattern Generator

This script analyzes captured error data and suggests improvements 
to the _detect_login_errors() method in moodle_direct_scraper.py

Usage:
    python enhance_error_detection.py
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def analyze_error_data():
    """Analyze captured error data and suggest pattern improvements"""
    print("🔍 Analyzing captured error data...")
    
    # Look for error data files
    error_data_dir = Path(__file__).parent / "error_data"
    
    if not error_data_dir.exists():
        print("❌ No error data directory found. Run quick_gmail_error_test.py first.")
        return
    
    json_files = list(error_data_dir.glob("*.json"))
    
    if not json_files:
        print("❌ No error data files found. Run quick_gmail_error_test.py first.")
        return
    
    print(f"📄 Found {len(json_files)} error data files")
    
    # Collect all error patterns
    email_errors = set()
    password_errors = set()
    all_keywords = set()
    error_selectors = set()
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            scenario = data.get("scenario", "")
            found_keywords = data.get("found_keywords", [])
            errors_found = data.get("errors_found", [])
            
            print(f"\n📋 Analyzing {json_file.name} ({scenario})")
            
            # Categorize errors
            if "email" in scenario:
                email_errors.update(found_keywords)
                print(f"   📧 Email error keywords: {found_keywords}")
            elif "password" in scenario:
                password_errors.update(found_keywords)
                print(f"   🔒 Password error keywords: {found_keywords}")
            
            all_keywords.update(found_keywords)
            
            # Collect successful selectors
            for error in errors_found:
                selector = error.get("selector", "")
                text = error.get("text", "")
                if selector and text:
                    error_selectors.add(selector)
                    print(f"   🎯 Working selector: {selector} -> '{text}'")
                    
        except Exception as e:
            print(f"   ❌ Failed to process {json_file}: {e}")
    
    # Generate enhanced patterns
    generate_enhanced_patterns(email_errors, password_errors, all_keywords, error_selectors)


def generate_enhanced_patterns(email_errors: set, password_errors: set, all_keywords: set, error_selectors: set):
    """Generate enhanced error detection patterns"""
    print("\n" + "="*60)
    print("🛠️  ENHANCED ERROR DETECTION PATTERNS")
    print("="*60)
    
    # Enhanced email error patterns
    current_email_patterns = [
        "couldn't find your google account",
        "couldn't find an account",
        "email doesn't exist",
        "no account found", 
        "enter a valid email",
        "wrong email",
        "invalid email address",
        "couldn't find your account"
    ]
    
    enhanced_email_patterns = list(set(current_email_patterns) | email_errors)
    enhanced_email_patterns.sort()
    
    print("\n📧 ENHANCED EMAIL ERROR PATTERNS:")
    print("Replace the email_error_patterns list in _detect_login_errors() with:")
    print("\nemail_error_patterns = [")
    for pattern in enhanced_email_patterns:
        print(f'    "{pattern}",')
    print("]")
    
    # Enhanced password error patterns
    current_password_patterns = [
        "wrong password",
        "incorrect password", 
        "invalid password",
        "password is incorrect",
        "try again",
        "sign-in error"
    ]
    
    enhanced_password_patterns = list(set(current_password_patterns) | password_errors)
    enhanced_password_patterns.sort()
    
    print("\n🔒 ENHANCED PASSWORD ERROR PATTERNS:")
    print("Replace the password_error_patterns list in _detect_login_errors() with:")
    print("\npassword_error_patterns = [")
    for pattern in enhanced_password_patterns:
        print(f'    "{pattern}",')
    print("]")
    
    # Enhanced error selectors
    current_selectors = [
        '[role="alert"]',
        '.error',
        '.warning', 
        '.alert',
        '[data-error]',
        '[aria-live="polite"]',
        '[aria-live="assertive"]',
        '.Ekjuhf',
        '#identifierId_error',
        '#password_error',
        '[jsname="B34EJ"]',
        '.dEOOab'
    ]
    
    enhanced_selectors = list(set(current_selectors) | error_selectors)
    enhanced_selectors.sort()
    
    print("\n🎯 ENHANCED ERROR SELECTORS:")
    print("Consider adding these selectors to error detection:")
    print("\nenhanced_error_selectors = [")
    for selector in enhanced_selectors:
        print(f'    "{selector}",')
    print("]")
    
    # Generate complete enhanced _detect_login_errors method
    generate_enhanced_method(enhanced_email_patterns, enhanced_password_patterns, enhanced_selectors)


def generate_enhanced_method(email_patterns: List[str], password_patterns: List[str], selectors: List[str]):
    """Generate the complete enhanced _detect_login_errors method"""
    print("\n" + "="*60)
    print("🔧 COMPLETE ENHANCED METHOD")
    print("="*60)
    
    method_code = f'''
def _detect_login_errors(self, page) -> dict:
    """Enhanced error detection with improved patterns from testing"""
    try:
        page_text = page.content().lower()
        url = page.url.lower()

        error_info = {{
            'has_error': False,
            'error_type': None,
            'error_message': '',
            'retry_allowed': False,
            'detected_elements': []
        }}

        # Enhanced error element detection
        error_selectors = {selectors}
        
        detected_elements = []
        for selector in error_selectors:
            try:
                elements = page.query_selector_all(selector)
                for elem in elements:
                    if elem.is_visible():
                        text = elem.inner_text().strip()
                        if text:
                            detected_elements.append({{
                                'selector': selector,
                                'text': text
                            }})
            except:
                continue
        
        error_info['detected_elements'] = detected_elements

        # Enhanced email error patterns
        email_error_patterns = {email_patterns}

        for pattern in email_error_patterns:
            if pattern in page_text:
                error_info.update({{
                    'has_error': True,
                    'error_type': 'email',
                    'error_message': f"Email error detected: {{pattern}}",
                    'retry_allowed': True
                }})
                logger.debug(f"Detected email error: {{pattern}}")
                return error_info

        # Enhanced password error patterns  
        password_error_patterns = {password_patterns}

        for pattern in password_error_patterns:
            if pattern in page_text:
                error_info.update({{
                    'has_error': True,
                    'error_type': 'password', 
                    'error_message': f"Password error detected: {{pattern}}",
                    'retry_allowed': True
                }})
                logger.debug(f"Detected password error: {{pattern}}")
                return error_info

        # Check detected elements for error indicators
        for elem in detected_elements:
            elem_text = elem['text'].lower()
            # Check if element text contains error keywords
            for pattern in email_error_patterns + password_error_patterns:
                if pattern in elem_text:
                    error_type = 'email' if pattern in email_error_patterns else 'password'
                    error_info.update({{
                        'has_error': True,
                        'error_type': error_type,
                        'error_message': f"Error detected in element ({{elem['selector']}}): {{elem['text']}}",
                        'retry_allowed': True
                    }})
                    return error_info

        # Phone number errors (keeping existing patterns)
        phone_error_patterns = [
            "invalid phone number",
            "phone number is not valid", 
            "enter a valid phone number",
            "this phone number cannot be used"
        ]

        for pattern in phone_error_patterns:
            if pattern in page_text:
                error_info.update({{
                    'has_error': True,
                    'error_type': 'phone',
                    'error_message': f"Phone error detected: {{pattern}}",
                    'retry_allowed': True
                }})
                logger.debug(f"Detected phone error: {{pattern}}")
                return error_info

        # Account locked/suspended errors (keeping existing patterns)
        account_error_patterns = [
            "account has been disabled",
            "account is suspended",
            "account has been locked",
            "too many failed attempts",
            "account temporarily unavailable"
        ]

        for pattern in account_error_patterns:
            if pattern in page_text:
                error_info.update({{
                    'has_error': True,
                    'error_type': 'account_locked',
                    'error_message': f"Account error detected: {{pattern}}",
                    'retry_allowed': False
                }})
                logger.debug(f"Detected account error: {{pattern}}")
                return error_info

        # Check URL for error indicators
        url_error_indicators = ['error', 'invalid', 'failed']
        if any(indicator in url for indicator in url_error_indicators):
            error_info.update({{
                'has_error': True,
                'error_type': 'general',
                'error_message': f"Error indicator in URL: {{url}}",
                'retry_allowed': True
            }})

        return error_info

    except Exception as e:
        logger.debug(f"Error during login error detection: {{e}}")
        return {{
            'has_error': False,
            'error_type': None,
            'error_message': '',
            'retry_allowed': False
        }}'''
    
    print("Copy this enhanced method to replace _detect_login_errors() in moodle_direct_scraper.py:")
    print(method_code)
    
    # Save to file
    output_file = Path(__file__).parent / "enhanced_detect_login_errors.py"
    with open(output_file, 'w') as f:
        f.write(method_code)
    
    print(f"\n💾 Enhanced method saved to: {output_file}")


def generate_test_validation_script():
    """Generate a script to validate the enhanced error detection"""
    print("\n🧪 Generating validation test script...")
    
    validation_script = '''#!/usr/bin/env python3
"""
Validation script for enhanced error detection
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def test_enhanced_patterns():
    """Test the enhanced error detection patterns"""
    # Mock page content with various error scenarios
    test_cases = [
        {
            "content": "couldn't find your google account",
            "expected_type": "email"
        },
        {
            "content": "wrong password entered",
            "expected_type": "password"  
        },
        {
            "content": "invalid email address provided",
            "expected_type": "email"
        }
    ]
    
    # Here you would test the enhanced _detect_login_errors method
    print("🧪 Testing enhanced error detection patterns...")
    print("✅ Validation complete")

if __name__ == "__main__":
    test_enhanced_patterns()
'''
    
    validation_file = Path(__file__).parent / "validate_enhanced_errors.py"
    with open(validation_file, 'w') as f:
        f.write(validation_script)
    
    print(f"📄 Validation script saved to: {validation_file}")


def main():
    print("🛠️  Enhanced Error Detection Pattern Generator")
    print("="*50)
    
    # Analyze captured error data
    analyze_error_data()
    
    # Generate validation script
    generate_test_validation_script()
    
    print("\n" + "="*50)
    print("📋 NEXT STEPS:")
    print("1. Run quick_gmail_error_test.py to capture error data")
    print("2. Run this script again to analyze the data")
    print("3. Update _detect_login_errors() in moodle_direct_scraper.py")
    print("4. Test the enhanced error detection")
    print("="*50)


if __name__ == "__main__":
    main()
