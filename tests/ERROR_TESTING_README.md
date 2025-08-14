# Gmail Authentication Error Testing Guide

This directory contains tools to test and improve Gmail authentication error detection in the Moodle scraper.

## Problem

The current Moodle scraper cannot reliably detect when Gmail authentication fails due to:
- Incorrect email addresses  
- Wrong passwords
- Account issues

This leads to the scraper hanging or failing silently instead of prompting for correct credentials.

## Solution

These test scripts help you:
1. **Capture error scenarios** - Test various authentication failures
2. **Analyze error patterns** - Extract DOM elements and error messages
3. **Improve detection** - Generate enhanced error detection patterns
4. **Validate improvements** - Test the enhanced error detection

## Quick Start

### 1. Run the Demo Script (Recommended)
```bash
python demo_error_testing.py
```

This interactive script guides you through all testing options.

### 2. Quick Error Test
```bash
python quick_gmail_error_test.py
```

Tests invalid email and wrong password scenarios. Creates screenshots and JSON data.

### 3. Comprehensive Testing
```bash
python test_gmail_auth_errors.py --moodle-url https://your-moodle.edu --test-email your@gmail.com
```

Comprehensive testing including Moodle SSO integration.

### 4. Analyze Results
```bash
python enhance_error_detection.py
```

Analyzes captured data and generates improved error detection patterns.

## Test Scripts Overview

### 📄 `demo_error_testing.py`
**Interactive demo script** - Start here!
- Guides you through all testing options
- Checks dependencies
- Shows current error patterns
- Provides easy access to all tools

### 📄 `quick_gmail_error_test.py`
**Quick focused testing**
- Tests invalid email scenarios
- Tests wrong password scenarios  
- Captures screenshots and DOM data
- Generates JSON files with error details
- Lightweight and fast

### 📄 `test_gmail_auth_errors.py`
**Comprehensive testing suite**
- Multiple invalid email addresses
- Multiple wrong password attempts
- Moodle SSO integration testing
- Detailed element capture
- Full page state analysis
- Generates comprehensive reports

### 📄 `enhance_error_detection.py`
**Pattern analysis and improvement**
- Analyzes captured error data
- Extracts new error patterns
- Generates enhanced detection code
- Creates improved `_detect_login_errors()` method
- Suggests DOM selectors to monitor

## Output Files

After running tests, you'll find:

### 📁 `error_screenshots/`
- Screenshots of error states
- Before/after submission images
- Visual reference for debugging

### 📁 `error_data/`
- JSON files with captured error details
- DOM element information
- Error text patterns
- Page state snapshots

### 📁 `auth_error_captures/` (comprehensive tests)
- Detailed capture data
- Multiple test scenarios
- Complete page analysis

## How to Use the Results

### 1. Review Captured Data
Look at the JSON files and screenshots to understand:
- What error messages actually appear
- Which DOM elements contain errors
- How error states differ from normal states

### 2. Update Error Detection
Copy the enhanced patterns from `enhance_error_detection.py` output into the `_detect_login_errors()` method in `moodle_direct_scraper.py`.

### 3. Test Your Changes
Re-run the tests to verify your improvements work correctly.

## Example Workflow

```bash
# 1. Start with the demo
python demo_error_testing.py

# 2. Run quick test to capture basic errors
python quick_gmail_error_test.py

# 3. Analyze the results  
python enhance_error_detection.py

# 4. Apply suggested improvements to moodle_direct_scraper.py

# 5. Test again to verify improvements
python quick_gmail_error_test.py --headless
```

## Dependencies

- **Playwright**: `pip install playwright && playwright install chromium`
- **Python 3.7+**
- **Internet connection** for testing Gmail

## Command Line Options

### `quick_gmail_error_test.py`
- `--headless` - Run browser in headless mode

### `test_gmail_auth_errors.py`  
- `--headless` - Run browser in headless mode
- `--timeout N` - Set timeout in minutes
- `--moodle-url URL` - Test Moodle SSO integration
- `--test-email EMAIL` - Email for wrong password tests

## Common Error Patterns to Look For

### Email Errors
- "Couldn't find your Google Account"
- "Enter a valid email" 
- "No account found"
- "Invalid email address"

### Password Errors
- "Wrong password"
- "Incorrect password"
- "Try again"
- "Sign-in error"

### DOM Selectors
- `[role="alert"]`
- `.Ekjuhf` (Google error class)
- `#identifierId_error`
- `#password_error`
- `[jsname="B34EJ"]`

## Troubleshooting

### Tests Not Detecting Errors
- Check if error patterns have changed
- Look at screenshots to see actual error messages
- Update patterns in `_detect_login_errors()`

### Browser Issues
- Install Playwright: `pip install playwright`
- Install browser: `playwright install chromium`
- Try non-headless mode first

### No Error Data Generated
- Check internet connection
- Verify Gmail is accessible
- Try different invalid email formats

## Integration with Main Scraper

After improving error detection:

1. **Update patterns** in `moodle_direct_scraper.py`
2. **Test with real credentials** 
3. **Verify prompting works** when errors occur
4. **Test retry logic** with corrected credentials

## Contributing

When you find new error patterns:
1. Add them to the test scripts
2. Update the pattern lists
3. Test with various scenarios
4. Document new patterns found

## Security Notes

- Never commit real credentials to git
- Use test accounts when possible
- Error testing may trigger account security measures
- Avoid excessive failed login attempts
