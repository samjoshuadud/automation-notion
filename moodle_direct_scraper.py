"""
Moodle Direct Scraper - Human-like browser automation for Moodle scraping
"""

import os
import sys
import logging
import time
import pickle
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import threading
from dotenv import load_dotenv
import re
import json
import random
try:
    from bs4 import BeautifulSoup  # optional for robust parsing
    BS4_AVAILABLE = True
except ImportError:  # noqa
    BS4_AVAILABLE = False

# Try to import playwright first, fall back to selenium
try:
    from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)

class MoodleSession:
    """Handles Moodle login sessions and cookie management with human-like behavior"""
    
    def __init__(self, moodle_url: str = None, headless: bool = False, google_email: str = None, google_password: str = None):
        load_dotenv()
        self.moodle_url = moodle_url or os.getenv('MOODLE_URL', 'https://your-moodle-site.com')
        self.headless = headless
        self.google_email = google_email
        self.google_password = google_password
        base_dir = Path(__file__).resolve().parent  # absolute base to avoid CWD issues
        self.session_dir = (base_dir / 'data' / 'moodle_session')
        self.session_dir.mkdir(exist_ok=True, parents=True)
        
        self.cookies_file = self.session_dir / 'cookies.pkl'
        self.user_data_dir = self.session_dir / 'browser_data'
        
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.driver = None  # For selenium fallback
        
        # Human-like behavior settings
        self.typing_delay = (50, 150)
        self.click_delay = (100, 300)
        self.page_load_wait = (2, 5)
        
        # Internal flags
        self._last_login_debug: dict = {}
        self.on_login_callback = None  # callback to trigger once when login confirmed
        self._login_announced = False
        # Flag to remember if we've detected a device confirmation flow
        self._device_confirmation_active = False
        # Flag to prevent showing UI multiple times
        self._device_ui_shown = False

    
    def _random_delay(self, min_ms: int, max_ms: int):
        """Add random human-like delay"""
        import random
        delay = random.randint(min_ms, max_ms) / 1000.0
        time.sleep(delay)
    
    def _init_playwright_browser(self) -> bool:
        """Initialize Playwright browser with human-like settings and persistent profile"""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        try:
            # Reuse existing playwright instance if already started
            if not hasattr(self, 'playwright'):
                self.playwright = sync_playwright().start()
            
            # Persistent context keeps session (including Google SSO) in user_data_dir
            if not self.context:
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    headless=self.headless,
                    viewport={'width': 1366, 'height': 768},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    accept_downloads=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-first-run',
                        '--disable-extensions-except',
                        '--disable-plugins-discovery',
                        '--no-sandbox',
                        '--disable-infobars',
                        '--window-size=1366,768'
                    ]
                )
            
            # Reuse first existing page if present (to keep loaded session state)
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
            
            # Set realistic properties once per context
            if not getattr(self, '_stealth_injected', False):
                self.page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                    Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
                """)
                self._stealth_injected = True
            
            logger.info("✅ Playwright browser initialized (persistent context)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            return False
    
    def _init_selenium_browser(self) -> bool:
        """Initialize Selenium browser as fallback"""
        if not SELENIUM_AVAILABLE:
            return False
        
        try:
            options = ChromeOptions()
            options.add_argument(f'--user-data-dir={self.user_data_dir}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            if self.headless:
                options.add_argument('--headless=new')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Selenium browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            return False
    
    def start_browser(self) -> bool:
        """Start browser session with user interaction capability"""
        if self._init_playwright_browser():
            logger.info("🌐 Using Playwright for browser automation")
            return True
        elif self._init_selenium_browser():
            logger.info("🌐 Using Selenium for browser automation")
            return True
        else:
            logger.error("❌ No web automation framework available. Please install playwright or selenium.")
            return False

    # ---------------------- Login Detection Helpers ---------------------- #
    def _moodle_cookie_names(self) -> List[str]:
        # Accept any cookie containing MoodleSession (some sites append hashes) + session test cookies
        return ["MoodleSession", "MoodleSessionTest"]
    
    def _get_moodle_cookies(self) -> List[Dict]:
        try:
            if self.page:
                cookies = self.context.cookies()
                moodle_cookies = [c for c in cookies if any(name in c['name'] for name in self._moodle_cookie_names())]
                logger.debug(f"Cookie check: total={len(cookies)} moodle={len(moodle_cookies)} names={[c['name'] for c in moodle_cookies]}")
                return moodle_cookies
            elif self.driver:
                cookies = self.driver.get_cookies()
                moodle_cookies = [c for c in cookies if any(name in c['name'] for name in self._moodle_cookie_names())]
                logger.debug(f"Cookie check (selenium): total={len(cookies)} moodle={len(moodle_cookies)} names={[c['name'] for c in moodle_cookies]}")
                return moodle_cookies
        except Exception as e:
            logger.debug(f"Cookie retrieval error: {e}")
        return []
    
    def _root_domain(self) -> str:
        try:
            host = self.moodle_url.split('//',1)[1].split('/',1)[0]
            return host
        except:
            return ''

    def _dom_login_indicators(self) -> List[str]:
        # Extended list for different Moodle themes
        return [
            '.usermenu',
            '#user-menu-toggle',
            'a[href*="logout" i]',
            'a[href*="logoff" i]',
            '.block_myoverview',
            'nav[aria-label="User menu"]',
            'div[data-region="drawer"]',
        ]
    
    def _dom_login_page_indicators(self) -> List[str]:
        return [
            '#login',
            'form[action*="login"]',
            'input[name="username"]',
            'input[name="password"]',
            'button[id*="login"]',
            'button[type="submit"][name="login"]'
        ]

    def _is_login_form_present(self) -> bool:
        if self.page:
            for sel in self._dom_login_page_indicators():
                try:
                    if self.page.query_selector(sel):
                        return True
                except:  # noqa
                    continue
        elif self.driver:
            for by, value in [
                (By.ID, 'login'),
                (By.NAME, 'username'),
                (By.NAME, 'password')
            ]:
                try:
                    if self.driver.find_elements(by, value):
                        return True
                except:  # noqa
                    continue
        return False

    def _is_logged_in_dom(self) -> bool:
        # Fast body class heuristic first (Moodle adds userloggedin class)
        try:
            if self.page:
                body_class = self.page.eval_on_selector('body', 'el => el.className') or ''
                if 'userloggedin' in body_class.split():
                    logger.debug("Body class indicates logged in")
                    return True
        except Exception:
            pass
        # Fallback to selectors
        if self.page:
            for sel in self._dom_login_indicators():
                try:
                    if self.page.query_selector(sel):
                        return True
                except:  # noqa
                    continue
        elif self.driver:
            for by, value in [
                (By.ID, 'user-menu-toggle'),
                (By.CLASS_NAME, 'usermenu'),
                (By.PARTIAL_LINK_TEXT, 'logout'),
            ]:
                try:
                    if self.driver.find_elements(by, value):
                        return True
                except:  # noqa
                    continue
        return False

    def open_login_page(self) -> bool:
        """Open Moodle login page for user interaction (only if not already logged in)"""
        try:
            # If already logged in skip navigation
            if self._check_login_status(skip_navigation=True):
                logger.info("🔐 Already logged in, skipping login page navigation")
                return True
            login_url = f"{self.moodle_url.rstrip('/')}/login/index.php"
            
            if self.page:  # Playwright
                logger.info(f"🔗 Opening Moodle login page: {login_url}")
                self.page.goto(login_url, wait_until='domcontentloaded')
                self._random_delay(500, 1200)
                return True
            elif self.driver:  # Selenium
                logger.info(f"🔗 Opening Moodle login page: {login_url}")
                self.driver.get(login_url)
                time.sleep(2)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to open login page: {e}")
            return False

    def automated_google_login(self, timeout_minutes: int = 10) -> bool:
        """Automated Google login with 2FA detection"""
        if not self.google_email or not self.google_password:
            logger.info("No Google credentials provided, falling back to manual login")
            return self.wait_for_user_login(timeout_minutes)
        
        # CRITICAL: Double-check login status before proceeding with automation
        if self._check_login_status(skip_navigation=True):
            logger.info("✅ Already logged in, skipping automated Google login")
            return True
        
        logger.info(f"🤖 Starting automated Google login for {self.google_email}")
        
        try:
            page = self.page
            if not page:
                logger.error("Browser page not available")
                return False
            
            # First, check if we're on Moodle login page and need to click Google SSO button
            current_url = page.url.lower()
            logger.debug(f"Current URL at start of automated login: {current_url}")
            
            # Only try to click SSO if we're on Moodle, not if we're already on Google
            if ('accounts.google.com' not in current_url and 
                (('login' in current_url and ('moodle' in current_url or 'tbl.umak.edu.ph' in current_url)) or
                 'tbl.umak.edu.ph' in current_url)):
                
                logger.info("🔍 Detected Moodle login page, looking for Google SSO button...")
                
                # Try to click Google SSO button first
                if self._attempt_auto_sso_login():
                    logger.info("✅ Clicked Google SSO button, waiting for redirect...")
                    # Wait for redirect to Google
                    time.sleep(3)
                    
                    # Wait for Google login page to load
                    try:
                        page.wait_for_url("**/accounts.google.com/**", timeout=10000)
                        logger.info("🔗 Successfully redirected to Google login")
                    except:
                        logger.info("⏳ Waiting for Google login page...")
                        time.sleep(2)
                else:
                    logger.warning("❌ Could not find or click Google SSO button on Moodle page")
                    logger.info("🔄 Falling back to manual login...")
                    return self.wait_for_user_login(timeout_minutes)
            elif 'accounts.google.com' in current_url:
                logger.info("✅ Already on Google accounts page, skipping SSO button click")
            else:
                logger.info("🔍 Not on expected Moodle login page, proceeding with Google login flow")
            
            # Now wait for Google login form to appear
            logger.info("🔍 Looking for Google email input field...")
            time.sleep(2)
            
            # First check if we're actually on Google login page
            current_url = page.url.lower()
            logger.debug(f"Current URL after SSO redirect: {current_url}")
            
            if 'accounts.google.com' not in current_url:
                logger.warning("⚠️ Not on Google accounts page, waiting for redirect...")
                try:
                    page.wait_for_url("**/accounts.google.com/**", timeout=15000)
                    logger.info("✅ Successfully reached Google accounts page")
                except Exception as e:
                    logger.warning(f"Failed to reach Google accounts page: {e}")
                    return self.wait_for_user_login(timeout_minutes)
            
            # Try to find email input field with enhanced detection
            email_selectors = [
                'input[type="email"]',
                'input[name="identifier"]', 
                'input[id="identifierId"]',
                '#Email', '#email',
                'input[placeholder*="email" i]',
                'input[autocomplete="username"]',
                'input[aria-label*="email" i]'
            ]
            
            email_input = None
            logger.info("🔍 Searching for email input field...")
            
            # Try each selector with detailed logging
            for i, selector in enumerate(email_selectors, 1):
                try:
                    logger.debug(f"Trying email selector {i}/{len(email_selectors)}: {selector}")
                    email_input = page.wait_for_selector(selector, timeout=3000)
                    if email_input and email_input.is_visible():
                        logger.info(f"✅ Found visible email input field: {selector}")
                        break
                    elif email_input:
                        logger.debug(f"Found email input but not visible: {selector}")
                        email_input = None
                except Exception as e:
                    logger.debug(f"Email selector {selector} failed: {e}")
                    continue
            
            # If still no input found, try waiting longer and check page content
            if not email_input:
                logger.warning("❌ Initial email input search failed, trying extended search...")
                page_content = page.content()
                
                # Check if we're on the right page
                if 'sign in' not in page_content.lower() and 'email' not in page_content.lower():
                    logger.error("❌ Page doesn't appear to be Google login page")
                    logger.debug(f"Page URL: {page.url}")
                    logger.debug(f"Page title: {page.title()}")
                    return self.wait_for_user_login(timeout_minutes)
                
                # Try waiting longer
                for selector in email_selectors[:3]:  # Try top 3 selectors with longer wait
                    try:
                        logger.debug(f"Extended wait for email selector: {selector}")
                        email_input = page.wait_for_selector(selector, timeout=10000)
                        if email_input and email_input.is_visible():
                            logger.info(f"✅ Found email input with extended wait: {selector}")
                            break
                    except:
                        continue
            
            if not email_input:
                logger.error("❌ Could not find Google email input field after extended search")
                logger.info("🔄 Falling back to manual login...")
                return self.wait_for_user_login(timeout_minutes)
            
            # Clear any existing text and enter email
            logger.info("📧 Entering email address")
            try:
                # Clear field first
                email_input.fill("")
                time.sleep(0.5)
                # Type email character by character for better reliability
                email_input.type(self.google_email)
                logger.info(f"✅ Successfully entered email: {self.google_email}")
            except Exception as e:
                logger.error(f"Failed to enter email: {e}")
                return self.wait_for_user_login(timeout_minutes)
            
            min_delay, max_delay = self.typing_delay
            time.sleep(random.uniform(min_delay/1000, max_delay/1000))
            
            # Click Next/Continue button
            next_selectors = [
                '#identifierNext',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Next")',
                'button:has-text("Continue")',
                '[data-test-id="next-button"]',
                'button[id*="next"]',
                'input[value*="Next"]'
            ]
            
            next_button = None
            logger.info("🔍 Looking for Next button...")
            for i, selector in enumerate(next_selectors, 1):
                try:
                    logger.debug(f"Trying Next button selector {i}/{len(next_selectors)}: {selector}")
                    next_button = page.wait_for_selector(selector, timeout=2000)
                    if next_button and next_button.is_visible():
                        logger.info(f"✅ Found Next button: {selector}")
                        break
                except:
                    continue
            
            if next_button:
                logger.info("👆 Clicking Next button")
                try:
                    next_button.click()
                    logger.info("✅ Successfully clicked Next button")
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"Failed to click Next button: {e}")
                    return self.wait_for_user_login(timeout_minutes)
            else:
                logger.warning("⚠️ Could not find Next button, trying to submit form with Enter key")
                try:
                    email_input.press("Enter")
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"Failed to submit email form: {e}")
                    return self.wait_for_user_login(timeout_minutes)
            
            # Wait for password field
            logger.info("🔍 Looking for password input field...")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                '#password', '#Password',
                'input[placeholder*="password" i]',
                'input[aria-label*="password" i]',
                'input[autocomplete="current-password"]'
            ]
            
            password_input = None
            # Try each password selector with detailed logging
            for i, selector in enumerate(password_selectors, 1):
                try:
                    logger.debug(f"Trying password selector {i}/{len(password_selectors)}: {selector}")
                    password_input = page.wait_for_selector(selector, timeout=3000)
                    if password_input and password_input.is_visible():
                        logger.info(f"✅ Found visible password input field: {selector}")
                        break
                    elif password_input:
                        logger.debug(f"Found password input but not visible: {selector}")
                        password_input = None
                except Exception as e:
                    logger.debug(f"Password selector {selector} failed: {e}")
                    continue
            
            # Extended search if no password field found
            if not password_input:
                logger.warning("❌ Initial password search failed, trying extended search...")
                
                # Check if we're on the right page
                current_url = page.url.lower()
                page_content = page.content()
                
                if 'password' not in page_content.lower():
                    logger.warning("Page doesn't contain password field yet, may need to wait...")
                    # Sometimes there's a delay before password field appears
                    time.sleep(2)
                
                # Try with longer timeout
                for selector in password_selectors[:3]:
                    try:
                        logger.debug(f"Extended wait for password selector: {selector}")
                        password_input = page.wait_for_selector(selector, timeout=10000)
                        if password_input and password_input.is_visible():
                            logger.info(f"✅ Found password input with extended wait: {selector}")
                            break
                    except:
                        continue
            
            if not password_input:
                logger.error("❌ Could not find password input field after extended search")
                logger.warning("⚠️ Password field not found, may need manual intervention")
                return self._handle_login_continuation(timeout_minutes)
            
            # Clear any existing text and enter password
            logger.info("🔐 Entering password")
            try:
                # Clear field first
                password_input.fill("")
                time.sleep(0.5)
                # Type password character by character for better reliability
                password_input.type(self.google_password)
                logger.info("✅ Successfully entered password")
            except Exception as e:
                logger.error(f"Failed to enter password: {e}")
                return self._handle_login_continuation(timeout_minutes)
            
            time.sleep(random.uniform(min_delay/1000, max_delay/1000))
            
            # Click Next/Sign in button
            signin_selectors = [
                '#passwordNext',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Next")',
                'button:has-text("Sign in")',
                'button:has-text("Continue")',
                'button[id*="next"]',
                'input[value*="Sign in"]'
            ]
            
            signin_button = None
            logger.info("🔍 Looking for Sign in button...")
            for i, selector in enumerate(signin_selectors, 1):
                try:
                    logger.debug(f"Trying Sign in button selector {i}/{len(signin_selectors)}: {selector}")
                    signin_button = page.wait_for_selector(selector, timeout=2000)
                    if signin_button and signin_button.is_visible():
                        logger.info(f"✅ Found Sign in button: {selector}")
                        break
                except:
                    continue
            
            if signin_button:
                logger.info("👆 Clicking Sign in button")
                try:
                    signin_button.click()
                    logger.info("✅ Successfully clicked Sign in button")
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"Failed to click Sign in button: {e}")
                    return self._handle_login_continuation(timeout_minutes)
            else:
                logger.warning("⚠️ Could not find Sign in button, trying to submit form with Enter key")
                try:
                    password_input.press("Enter")
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"Failed to submit password form: {e}")
                    return self._handle_login_continuation(timeout_minutes)
            
            # Check for 2FA or successful login
            return self._handle_login_continuation(timeout_minutes)
            
        except Exception as e:
            logger.error(f"Error during automated login: {e}")
            logger.info("Falling back to manual login")
            return self.wait_for_user_login(timeout_minutes)

    def _handle_login_continuation(self, timeout_minutes: int) -> bool:
        """Handle post-password login (2FA detection, success, etc.)"""
        logger.info("🔍 Checking for 2FA requirements or login success...")
        # Dynamic overall timeout: allow longer window if device confirmation engaged later
        base_deadline = time.time() + max(60, timeout_minutes * 60)
        # Hard cap only if not device confirmation; once device confirmation detected we extend up to 15m total
        max_cap_without_device = 300  # 5m
        device_cap = 900  # 15m
        self._device_confirmation_active = False  # reset each invocation
        self._device_ui_shown = False  # reset UI flag for new session

        while True:
            # Compute remaining time budget
            elapsed = time.time()
            remaining = (base_deadline - elapsed)
            if remaining <= 0:
                if self._device_confirmation_active and (elapsed - (base_deadline - max_cap_without_device)) < (device_cap - max_cap_without_device):
                    # We previously hit base deadline but device confirmation started; extend once up to device_cap
                    base_deadline = time.time() + (device_cap - (elapsed - (base_deadline - max_cap_without_device)))
                else:
                    logger.warning("⏰ Login continuation window exhausted")
                    if self._device_confirmation_active:
                        logger.warning("⚠️ Device confirmation still pending. Keeping browser open. You can approve on device and rerun status check.")
                        # Do not force manual fallback—just continue short polling for another 2 minutes grace
                        grace_deadline = time.time() + 120
                        while time.time() < grace_deadline:
                            if self._check_login_status():
                                logger.info("✅ Login completed during grace period after device approval")
                                self._save_session()
                                return True
                            time.sleep(5)
                        logger.warning("⌛ Grace period expired; falling back to manual login wait")
                    return self.wait_for_user_login(timeout_minutes)
            try:
                page = self.page
                if not page:
                    logger.error("Page object missing during login continuation")
                    return False
                page_text = page.content().lower()

                # Success check first
                if self._check_login_status():
                    logger.info("✅ Automated login successful!")
                    self._save_session()
                    return True

                # Detect 2FA
                tfa_detected = self._detect_and_handle_2fa(page)
                if tfa_detected:
                    # If device confirmation just became active, mark and log
                    if not self._device_confirmation_active and any(p in page_text for p in [
                        'check your', 'tap yes', 'galaxy tab', 'ipad', 'iphone', 'google sent a notification', 'notification to verify'
                    ]):
                        self._device_confirmation_active = True
                        logger.info("📱 Device confirmation flow engaged — extending monitoring window")
                    # Passive wait loop (short) before re-evaluating
                    time.sleep(4 if self._device_confirmation_active else 2)
                    continue

                # Error heuristics
                if any(err in page_text for err in ['incorrect', 'wrong password', 'couldn\'t find your', 'invalid password']):
                    logger.error("❌ Credential error detected on login page")
                    return False

                # If device confirmation active, use slower poll cadence
                time.sleep(5 if self._device_confirmation_active else 2)
            except Exception as e:
                logger.debug(f"Error during login continuation loop: {e}")
                time.sleep(3)
        
    def _detect_and_handle_2fa(self, page) -> bool:
        """
        Intelligently detect and handle various 2FA scenarios with interactive CLI prompts
        """
        import time
        
        # Wait a bit longer for any 2FA prompts to appear and stabilize
        time.sleep(3)
        
        # Get page text for pattern detection
        page_text = page.content().lower()
        
        # Debug: Print page URL and key text snippets
        current_url = page.url if page else "unknown"
        logger.debug(f"2FA Detection - URL: {current_url}")
        logger.debug(f"2FA Detection - Page contains '2-step': {'2-step' in page_text}")
        logger.debug(f"2FA Detection - Page contains 'verification': {'verification' in page_text}")
        logger.debug(f"2FA Detection - Page contains 'check your': {'check your' in page_text}")
        logger.debug(f"2FA Detection - Page contains 'notification': {'notification' in page_text}")
        logger.debug(f"2FA Detection - Page contains 'approve': {'approve' in page_text}")
        
        # Enhanced 2FA pattern detection - more comprehensive
        tfa_patterns = [
            '2-step', 'two-step', '2fa', 'two-factor', 'verification', 
            'verify', 'code', 'authenticator', 'device', 'confirm',
            # Device confirmation specific
            'notification', 'approve', 'tap yes', 'check your',
            'google sent', 'sent a notification', 'confirm it\'s you'
        ]
        
        # First check if we're even on a 2FA page anymore (user might have already completed it)
        if not any(phrase in page_text for phrase in tfa_patterns):
            logger.debug("2FA Detection - No 2FA patterns found in page")
            return False
        
        logger.info("🔍 2FA patterns detected, analyzing page...")
        
        # PRIORITY ORDER: Use URL-based detection for accurate classification
        current_url = page.url.lower()
        logger.debug(f"2FA URL analysis: {current_url}")
        
        # 1. Method selection page - URL contains "challenge/selection" OR has multiple challenge types
        if ('challenge/selection' in current_url or 
            self._has_multiple_challenge_types(page)):
            logger.info("🔐 Method selection page detected via URL/elements")
            if self._handle_verification_method_selection(page):
                logger.info("🔐 Verification method selection detected and handled")
                return True
        
        # 2. SMS/Code entry page - URL contains "challenge/ipp" or "challenge/totp"
        elif ('challenge/ipp' in current_url or 'challenge/totp' in current_url):
            logger.info("📲 SMS page detected via URL - checking if phone setup or code entry")
            
            # Check if this is phone number setup or code entry
            if self._is_phone_number_setup_page(page):
                logger.info("📞 Phone number setup page detected")
                return self._handle_phone_verification_setup(page)
            else:
                logger.info("📲 SMS code entry page detected")
                return self._handle_sms_code_entry(page)
        
        # 3. Device confirmation - URL contains "challenge/az" OR specific device confirmation content
        elif ('challenge/az' in current_url or 
              self._is_device_confirmation_page(page, page_text)):
            logger.info("📱 Device confirmation page detected")
            device_confirmation_result = self._handle_specific_2fa_scenarios(page, page_text)
            if device_confirmation_result:
                logger.info("📱 Device confirmation flow detected and handled")
                return True
        
        # 3. Check for phone number verification setup
        if self._handle_phone_verification_setup(page):
            logger.info("📞 Phone verification setup detected and handled")
            return True
            
        # If none of the above worked, something might be wrong - provide debug info
        logger.warning("⚠️ 2FA patterns detected but no specific handler succeeded")
        logger.debug(f"Page title: {page.title()}")
        logger.debug(f"Page content preview: {page_text[:200]}...")
        
        # Save debug snapshot for troubleshooting
        try:
            import os
            if os.getenv('MOODLE_SCRAPE_DEBUG', '0') in ['1', 'true', 'yes', 'on']:
                self._save_2fa_debug_snapshot(page, "unhandled_2fa")
        except Exception as e:
            logger.debug(f"Debug snapshot failed: {e}")
        
        return False
    
    def _save_2fa_debug_snapshot(self, page, tag: str):
        """Save HTML and screenshot for 2FA debugging"""
        try:
            import time
            from pathlib import Path
            
            timestamp = int(time.time())
            debug_dir = Path('data/moodle_session/2fa_debug')
            debug_dir.mkdir(exist_ok=True, parents=True)
            
            # Save HTML content
            html_file = debug_dir / f"{tag}_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page.content())
            
            # Save screenshot if possible
            try:
                screenshot_file = debug_dir / f"{tag}_{timestamp}.png"
                page.screenshot(path=str(screenshot_file))
                logger.info(f"🔍 2FA Debug saved: {html_file.name} and {screenshot_file.name}")
            except Exception:
                logger.info(f"🔍 2FA Debug HTML saved: {html_file.name}")
                
            # Save page info
            info_file = debug_dir / f"{tag}_{timestamp}_info.txt"
            with open(info_file, 'w') as f:
                f.write(f"URL: {page.url}\n")
                f.write(f"Title: {page.title()}\n")
                f.write(f"Timestamp: {timestamp}\n")
                
                # Extract some key text snippets
                page_text = page.content().lower()
                key_phrases = ['check your', 'notification', 'approve', 'verify', '2-step', 'device']
                f.write("\nKey phrases found:\n")
                for phrase in key_phrases:
                    if phrase in page_text:
                        f.write(f"  ✓ {phrase}\n")
                    else:
                        f.write(f"  ✗ {phrase}\n")
                        
        except Exception as e:
            logger.debug(f"Failed to save 2FA debug snapshot: {e}")
    
    def _has_multiple_challenge_types(self, page) -> bool:
        """Check if page has multiple challenge type options (method selection indicator)"""
        try:
            challenge_elements = page.locator('[data-challengetype]').all()
            unique_types = set()
            for elem in challenge_elements:
                challenge_type = elem.get_attribute('data-challengetype')
                if challenge_type:
                    unique_types.add(challenge_type)
            
            # If we have 2+ different challenge types, it's likely a method selection page
            is_method_selection = len(unique_types) >= 2
            logger.debug(f"Challenge types found: {unique_types}, method selection: {is_method_selection}")
            return is_method_selection
        except Exception as e:
            logger.debug(f"Error checking challenge types: {e}")
            return False
    
    def _is_device_confirmation_page(self, page, page_text: str) -> bool:
        """Check if this is specifically a device confirmation page (not method selection)"""
        try:
            # Device confirmation should have specific content but NOT multiple challenge types
            has_device_content = any(phrase in page_text for phrase in [
                'check your device', 'tap yes', 'notification', 'approve this sign-in',
                'confirm it\'s you', 'google sent a notification'
            ])
            
            # Should NOT have multiple challenge types (that would be method selection)
            has_multiple_options = self._has_multiple_challenge_types(page)
            
            is_device_confirmation = has_device_content and not has_multiple_options
            logger.debug(f"Device confirmation check: content={has_device_content}, multiple_options={has_multiple_options}, result={is_device_confirmation}")
            return is_device_confirmation
        except Exception as e:
            logger.debug(f"Error checking device confirmation: {e}")
            return False
    
    def _is_phone_number_setup_page(self, page) -> bool:
        """Check if this is a phone number setup/input page (NOT SMS code entry)"""
        try:
            page_text = page.content().lower()
            
            # Check for phone input field (tel type or phone-related)
            phone_input_selectors = [
                'input[type="tel"]',
                'input[placeholder*="phone" i]',
                'input[name*="phone" i]',
                'input[id*="phone" i]',
                'input[autocomplete="tel"]'
            ]
            
            has_phone_input = False
            for selector in phone_input_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=1000):
                        # Additional check - make sure it's not a code input disguised as tel
                        placeholder = element.get_attribute('placeholder') or ''
                        if 'code' in placeholder.lower() or 'verification' in placeholder.lower():
                            logger.debug(f"Skipping {selector} - appears to be code input: {placeholder}")
                            continue
                        has_phone_input = True
                        logger.debug(f"Found phone input: {selector}")
                        break
                except:
                    continue
            
            # Check for SMS code input (should NOT be phone setup)
            code_input_selectors = [
                'input[placeholder*="code" i]',
                'input[placeholder*="verification" i]',
                'input[maxlength="6"]',
                'input[maxlength="8"]',
                'input[name*="code" i]'
            ]
            
            has_code_input = False
            for selector in code_input_selectors:
                try:
                    if page.locator(selector).first.is_visible(timeout=1000):
                        has_code_input = True
                        logger.debug(f"Found code input: {selector}")
                        break
                except:
                    continue
            
            # Check for phone setup text patterns (NOT code entry patterns)
            phone_setup_patterns = [
                'enter your phone number', 'add a phone number', 'phone number verification',
                'add phone', 'verify your phone', 'we need to verify your phone',
                'provide a phone number', 'phone number for verification'
            ]
            
            # Code entry patterns (should exclude this from being phone setup)
            code_entry_patterns = [
                'enter the code', 'verification code sent', 'code sent to',
                'enter code', 'sms code', '6-digit code'
            ]
            
            has_phone_text = any(pattern in page_text for pattern in phone_setup_patterns)
            has_code_text = any(pattern in page_text for pattern in code_entry_patterns)
            
            # Only consider it phone setup if:
            # 1. Has phone input OR phone setup text
            # 2. Does NOT have code input or code text
            is_phone_setup = (has_phone_input or has_phone_text) and not (has_code_input or has_code_text)
            
            logger.debug(f"Phone setup check: phone_input={has_phone_input}, phone_text={has_phone_text}, code_input={has_code_input}, code_text={has_code_text}, result={is_phone_setup}")
            
            return is_phone_setup
            
        except Exception as e:
            logger.debug(f"Error checking phone setup: {e}")
            return False
    
    def _extract_device_name(self, page_text: str) -> str:
        """Extract device name from page text"""
        try:
            import re
            # Try to extract specific device names
            if 'honor x9c' in page_text.lower():
                return 'Honor X9c'
            elif 'galaxy tab s9' in page_text.lower():
                return 'Galaxy Tab S9'
            elif 'galaxy tab' in page_text.lower():
                match = re.search(r'galaxy tab[^.<\n]*', page_text, re.IGNORECASE)
                if match:
                    return match.group(0).title()
                return 'Galaxy Tab'
            elif 'ipad' in page_text.lower():
                return 'your iPad'
            elif 'iphone' in page_text.lower():
                return 'your iPhone'
            elif 'android' in page_text.lower():
                return 'your Android device'
            elif 'tablet' in page_text.lower():
                return 'your tablet'
            else:
                return 'your device'
        except Exception:
            return 'your device'
    
    def _show_device_confirmation_ui(self, page, device_name: str):
        """Show the device confirmation UI with options"""
        # Check if UI already shown to prevent repetition
        if self._device_ui_shown:
            return
            
        self._device_ui_shown = True
        
        # Force flush to ensure output is visible
        import sys
        print(f"\n" + "="*60, flush=True)
        print(f"📱 DEVICE CONFIRMATION REQUIRED", flush=True)
        print(f"🔔 Approve the sign-in on {device_name}.", flush=True)
        print("💡 You can also choose to resend or pick another method below.", flush=True)
        print("="*60, flush=True)
        sys.stdout.flush()
        
        # Check for resend / alternate method options
        resend = False
        try_another = False
        
        print("🔍 Checking for interactive options...", flush=True)
        
        # Multiple selectors for resend button
        resend_selectors = [
            'span[jsname="V67aGc"]:has-text("Resend it")',
            'span:has-text("Resend it")',
            'button:has-text("Resend")',
            'a:has-text("Resend")',
            '*:has-text("Resend it")',
            '*:has-text("Resend")'
        ]
        
        # Multiple selectors for try another way
        try_another_selectors = [
            'span[jsname="V67aGc"]:has-text("Try another way")',
            'span:has-text("Try another way")',
            'button:has-text("Try another way")',
            'a:has-text("Try another way")',
            '*:has-text("Try another way")',
            '*:has-text("Use a different method")',
            '*:has-text("Other options")'
        ]
        
        try:
            # Check for resend options
            for selector in resend_selectors:
                try:
                    if page.locator(selector).first.is_visible(timeout=1000):
                        resend = True
                        print(f"✅ Found resend option with: {selector}", flush=True)
                        logger.debug(f"Resend option found with selector: {selector}")
                        break
                except Exception:
                    continue
            
            # Check for try another way options    
            for selector in try_another_selectors:
                try:
                    if page.locator(selector).first.is_visible(timeout=1000):
                        try_another = True
                        print(f"✅ Found 'try another way' option with: {selector}", flush=True)
                        logger.debug(f"Try another way option found with selector: {selector}")
                        break
                except Exception:
                    continue
                    
            if not resend and not try_another:
                print("⚠️ No interactive options found - buttons may not be available yet", flush=True)
                
        except Exception as e:
            print(f"❌ Error checking for interactive options: {e}", flush=True)
            logger.debug(f"Error checking for resend/try another options: {e}")
        
        # Always show the interactive menu for device confirmation
        opts = ["Wait for approval"]
        if resend: 
            opts.append("Resend notification")
        if try_another: 
            opts.append("Try another way")
        else:
            # Add generic "Try another way" option even if button not detected
            opts.append("Try another verification method")
        
        print("\nAvailable options:", flush=True)
        for i, o in enumerate(opts, 1):
            print(f"{i}. {o}", flush=True)
        print(flush=True)  # Extra line break
        sys.stdout.flush()
        
        try:
            choice = input("Select option (1-{}, Enter for option 1): ".format(len(opts))).strip()
            
            # Default to option 1 if no input
            if not choice:
                choice = '1'
                
            if choice == '2' and resend:
                try:
                    page.locator('span[jsname="V67aGc"]:has-text("Resend it")').first.click()
                    print("📤 Notification resent.", flush=True)
                except Exception as e:
                    print(f"⚠️ Failed to resend notification: {e}", flush=True)
                    
            elif choice == '2' and not resend:
                # Generic "Try another verification method" was selected
                print("🔄 Looking for alternative verification methods...", flush=True)
                # Try to find and click "Try another way" or similar
                alt_selectors = [
                    'span[jsname="V67aGc"]:has-text("Try another way")',
                    'span:has-text("Try another way")',
                    'button:has-text("Try another way")',
                    'a:has-text("Try another way")',
                    '*:has-text("Use a different method")',
                    '*:has-text("Other options")'
                ]
                clicked = False
                for selector in alt_selectors:
                    try:
                        if page.locator(selector).first.is_visible(timeout=1000):
                            page.locator(selector).first.click()
                            print("🔄 Loading alternative methods...", flush=True)
                            time.sleep(2)
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    print("⚠️ Could not find 'Try another way' button. You may need to manually click it in the browser.", flush=True)
                    
            elif choice == '3' and try_another:
                try:
                    page.locator('span[jsname="V67aGc"]:has-text("Try another way")').first.click()
                    print("🔄 Loading alternative methods...", flush=True)
                    time.sleep(2)
                except Exception as e:
                    print(f"⚠️ Failed to open alternative methods: {e}", flush=True)
            else:
                print("⏳ Waiting for device approval...", flush=True)
                    
        except KeyboardInterrupt:
            print("\n⏸️ Skipping method selection...", flush=True)
            
        print("💡 If you don't see the notification, check your device manually", flush=True)
        
        sys.stdout.flush()  # Final flush to ensure everything is visible
    
    def _handle_phone_verification_setup(self, page):
        """Handle phone number setup for 2FA"""
        print(f"\n📱 PHONE NUMBER SETUP REQUIRED", flush=True)
        print("Google needs to verify your phone number for 2FA", flush=True)
        
        try:
            # Look for phone input field with multiple selectors
            phone_input_selectors = [
                'input[type="tel"]',
                'input[placeholder*="phone" i]',
                'input[name*="phone" i]',
                'input[id*="phone" i]',
                'input[autocomplete="tel"]'
            ]
            
            phone_input = None
            for selector in phone_input_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        phone_input = element
                        logger.debug(f"Found phone input with selector: {selector}")
                        break
                except:
                    continue
            
            if not phone_input:
                print("❌ Could not find phone input field")
                return self._handle_generic_verification(page)
            
            # Get phone number from user
            print("\n📞 Please enter your phone number:")
            print("   - Include country code (e.g., +1 for US, +63 for Philippines)")
            print("   - Example: +639123456789")
            
            phone_number = input("Phone number: ").strip()
            
            if not phone_number:
                print("❌ No phone number entered")
                return False
            
            print(f"📱 Entering phone number: {phone_number}")
            phone_input.fill(phone_number)
            time.sleep(1)
            
            # Look for submit button
            submit_selectors = [
                'button:has-text("Next")',
                'button:has-text("Continue")', 
                'button:has-text("Send")',
                'button:has-text("Verify")',
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        submit_button = element
                        logger.debug(f"Found submit button with selector: {selector}")
                        break
                except:
                    continue
            
            if submit_button:
                print("📤 Submitting phone number...")
                submit_button.click()
                print("⏳ Waiting for page transition...")
                time.sleep(5)  # Give more time for page to change
                
                # Check if we successfully moved to SMS code entry
                new_url = page.url.lower()
                print(f"🔍 New URL after submission: {new_url}")
                
                if self._is_phone_number_setup_page(page):
                    print("⚠️ Still on phone setup page - submission may have failed")
                    # Don't return True - let it try again or handle error
                    return False
                else:
                    print("✅ Phone number submitted - moved to next step")
                    return True
            else:
                print("⚠️ Could not find submit button - trying Enter key")
                phone_input.press("Enter")
                time.sleep(5)
                
                # Check transition after Enter key
                if self._is_phone_number_setup_page(page):
                    print("❌ Enter key submission failed")
                    return False
                else:
                    print("✅ Phone number submitted via Enter")
                    return True
                
        except Exception as e:
            print(f"❌ Error during phone setup: {e}")
            logger.error(f"Phone verification setup error: {e}")
            return self._handle_generic_verification(page)
    
    def _handle_verification_method_selection(self, page):
        """Handle when user needs to choose verification method"""
        selection_patterns = [
            'text=How would you like to verify',
            'text=Choose a verification method',
            'text=Select how to get your code',
            'text=Try another way',
            'text=More ways to verify',
            'text=Choose how you want to sign in',  # From actual HTML
            'span[jsname="I74d0c"]'  # The span containing "Choose how you want to sign in:"
        ]
        
        for pattern in selection_patterns:
            try:
                if page.locator(pattern).is_visible(timeout=1000):
                    print(f"\n🔐 Verification Method Selection (detected with: {pattern})", flush=True)
                    logger.info(f"Method selection page detected with pattern: {pattern}")
                    
                    # Look for available options using the actual HTML structure
                    available_options = []
                    
                    # Check for device confirmation option (challengetype="39")
                    try:
                        if page.locator('div[data-challengetype="39"]').is_visible(timeout=500):
                            device_text = page.locator('div[data-challengetype="39"] .l5PPKe').text_content()
                            available_options.append(('div[data-challengetype="39"]', f'Device confirmation: {device_text}'))
                    except:
                        pass
                    
                    # Check for authenticator app option (challengetype="5")
                    try:
                        if page.locator('div[data-challengetype="5"]').is_visible(timeout=500):
                            auth_text = page.locator('div[data-challengetype="5"] .l5PPKe').text_content()
                            available_options.append(('div[data-challengetype="5"]', f'Authenticator app: {auth_text}'))
                    except:
                        pass
                    
                    # Check for SMS option (challengetype="9") - PRIORITY AUTO-SELECT
                    sms_found = False
                    try:
                        if page.locator('div[data-challengetype="9"]').is_visible(timeout=500):
                            sms_text = page.locator('div[data-challengetype="9"] .l5PPKe').text_content()
                            available_options.append(('div[data-challengetype="9"]', f'SMS code: {sms_text}'))
                            sms_found = True
                    except Exception as e:
                        logger.debug(f"SMS detection failed: {e}")
                    
                    # AUTO-SELECT SMS IMMEDIATELY if found
                    if sms_found:
                        logger.info("🎯 SMS option detected - attempting auto-selection")
                        
                        # Extract phone number hint from SMS option
                        phone_hint = "your phone"
                        try:
                            phone_span = page.query_selector('div[data-challengetype="9"] span[jsname="wKtwcc"]')
                            if phone_span:
                                phone_text = phone_span.inner_text().strip()
                                if phone_text:
                                    # Convert patterns like "•••• ••• ••51" to "***-***-51"
                                    import re
                                    # Extract last 2-4 digits
                                    match = re.search(r'(\d{2,4})$', phone_text)
                                    if match:
                                        phone_hint = f"***-***-{match.group(1)}"
                                    else:
                                        phone_hint = phone_text  # Use as-is if pattern doesn't match
                        except Exception as e:
                            logger.debug(f"Phone hint extraction failed: {e}")
                        
                        print(f"\n🚀 AUTO-SELECTING SMS VERIFICATION", flush=True)
                        print(f"📱 Automatically choosing SMS verification...", flush=True)
                        print(f"💬 SMS will be sent to {phone_hint}", flush=True)
                        
                        # Enhanced SMS click attempts with more selectors
                        sms_selectors = [
                            'div[data-challengetype="9"]',
                            'div[role="link"][data-challengetype="9"]',
                            'div[jsname="EBHGs"][data-challengetype="9"]',
                            'div[data-challengetype="9"] div[role="link"]',
                            'div[data-challengetype="9"][role="link"]'
                        ]
                        
                        click_success = False
                        for i, selector in enumerate(sms_selectors, 1):
                            try:
                                logger.debug(f"Trying SMS click method {i}: {selector}")
                                sms_element = page.locator(selector).first
                                if sms_element.is_visible(timeout=2000):
                                    sms_element.click()
                                    click_success = True
                                    logger.info(f"✅ SMS clicked successfully with method {i}: {selector}")
                                    break
                            except Exception as e:
                                logger.debug(f"SMS click method {i} failed: {e}")
                                continue
                        
                        if click_success:
                            print("✅ SMS verification selected successfully!", flush=True)
                            print("⏳ Waiting for SMS code input page...", flush=True)
                            time.sleep(3)  # Give more time for page transition
                            return True  # This will trigger SMS code detection
                        else:
                            print("❌ SMS auto-selection failed - showing manual options", flush=True)
                            logger.warning("All SMS click methods failed")
                    
                    # Check for backup codes (challengetype="8")
                    try:
                        if page.locator('div[data-challengetype="8"]').is_visible(timeout=500):
                            backup_text = page.locator('div[data-challengetype="8"] .l5PPKe').text_content()
                            available_options.append(('div[data-challengetype="8"]', f'Backup codes: {backup_text}'))
                    except:
                        pass
                    
                    # Check for passkey option (challengetype="53")
                    try:
                        if page.locator('div[data-challengetype="53"]').is_visible(timeout=500):
                            passkey_text = page.locator('div[data-challengetype="53"] .l5PPKe').text_content()
                            available_options.append(('div[data-challengetype="53"]', f'Passkey: {passkey_text}'))
                    except:
                        pass
                    
                    # Fallback to generic text-based detection if structured detection fails
                    if not available_options:
                        option_selectors = [
                            ('text*=text message', 'SMS'),
                            ('text*=phone call', 'Phone Call'),
                            ('text*=authenticator', 'Authenticator App'),
                            ('text*=backup code', 'Backup Code'),
                            ('text*=security key', 'Security Key'),
                            ('text*=another device', 'Another Device'),
                            ('text*=passkey', 'Passkey')
                        ]
                        
                        for selector, option_name in option_selectors:
                            try:
                                if page.locator(selector).is_visible(timeout=500):
                                    available_options.append((selector, option_name))
                            except:
                                continue
                    
                    if available_options:
                        print("Available verification methods:")
                        for i, (_, option_name) in enumerate(available_options, 1):
                            print(f"{i}. {option_name}")
                        
                        while True:
                            try:
                                choice = input("Please select a verification method (number): ").strip()
                                if choice.isdigit():
                                    choice_num = int(choice) - 1
                                    if 0 <= choice_num < len(available_options):
                                        selector, option_name = available_options[choice_num]
                                        print(f"Selected: {option_name}")
                                        
                                        # Click the selected option
                                        page.locator(selector).first.click()
                                        time.sleep(2)
                                        
                                        # Handle the specific verification type based on challengetype or text
                                        if 'data-challengetype="9"' in selector or 'SMS' in option_name or 'text message' in option_name.lower():
                                            return self._handle_sms_code_entry(page)
                                        elif 'data-challengetype="5"' in selector or 'authenticator' in option_name.lower():
                                            return self._handle_authenticator_code(page)
                                        elif 'data-challengetype="8"' in selector or 'backup' in option_name.lower():
                                            return self._handle_backup_code(page)
                                        elif 'data-challengetype="39"' in selector or 'device' in option_name.lower():
                                            # Device confirmation - let it be handled by the main detection loop
                                            return True
                                        elif 'data-challengetype="53"' in selector or 'passkey' in option_name.lower():
                                            print("🔐 Passkey authentication initiated. Please follow the browser prompts.")
                                            return self._handle_generic_verification(page)
                                        else:
                                            return self._handle_generic_verification(page)
                                    else:
                                        print(f"Please enter a number between 1 and {len(available_options)}")
                                else:
                                    print("Please enter a valid number")
                            except KeyboardInterrupt:
                                print("\n⏸️ Skipping method selection...")
                                return False
                            except ValueError:
                                print("Please enter a valid number")
                    else:
                        return self._handle_generic_verification(page)
                    
                    return True
            except Exception:
                continue
        return False
    
    def _handle_sms_code_entry(self, page):
        """Handle SMS code entry"""
        print("\n📱 SMS Verification")
        code = input("Please enter the verification code sent to your phone: ")
        
        # Find SMS code input field
        sms_inputs = [
            'input[type="tel"]',
            'input[placeholder*="code"]',
            'input[aria-label*="code"]',
            'input[name*="code"]',
            'input[autocomplete="one-time-code"]'
        ]
        
        for selector in sms_inputs:
            try:
                input_field = page.locator(selector).first
                if input_field.is_visible():
                    input_field.fill(code)
                    break
            except:
                continue
        
        # Submit the code
        self._click_submit_button(page)
        return True
    
    def _handle_authenticator_code(self, page):
        """Handle authenticator app code entry"""
        print("\n� Authenticator App Verification")
        code = input("Please enter the 6-digit code from your authenticator app: ")
        
        # Find authenticator input field
        auth_inputs = [
            'input[type="text"]',
            'input[type="tel"]',
            'input[placeholder*="code"]',
            'input[maxlength="6"]'
        ]
        
        for selector in auth_inputs:
            try:
                input_field = page.locator(selector).first
                if input_field.is_visible():
                    input_field.fill(code)
                    break
            except:
                continue
        
        self._click_submit_button(page)
        return True
    
    def _handle_backup_code(self, page):
        """Handle backup code entry"""
        print("\n🔑 Backup Code Verification")
        code = input("Please enter one of your 8-digit backup codes: ")
        
        # Find backup code input
        input_field = page.locator('input').first
        if input_field.is_visible():
            input_field.fill(code)
        
        self._click_submit_button(page)
        return True
    
    def _handle_generic_verification(self, page):
        """Handle generic verification scenarios"""
        print("\n🔐 Manual Verification Required")
        print("Please complete the verification process manually in the browser.")
        input("Press Enter once you've completed verification...")
        return True
    
    def _click_submit_button(self, page):
        """Find and click the appropriate submit button"""
        submit_buttons = [
            'button[type="submit"]',
            'button:has-text("Next")',
            'button:has-text("Verify")',
            'button:has-text("Continue")',
            'button:has-text("Submit")',
            'input[type="submit"]'
        ]
        
        for selector in submit_buttons:
            try:
                btn = page.locator(selector).first
                if btn.is_visible():
                    btn.click()
                    page.wait_for_load_state('networkidle', timeout=10000)
                    return True
            except:
                continue
        return False
    
    def _handle_specific_2fa_scenarios(self, page, page_text):
        """Handle other specific 2FA scenarios using page text analysis"""
        logger.debug("=== 2FA SCENARIO DETECTION START ===")
        logger.debug(f"Page URL: {page.url}")
        logger.debug(f"Page text length: {len(page_text)} characters")
        
        device_confirmation_detected = False
        device_name = "your device"
        
        # CRITICAL: Check if we're already logged in successfully to avoid false positives
        current_url = page.url.lower()
        
        # Only check for actual Moodle dashboard indicators, not login URLs
        login_success_indicators = [
            'dashboard',
            'my courses',
            'site home',
            'university of makati',
            'course overview'
        ]
        
        # URL-based success indicators (must be on actual Moodle site, not accounts.google.com)
        moodle_success_urls = [
            'tbl.umak.edu.ph/my/',
            'tbl.umak.edu.ph/course/',
            'tbl.umak.edu.ph/?redirect=0'
        ]
        
        # Only skip device confirmation if we're actually ON the Moodle site (not Google accounts)
        is_on_google_accounts = 'accounts.google.com' in current_url
        is_on_moodle_success = any(url in current_url for url in moodle_success_urls)
        has_moodle_content = any(indicator in page_text for indicator in login_success_indicators)
        
        if not is_on_google_accounts and (is_on_moodle_success or has_moodle_content):
            logger.debug("Already logged in successfully - skipping device confirmation detection")
            return False
        
        logger.debug(f"Not yet logged in - on_google: {is_on_google_accounts}, moodle_success: {is_on_moodle_success}, moodle_content: {has_moodle_content}")
        
        # ENHANCED DEVICE CONFIRMATION DETECTION - HIGHEST PRIORITY
        device_confirmation_phrases = [
            # Core confirmation phrases
            'check your', 'tap yes', 'confirm', 'approve', 
            'device notification', 'push notification', 'phone notification',
            'notification to verify', 'gmail app', 'tap yes on your', 
            'google sent a notification', 'sent a notification to',
            
            # Device types (from your screenshot)
            'honor x9c', 'galaxy tab s9', 'galaxy tab', 'ipad', 'tablet', 
            'android device', 'iphone', 'your phone', 'your device', 'another device',
            
            # Action phrases
            'approve this sign-in', 'confirm it\'s you', 'verify it\'s you',
            'sign in request', 'approve sign-in', 'confirm your identity',
            'check for a notification', 'look for a notification',
            
            # Google-specific patterns (from your screenshot)
            'we sent a notification', 'notification sent to', 'check the notification',
            'tap the notification', 'open the notification',
            'google sent a notification to your', 'tap yes on the notification',
            'or open the gmail app on your iphone to verify',
            
            # Exact patterns from screenshot
            'check your device', 'google sent a notification to your honor x9c and galaxy tab s9',
            'tap yes on the notification to verify it\'s you',
            'or open the gmail app on your iphone to verify it\'s you from there'
        ]
        
        # RELAXED method selection detection - only block if very explicit
        method_selection_indicators = [
            'choose how you want to sign in',
            'choose a verification method', 
            'select how to get your code',
            'more ways to verify it\'s you'
        ]
        
        # Debug all pattern matches
        matched_device_phrases = [p for p in device_confirmation_phrases if p in page_text]
        matched_selection_phrases = [p for p in method_selection_indicators if p in page_text]
        
        logger.debug(f"Device confirmation phrases found: {matched_device_phrases}")
        logger.debug(f"Method selection phrases found: {matched_selection_phrases}")
        
        # Enhanced element-based detection FIRST (more reliable than text)
        device_confirmation_elements = [
            # SPECIFIC device confirmation elements (NOT generic 2FA)
            'h1:has-text("Check your device")',
            'h2:has-text("Check your")',
            'span:has-text("Check your")',
            'div:has-text("Google sent a notification")',
            'div:has-text("We sent a notification")',
            'span:has-text("Tap Yes")',
            'span:has-text("tap Yes")',
            'div:has-text("approve this sign-in")',
            'div:has-text("confirm it\'s you")',
            
            # Specific device confirmation content
            'div:has-text("Check your device")',
            'text=Check your device',
            'div:has-text("Google sent a notification to your Honor X9c")',
            'div:has-text("Tap Yes on the notification")',
            'div:has-text("or open the Gmail app")',
            'div:has-text("notification to verify")',
            'div:has-text("check for a notification")',
            'div:has-text("tap yes on the notification")',
            
            # Technical indicators for device confirmation
            'div[data-challenge-ui="CONFIRM_DEVICE"]',
            '[data-action="confirm_device"]',
            'div[data-challengetype="39"]'  # Device confirmation challenge type
        ]
        
        # Try element-based detection first with retry logic
        for sel in device_confirmation_elements:
            try:
                element = page.locator(sel).first
                # Use longer timeout for device confirmation elements (they may load slowly)
                if element.is_visible(timeout=3000):
                    device_confirmation_detected = True
                    logger.info(f"🎯 DEVICE CONFIRMATION DETECTED via element: {sel}")
                    print(f"🎯 DEVICE CONFIRMATION DETECTED via element: {sel}")
                    print(f"📱 2-Step Verification page detected!")
                    self._device_confirmation_active = True
                    
                    # Extract device name if possible
                    if device_name == 'your device':
                        device_name = self._extract_device_name(page_text)
                    
                    # SHOW UI IMMEDIATELY when detected via elements
                    self._show_device_confirmation_ui(page, device_name)
                    # Don't return True immediately - let the caller handle the wait loop
                    return True
                    
            except Exception as e:
                logger.debug(f"Element check failed for {sel}: {e}")
                continue
        
        # If element detection failed, wait a bit more and try again (Google UI can be slow)
        if not device_confirmation_detected:
            logger.debug("First element detection pass failed, waiting and retrying...")
            time.sleep(2)
            for sel in device_confirmation_elements[:5]:  # Try top 5 most reliable selectors again
                try:
                    element = page.locator(sel).first
                    if element.is_visible(timeout=2000):
                        device_confirmation_detected = True
                        logger.info(f"🎯 DEVICE CONFIRMATION DETECTED via element (retry): {sel}")
                        print(f"✅ DEBUG: Device confirmation detected via element (retry): {sel}")
                        self._device_confirmation_active = True
                        
                        # Extract device name if possible
                        if device_name == 'your device':
                            device_name = self._extract_device_name(page_text)
                        
                        # SHOW UI IMMEDIATELY when detected via elements (retry)
                        self._show_device_confirmation_ui(page, device_name)
                        return True
        
                except Exception as e:
                    logger.debug(f"Retry element check failed for {sel}: {e}")
                    continue
        
        # If not found via elements, try text-based detection with improved logic
        if not device_confirmation_detected:
            # Check if this is clearly a method selection page
            is_method_selection = any(phrase in page_text for phrase in method_selection_indicators)
            
            if is_method_selection:
                logger.debug("❌ This is a method selection page, not device confirmation")
                # Continue to other detection methods but don't trigger device confirmation
            else:
                # Enhanced text pattern matching
                text_detected = any(p in page_text for p in device_confirmation_phrases)
                
                # Additional context checks for device confirmation
                device_context_phrases = [
                    'we sent a notification to verify it\'s you',
                    'check your device for a notification',
                    'approve this sign-in on your',
                    'confirm this sign-in'
                ]
                context_detected = any(p in page_text for p in device_context_phrases)
                
                logger.debug(f"✅ Device confirmation text patterns detected: {text_detected}")
                logger.debug(f"✅ Device context patterns detected: {context_detected}")
                
                # Trigger if either main patterns OR context patterns match
                if text_detected or context_detected:
                    device_confirmation_detected = True
                    logger.info("🎯 DEVICE CONFIRMATION DETECTED via text patterns!")
                    print(f"✅ DEBUG: Device confirmation detected! Phrases: {matched_device_phrases}")
                    
                    # Mark session state so continuation logic knows
                    self._device_confirmation_active = True
                    
                    # Extract device name if possible
                    if device_name == 'your device':
                        device_name = self._extract_device_name(page_text)
                    
                    # SHOW UI using the centralized function
                    self._show_device_confirmation_ui(page, device_name)
                    return True
        
        # This section is now handled by the element-based detection above
        
        # If device confirmation already detected, just return True
        if device_confirmation_detected:
            logger.debug("Device confirmation already handled, returning True")
            return True
        # SMS/Text codes - now with more specific detection to avoid false positives
        sms_specific_phrases = [
            'enter the code', 'verification code sent', 'code sent to',
            'enter code', 'text message code', '6-digit code',
            'sms code', 'phone number ending in'
        ]
        
        if any(phrase in page_text for phrase in sms_specific_phrases):
            logger.debug(f"🔍 SMS code detection triggered by: {[p for p in sms_specific_phrases if p in page_text]}")
            # Try to extract phone number hint
            phone_hint = "your phone"
            if 'ending in' in page_text:
                import re
                match = re.search(r'ending in (\d+)', page_text)
                if match:
                    phone_hint = f"***-***-{match.group(1)}"
            
            print(f"\n📱 SMS Code Required")
            print(f"💬 A verification code was sent to {phone_hint}")
            return self._handle_sms_code_entry(page)
        
        # Authenticator apps - now with interactive input
        authenticator_phrases = [
            'authenticator', 'google authenticator', 'auth app',
            'verification app', 'time-based'
        ]
        if any(phrase in page_text for phrase in authenticator_phrases):
            logger.debug(f"🔍 Authenticator detection triggered by: {[p for p in authenticator_phrases if p in page_text]}")
            print("\n🔐 Authenticator App Required")
            print("📲 Please use your authenticator app")
            return self._handle_authenticator_code(page)
        
        # Backup codes - now with interactive input
        backup_phrases = [
            'backup code', 'recovery code', 'backup verification'
        ]
        if any(phrase in page_text for phrase in backup_phrases):
            logger.debug(f"🔍 Backup code detection triggered by: {[p for p in backup_phrases if p in page_text]}")
            print("\n🔑 Backup Code Required")
            print("📄 Please use one of your backup codes")
            return self._handle_backup_code(page)
        
        # Generic 2FA detection - VERY RESTRICTIVE last resort (avoid false positives with device confirmation)
        # Only trigger if it's clearly 2FA but NOT any of the above specific scenarios
        generic_2fa_phrases = [
            '2-step', 'two-step', '2fa', 'two-factor'
        ]
        # EXCLUDE common words that might appear in device confirmation pages - EXPANDED LIST
        device_exclusion_phrases = [
            'check your', 'tap yes', 'notification', 'approve', 'confirm your identity',
            'google sent a notification', 'galaxy tab', 'ipad', 'iphone', 'android device',
            'your phone', 'your device', 'notification to verify', 'gmail app', 'push notification'
        ]
        
        has_generic_2fa = any(phrase in page_text for phrase in generic_2fa_phrases)
        has_device_indicators = any(phrase in page_text for phrase in device_exclusion_phrases)
        
        logger.debug(f"🔍 Generic 2FA check: has_generic={has_generic_2fa}, has_device_indicators={has_device_indicators}")
        logger.debug(f"🔍 Device exclusion phrases found: {[p for p in device_exclusion_phrases if p in page_text]}")
        
        # CRITICAL: If device indicators are present, DO NOT trigger generic 2FA
        if has_generic_2fa and not has_device_indicators:
            matching_generic_phrases = [phrase for phrase in generic_2fa_phrases if phrase in page_text]
            logger.warning(f"⚠️ Generic 2FA detected - no specific scenario matched. Phrases: {matching_generic_phrases}")
            print(f"❌ DEBUG: Generic 2FA fallback triggered by: {matching_generic_phrases}")
            print(f"❌ DEBUG: Device indicators present: {[p for p in device_exclusion_phrases if p in page_text]}")
            print("\n🔐 Additional Verification Required")
            print("🛡️  Please complete the security verification")
            return self._handle_generic_verification(page)
        elif has_generic_2fa and has_device_indicators:
            logger.debug(f"🚫 Generic 2FA patterns found BUT device indicators present - skipping generic fallback")
            logger.debug(f"🚫 This appears to be device confirmation that wasn't caught earlier")
            print(f"✅ DEBUG: Skipped generic 2FA because device indicators found: {[p for p in device_exclusion_phrases if p in page_text]}")
        
        logger.debug("=== 2FA SCENARIO DETECTION END - No scenarios detected ===")
        return False

    def wait_for_user_login(self, timeout_minutes: int = 10) -> bool:
        """Wait for user to manually login and detect when they're logged in"""
        logger.info(f"⏳ Waiting for user to login (timeout: {timeout_minutes} minutes)")
        logger.info("💡 Complete Moodle (and Google SSO if used) authentication in the browser window")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        stable_success_count = 0
        
        while time.time() - start_time < timeout_seconds:
            try:
                if self._check_login_status():
                    stable_success_count += 1
                    # Require a couple consecutive positives to avoid false positives
                    if stable_success_count >= 2:
                        logger.info("✅ Login detected and stabilized")
                        self._save_session()
                        return True
                else:
                    stable_success_count = 0
                time.sleep(2)
            except Exception as e:
                logger.debug(f"Error during login check: {e}")
                time.sleep(2)
        logger.warning(f"⏰ Login timeout after {timeout_minutes} minutes")
        return False

    def _compute_login_signals(self) -> Dict[str, bool]:
        signals = {
            'body_logged_in': False,
            'menu_present': False,
            'user_avatar': False,
            'cookie_present': False,
            'login_form': False,
            'url_has_login': False
        }
        try:
            if self.page:
                url = (self.page.url or '').lower()
                signals['url_has_login'] = 'login' in url
                # body class
                try:
                    body_class = self.page.eval_on_selector('body', 'el => el.className') or ''
                    signals['body_logged_in'] = any(cls in body_class.split() for cls in ['userloggedin', 'path-my'])
                    self._last_body_class = body_class
                except Exception:
                    pass
                # menu / avatar selectors (try several)
                menu_selectors = [
                    '.usermenu', '#user-menu-toggle', 'a[href*="logout" i]',
                    'nav[aria-label="User menu"]', 'div[data-region="drawer"] .usermenu',
                    'div[data-region="drawer"] a[href*="logout" i]'
                ]
                for sel in menu_selectors:
                    try:
                        if self.page.query_selector(sel):
                            signals['menu_present'] = True
                            break
                    except Exception:
                        continue
                avatar_selectors = [
                    'img.userpicture', 'img[alt*="profile" i]', 'span.userinitials'
                ]
                for sel in avatar_selectors:
                    try:
                        if self.page.query_selector(sel):
                            signals['user_avatar'] = True
                            break
                    except Exception:
                        continue
                # cookies
                signals['cookie_present'] = len(self._get_moodle_cookies()) > 0
                # login form
                signals['login_form'] = self._is_login_form_present()
            elif self.driver:
                url = (self.driver.current_url or '').lower()
                signals['url_has_login'] = 'login' in url
                try:
                    body_class = self.driver.execute_script('return document.body.className') or ''
                    signals['body_logged_in'] = any(cls in body_class.split() for cls in ['userloggedin', 'path-my'])
                    self._last_body_class = body_class
                except Exception:
                    pass
                try:
                    if self.driver.find_elements(By.CLASS_NAME, 'usermenu') or \
                       self.driver.find_elements(By.ID, 'user-menu-toggle'):
                        signals['menu_present'] = True
                    if self.driver.find_elements(By.CSS_SELECTOR, 'img.userpicture') or \
                       self.driver.find_elements(By.CSS_SELECTOR, 'span.userinitials'):
                        signals['user_avatar'] = True
                except Exception:
                    pass
                try:
                    signals['cookie_present'] = len(self._get_moodle_cookies()) > 0
                except Exception:
                    pass
                signals['login_form'] = self._is_login_form_present()
        except Exception as e:
            logger.debug(f"Error computing login signals: {e}")
        return signals

    def _capture_debug_snapshot(self, tag: str):
        if not self.page:
            return
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        base = self.session_dir / f'snapshot_{tag}_{ts}'
        try:
            html_path = base.with_suffix('.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.page.content())
            try:
                self.page.screenshot(path=str(base.with_suffix('.png')))
            except Exception:
                pass
            logger.info(f"📝 Saved debug snapshot: {html_path.name}")
        except Exception as e:
            logger.debug(f"Snapshot error: {e}")

    def _attempt_auto_sso_login(self, force_retry: bool = False) -> bool:
        """Attempt automatic Google SSO click if login form is present.
        Returns True if a click was issued (then we wait for redirects)."""
        if getattr(self, '_sso_attempted', False) and not force_retry:
            return False
        if not self.page:
            return False
        try:
            # Candidate selectors (provided snippet + fallbacks)
            selectors = [
                'a.login-identityprovider-btn[href*="oauth2/login.php"][href*="id=1"]',
                'a.login-identityprovider-btn[href*="oauth2/login.php"]',
                'a[href*="auth/oauth2/login.php"][class*="identityprovider"]',
                'a[href*="oauth2"][class*="btn"]',
                'a[class*="google"][class*="btn"]',
                'button[class*="google"]',
                'input[value*="Google"]'
            ]
            for sel in selectors:
                el = None
                try:
                    el = self.page.query_selector(sel)
                except Exception:
                    continue
                if el:
                    text_content = (el.text_content() or '').strip().lower()
                    # Heuristic: must contain university or google context
                    if any(k in text_content for k in ['university', 'google', 'makati', 'sso', 'login']):
                        logger.info(f"⚡ Auto-clicking SSO button via selector: {sel}")
                        logger.info(f"🔍 Button text: '{text_content}'")
                        self._sso_attempted = True
                        el.click()
                        return True
            
            # If no specific SSO button found, look for generic patterns
            generic_selectors = [
                'a[href*="oauth2"]',
                'a[href*="google"]',
                'button:has-text("Google")',
                'a:has-text("Google")'
            ]
            
            for sel in generic_selectors:
                try:
                    el = self.page.query_selector(sel)
                    if el:
                        logger.info(f"⚡ Auto-clicking generic SSO button: {sel}")
                        self._sso_attempted = True
                        el.click()
                        return True
                except Exception:
                    continue
            
            logger.warning("❌ No Google SSO button found on the page")
            return False
        except Exception as e:
            logger.debug(f"Auto SSO attempt failed: {e}")
            return False

    def _check_login_status(self, skip_navigation: bool = False) -> bool:
        try:
            dashboard_url = f"{self.moodle_url.rstrip('/')}/my/"
            if self.page:
                current_url = (self.page.url or '').lower()
                if (not skip_navigation and 'login' not in current_url and not current_url.startswith(dashboard_url.lower())):
                    try:
                        # Navigate to dashboard to stabilize DOM for detection
                        self.page.goto(dashboard_url, wait_until='domcontentloaded')
                    except Exception as nav_e:
                        logger.debug(f"Nav error (playwright): {nav_e}")
                signals = self._compute_login_signals()
                logger.debug(f"Login signals: {signals} body_class={getattr(self, '_last_body_class', None)}")
                strict_logged_in = all([
                    signals['menu_present'],
                    signals['cookie_present'],
                    not signals['login_form'],
                    not signals['url_has_login'],
                    (signals['body_logged_in'] or signals['user_avatar'])
                ])
                relaxed_candidate = all([
                    signals['menu_present'],
                    signals['cookie_present'],
                    not signals['login_form'],
                    not signals['url_has_login']
                ]) and (signals['user_avatar'] or True)
                if not (strict_logged_in or relaxed_candidate) and signals['login_form']:
                    if self._attempt_auto_sso_login():
                        logger.debug("Auto SSO click issued")
                if strict_logged_in:
                    self._relaxed_success_count = 0
                    self._after_login_success_once()
                    return True
                if relaxed_candidate:
                    self._relaxed_success_count = getattr(self, '_relaxed_success_count', 0) + 1
                    if self._relaxed_success_count >= 3:
                        self._after_login_success_once(relaxed=True)
                        return True
                else:
                    self._relaxed_success_count = 0
                return False
            elif self.driver:
                current_url = self.driver.current_url.lower()
                if (not skip_navigation and 'login' not in current_url and not current_url.startswith(dashboard_url.lower())):
                    try:
                        self.driver.get(dashboard_url)
                    except Exception as nav_e:
                        logger.debug(f"Nav error (selenium): {nav_e}")
                signals = self._compute_login_signals()
                logger.debug(f"Login signals (selenium): {signals} body_class={getattr(self, '_last_body_class', None)}")
                strict_logged_in = all([
                    signals['menu_present'],
                    signals['cookie_present'],
                    not signals['login_form'],
                    not signals['url_has_login'],
                    (signals['body_logged_in'] or signals['user_avatar'])
                ])
                relaxed_candidate = all([
                    signals['menu_present'],
                    signals['cookie_present'],
                    not signals['login_form'],
                    not signals['url_has_login']
                ]) and (signals['user_avatar'] or True)
                if strict_logged_in:
                    self._relaxed_success_count = 0
                    self._after_login_success_once()
                    return True
                if relaxed_candidate:
                    self._relaxed_success_count = getattr(self, '_relaxed_success_count', 0) + 1
                    if self._relaxed_success_count >= 3:
                        self._after_login_success_once(relaxed=True)
                        return True
                else:
                    self._relaxed_success_count = 0
                return False
            return False
        except Exception as e:
            logger.debug(f"Error checking login status: {e}")
            return False
    
    def _after_login_success_once(self, relaxed: bool = False):
        """Actions to run exactly once after confirming login (strict or relaxed)."""
        if getattr(self, '_login_success_handled', False):
            return
        self._login_success_handled = True
        try:
            logger.info("✅ Login confirmed (relaxed mode)" if relaxed else "✅ Login confirmed")
            # Save cookies/session
            try:
                self._save_session()
            except Exception as e:
                logger.debug(f"Session save error: {e}")
            # Trigger callback (e.g., auto scrape) once
            if self.on_login_callback and not self._login_announced:
                self._login_announced = True
                try:
                    self.on_login_callback()
                except Exception as cb_e:
                    logger.warning(f"Login callback failed: {cb_e}")
        except Exception as e:
            logger.debug(f"After-login hook error: {e}")

    def _save_session(self):
        try:
            if self.page:
                moodle_cookies = self._get_moodle_cookies()
                with open(self.cookies_file, 'wb') as f:
                    pickle.dump(moodle_cookies, f)
                logger.info(f"💾 Session cookies snapshot saved ({len(moodle_cookies)})")
                if not moodle_cookies:
                    logger.warning("No Moodle cookies captured. If using Google SSO ensure login fully completes (Moodle dashboard loaded) before saving.")
            else:
                logger.info("💾 Session state saved (selenium profile)")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def close(self):
        """Close browser resources safely"""
        try:
            if self.page:
                try: self.page.close()
                except Exception: pass
            if self.context:
                try: self.context.close()
                except Exception: pass
            if hasattr(self, 'playwright'):
                try: self.playwright.stop()
                except Exception: pass
            if self.driver:
                try: self.driver.quit()
                except Exception: pass
            logger.info("🔒 MoodleSession browser resources closed")
        except Exception as e:
            logger.debug(f"Error during session close: {e}")
    
    # Debug utility
    def debug_login_state(self) -> Dict[str, any]:
        info = {'url': None, 'cookies': [], 'body_classes': None, 'login_form': None}
        try:
            if self.page:
                info['url'] = self.page.url
                try:
                    info['body_classes'] = self.page.eval_on_selector('body', 'el => el.className')
                except Exception:
                    pass
                info['login_form'] = self._is_login_form_present()
                info['cookies'] = [c['name'] for c in self._get_moodle_cookies()]
            elif self.driver:
                info['url'] = self.driver.current_url
                info['login_form'] = self._is_login_form_present()
                info['cookies'] = [c['name'] for c in self._get_moodle_cookies()]
        except Exception as e:
            info['error'] = str(e)
        logger.debug(f"Login debug: {info}")
        return info

class MoodleDirectScraper:
    """Main class for scraping Moodle content directly with human-like behavior"""
    
    def __init__(self, moodle_url: str = None, headless: bool = False, auto_scrape_on_login: Optional[bool] = None, auto_scrape_background: bool = True, click_delay: tuple = None, page_wait: tuple = None, typing_delay: tuple = None, google_email: str = None, google_password: str = None):
        """Create a scraper.
        auto_scrape_on_login:
          True  -> always auto-scrape right after login
          False -> never auto-scrape (you must call scrape_all_due_items manually)
          None  -> infer: auto-scrape only when headless (recommended so interactive sessions stay manual)
        auto_scrape_background: if auto-scrape enabled, run in background thread (non-blocking)
        click_delay: tuple of (min_ms, max_ms) for click delays (default: (100, 300))
        page_wait: tuple of (min_sec, max_sec) for page load waits (default: (2, 5))
        typing_delay: tuple of (min_ms, max_ms) for typing delays (default: (50, 150))
        google_email: Google email for automated login
        google_password: Google password for automated login
        """
        load_dotenv()
        self.moodle_url = moodle_url or os.getenv('MOODLE_URL')
        self.session = MoodleSession(self.moodle_url, headless, google_email, google_password)
        
        # Configure timing parameters
        if click_delay:
            self.session.click_delay = click_delay
        if page_wait:
            self.session.page_load_wait = page_wait
        if typing_delay:
            self.session.typing_delay = typing_delay
        if not self.moodle_url:
            raise ValueError("Moodle URL not provided. Set MOODLE_URL environment variable or pass moodle_url parameter.")
        # Decide auto-scrape behavior (default only in headless mode)
        if auto_scrape_on_login is None:
            resolved_auto = headless  # auto only in headless by default
        else:
            resolved_auto = bool(auto_scrape_on_login)
        self.auto_scrape_on_login = resolved_auto
        self.auto_scrape_background = auto_scrape_background and resolved_auto  # only relevant if auto enabled
        self._scrape_executed = False  # guard to avoid double scraping in a single session
        self._auto_scrape_thread: Optional[threading.Thread] = None
        # NEW: concurrency + state flags
        self._scrape_lock = threading.Lock()
        self._scrape_in_progress = False
        # Register login callback only if auto enabled
        if self.auto_scrape_on_login:
            self.session.on_login_callback = self._on_session_logged_in
        # Storage paths
        self.scraped_file = 'data/assignments_scraped.json'
        self.main_file = 'data/assignments.json'
        # In-memory cache
        self._scraped_items: List[Dict] = []
        # Duplicate thresholds
        self._fuzzy_threshold_same = 0.85
        self._fuzzy_threshold_update = 0.90
        self.debug_scrape = os.getenv('MOODLE_SCRAPE_DEBUG', '0') in ['1','true','yes','on']
        if not self.auto_scrape_on_login and headless:
            logger.info("ℹ️ Headless mode without auto-scrape: remember to call scrape_all_due_items() manually.")
        if self.auto_scrape_on_login and not headless:
            logger.info("ℹ️ Auto-scrape enabled in non-headless mode (override default).")

    # ---------------- Internal Helpers ---------------- #
    def _ensure_logged_in(self, retries: int = 5, delay: float = 1.0) -> bool:
        """Retry login detection briefly to avoid race where callback fires before signals stabilize."""
        for attempt in range(retries + 1):
            if self.session._check_login_status(skip_navigation=True):
                # One extra short settle check
                time.sleep(0.3)
                if self.session._check_login_status(skip_navigation=True):
                    return True
            if attempt < retries:
                time.sleep(delay)
        return False

    # ---------------- Scraping Orchestration ---------------- #
    def _on_session_logged_in(self):
        """Triggered automatically once after login is confirmed (if auto_scrape_on_login).
        Ensures Playwright sync API stays on original thread (no background thread) to avoid greenlet errors.
        Runs in background only when safe (e.g., selenium) and auto_scrape_background=True."""
        with self._scrape_lock:
            if self._scrape_executed or self._scrape_in_progress:
                logger.info("⚠️ Auto-scrape skipped (already executed or in progress)")
                return
            self._scrape_in_progress = True  # reserve slot early
        using_playwright = bool(getattr(self.session, 'page', None))
        # Playwright sync objects are NOT thread-safe; disable background threading if active
        if using_playwright and self.auto_scrape_background:
            logger.info("⚠️ Playwright detected – running auto scrape on main thread (background disabled to avoid greenlet thread switch error)")
            self.auto_scrape_background = False
        def _do_scrape():
            try:
                # small delay to let Moodle UI fully load after redirect
                time.sleep(1.0)
                if not self._ensure_logged_in():
                    logger.warning("⛔ Auto-scrape aborted: login not fully detected after retries")
                    return
                logger.info("🚀 Starting automatic scrape of due items...") if not self.auto_scrape_background else logger.info("🚀 (Background) Starting automatic scrape of due items...")
                self.scrape_all_due_items(auto_merge=True)
            except Exception as e:
                logger.warning(f"Automatic scrape failed: {e}")
            finally:
                with self._scrape_lock:
                    if not self._scrape_executed:
                        self._scrape_in_progress = False
        if self.auto_scrape_background and not using_playwright:
            if self._auto_scrape_thread and self._auto_scrape_thread.is_alive():
                logger.debug("Auto-scrape thread already running")
                return
            self._auto_scrape_thread = threading.Thread(target=_do_scrape, name="AutoScrapeThread", daemon=True)
            self._auto_scrape_thread.start()
            logger.info("⏳ Auto-scrape launched in background thread")
        else:
            _do_scrape()

    def scrape_all_due_items(self, auto_merge: bool = False) -> List[Dict]:
        # Concurrency + one-time execution guard
        with self._scrape_lock:
            if self._scrape_executed:
                logger.info("⏩ Scrape skipped (already executed this session)")
                return self._scraped_items
            if self._scrape_in_progress:
                logger.info("⏳ Scrape already in progress (second trigger skipped)")
                return self._scraped_items
            self._scrape_in_progress = True
        try:
            # Stabilize login (helps manual trigger right after UI shows logged in)
            if not self._ensure_logged_in():
                raise Exception("Not logged in to Moodle")
            courses = self.fetch_courses()
            
            if self.debug_scrape:
                print(f"🔍 DEBUG: Starting to iterate through {len(courses)} courses")
                for i, course in enumerate(courses, 1):
                    print(f"   {i}. {course.get('code', 'UNKNOWN')} - {course.get('name', 'Unknown')}")
                    print(f"      URL: {course.get('url', 'No URL')}")
            
            all_items: List[Dict] = []
            for i, course in enumerate(courses, 1):
                try:
                    if self.debug_scrape:
                        print(f"🔍 DEBUG: Processing course {i}/{len(courses)}: {course.get('code', 'UNKNOWN')}")
                    
                    items = self._scrape_course_due_items(course)
                    all_items.extend(items)
                    
                    if self.debug_scrape:
                        print(f"🔍 DEBUG: Course {course.get('code', 'UNKNOWN')} yielded {len(items)} items")
                        if items:
                            for item in items[:3]:  # Show first 3 items
                                print(f"      - {item.get('title', 'Unknown')} (due: {item.get('due_date', 'N/A')})")
                            if len(items) > 3:
                                print(f"      ... and {len(items) - 3} more items")
                
                except Exception as e:
                    logger.warning(f"Course scrape failed for {course.get('name')}: {e}")
                    if self.debug_scrape:
                        print(f"❌ DEBUG: Error processing course {course.get('code', 'UNKNOWN')}: {e}")
            
            if self.debug_scrape:
                print(f"🔍 DEBUG: Total items found across all courses: {len(all_items)}")
            
            # Save raw scraped list separately
            self._scraped_items = all_items
            self._save_json(self.scraped_file, all_items)
            logger.info(f"💾 Saved {len(all_items)} scraped items to {self.scraped_file}")
            if auto_merge:
                try:
                    merged, new_count, updated = self.merge_into_main()
                    logger.info(f"🔄 Merge summary: new={new_count} updated={updated} total_main={len(merged)}")
                except Exception as e:
                    logger.warning(f"Merge failed: {e}")
            # NEW: summary output
            try:
                self._print_scrape_summary(all_items)
            except Exception as e:
                logger.debug(f"Summary generation failed: {e}")
            # Mark as executed so subsequent triggers (manual or auto) won't duplicate work/summary
            with self._scrape_lock:
                self._scrape_executed = True
            return all_items
        finally:
            with self._scrape_lock:
                self._scrape_in_progress = False

    # ---------------- Summary Helper ---------------- #
    def _print_scrape_summary(self, items: List[Dict]):
        """Print/log a concise summary of scraped items.
        Includes counts per activity type and per course with titles.
        Always prints a human-readable summary to stdout regardless of log verbosity."""
        if not items:
            logger.info("📊 Scrape summary: No items found.")
            print("📊 Scrape summary: No items found.")
            return
        from collections import Counter, defaultdict
        type_counter = Counter()
        course_titles = defaultdict(list)
        course_name_map = {}
        for it in items:
            atype = (it.get('activity_type') or 'unknown').lower()
            type_counter[atype] += 1
            code = it.get('course_code') or it.get('course') or 'UNKNOWN'
            course_name_map[code] = it.get('course') or code
            course_titles[code].append(it.get('title') or it.get('raw_title') or 'Untitled')
        total_items = len(items)
        distinct_courses = len(course_titles)
        type_parts = [f"{t}:{c}" for t, c in sorted(type_counter.items(), key=lambda x: (-x[1], x[0]))]
        logger.info(f"📊 Scrape summary: {total_items} items across {distinct_courses} courses | Activity types -> " + ", ".join(type_parts))
        # Build stdout summary (always)
        print("\n📊 SCRAPE SUMMARY")
        print(f"Total: {total_items} items | Courses: {distinct_courses}")
        print("Activity types:")
        for t, c in sorted(type_counter.items(), key=lambda x: (-x[1], x[0])):
            print(f"  - {t}: {c}")
        print("Courses & Items:")
        for code, titles in sorted(course_titles.items(), key=lambda x: (-len(x[1]), x[0])):
            cname = course_name_map.get(code, code)
            # Truncate course name if too long for better readability
            display_cname = cname[:40] + "..." if len(cname) > 40 else cname
            print(f"  - {code} ({display_cname}): {len(titles)} items")
            
            # Show items in a more readable format (max 3 per line, truncate long titles)
            max_show = 8 if not self.debug_scrape else 15
            shown = titles[:max_show]
            more = len(titles) - len(shown)
            
            for i, title in enumerate(shown):
                # Truncate very long titles for readability
                display_title = title[:60] + "..." if len(title) > 60 else title
                prefix = "    " if i == 0 else "      "
                print(f"{prefix}• {display_title}")
            
            if more > 0:
                print(f"      ... and {more} more items")
            
            # Log the full version for debugging/logs
            title_list = '; '.join(titles[:15])
            if len(titles) > 15:
                title_list += f" ... (+{len(titles) - 15} more)"
            logger.info(f"  • {code}: {len(titles)} items ({cname}) -> {title_list}")

    # ---------------- Course & Activity Scraping ---------------- #
    def fetch_courses(self) -> List[Dict]:  # override placeholder with basic implementation
        if not self.session._check_login_status(skip_navigation=True):
            raise Exception("Not logged in to Moodle")
        courses: List[Dict] = []
        tried_urls = []
        course_pages = [f"{self.moodle_url.rstrip('/')}/my/courses.php", f"{self.moodle_url.rstrip('/')}/my/"]
        for dashboard in course_pages:
            tried_urls.append(dashboard)
            try:
                page = self.session.page
                driver = self.session.driver
                if page:
                    page.goto(dashboard, wait_until='domcontentloaded')
                    # Use configurable page load wait
                    min_wait, max_wait = self.session.page_load_wait
                    time.sleep(random.uniform(min_wait, max_wait))
                    anchors = []
                    sel_list = [
                        'a[href*="/course/view.php?id="]',  # generic
                        'div.card.course-card a.aalink.coursename',  # card theme primary
                        'div.card.course-card a[href*="/course/view.php?id="]',
                        '.coursebox a[href*="/course/view.php?id="]',
                        'a.course-title'
                    ]
                    seen = set()
                    for sel in sel_list:
                        try:
                            anchors.extend(page.query_selector_all(sel) or [])
                        except Exception:
                            continue
                    logger.debug(f"Course anchor candidates: {len(anchors)} (dedup pending)")
                    for a in anchors:
                        try:
                            href = (a.get_attribute('href') or '').split('#')[0]
                            if '/course/view.php?id=' not in href:
                                continue
                            if href in seen:
                                continue
                            seen.add(href)
                            # Prefer visible multiline span text
                            name = ''
                            try:
                                multiline = a.query_selector('span.multiline span[aria-hidden="true"]')
                                if multiline:
                                    name = (multiline.text_content() or '').strip()
                            except Exception:
                                pass
                            if not name:
                                name = (a.text_content() or '').strip()
                            # Clean excessive whitespace / hidden labels
                            name = re.sub(r'\s+', ' ', name)
                            name = re.sub(r'(?i)course name', '', name).strip()
                            if not name:
                                continue
                            code, cname = self._extract_course_code_name(name)
                            courses.append({'name': cname, 'code': code, 'url': href})
                        except Exception:
                            continue
                elif driver:
                    driver.get(dashboard)
                    time.sleep(2)
                    from selenium.webdriver.common.by import By
                    anchors = []
                    sel_list = [
                        'div.card.course-card a.aalink.coursename',
                        'div.card.course-card a[href*="/course/view.php?id="]',
                        'a[href*="/course/view.php?id="]',
                        '.coursebox a[href*="/course/view.php?id="]',
                        'a.course-title'
                    ]
                    for sel in sel_list:
                        try:
                            anchors.extend(driver.find_elements(By.CSS_SELECTOR, sel))
                        except Exception:
                            continue
                    logger.debug(f"(Selenium) Course anchor candidates: {len(anchors)}")
                    seen = set()
                    for a in anchors:
                        try:
                            href = (a.get_attribute('href') or '').split('#')[0]
                            if '/course/view.php?id=' not in href or href in seen:
                                continue
                            seen.add(href)
                            name = a.text.strip()
                            # Fallback: look inside multiline span if empty
                            if not name:
                                try:
                                    multiline = a.find_element(By.CSS_SELECTOR, 'span.multiline span[aria-hidden="true"]')
                                    name = multiline.text.strip()
                                except Exception:
                                    pass
                            name = re.sub(r'\s+', ' ', name)
                            name = re.sub(r'(?i)course name', '', name).strip()
                            if not name:
                                continue
                            code, cname = self._extract_course_code_name(name)
                            courses.append({'name': cname, 'code': code, 'url': href})
                        except Exception:
                            continue
            except Exception as e:
                logger.debug(f"Course fetch attempt failed for {dashboard}: {e}")
            if courses:
                break
        logger.info(f"📚 Found {len(courses)} courses (tried: {', '.join(tried_urls)})")
        if os.getenv('MOODLE_SCRAPE_DEBUG','0') in ['1','true','yes','on'] and self.session.page:
            logger.debug("Course list: " + ", ".join([c.get('code') or c.get('name') for c in courses]))
        return courses

    def _scrape_course_due_items(self, course: Dict) -> List[Dict]:
        items: List[Dict] = []
        page = self.session.page
        driver = self.session.driver
        url = course.get('url')
        if not url:
            return items
        try:
            if page:
                if self.debug_scrape:
                    print(f"🔍 DEBUG: Navigating to {course.get('code', 'UNKNOWN')} at {url}")
                
                page.goto(url, wait_until='domcontentloaded')
                # Use configurable page load wait
                min_wait, max_wait = self.session.page_load_wait
                time.sleep(random.uniform(min_wait, max_wait))
                html = page.content()
                
                if self.debug_scrape:
                    try:
                        # Save course page HTML for debugging
                        course_code = course.get('code', 'nocode').replace('/', '_')
                        snap = Path('data/moodle_session') / f"course_{course_code}_page_{int(time.time())}.html"
                        snap.parent.mkdir(exist_ok=True, parents=True)
                        with open(snap, 'w', encoding='utf-8') as f: 
                            f.write(html)
                        print(f"🔍 DEBUG: Saved course page HTML to {snap}")
                        
                        # Quick check for activities
                        if 'activity' in html.lower():
                            print(f"🔍 DEBUG: Course page contains 'activity' text")
                        else:
                            print(f"⚠️ DEBUG: Course page does NOT contain 'activity' text")
                        
                    except Exception as e:
                        print(f"⚠️ DEBUG: Could not save course HTML: {e}")
                
                items.extend(self._extract_due_items_from_html(html, course))
                
            elif driver:
                driver.get(url)
                time.sleep(random.uniform(1.5, 2.5))
                html = driver.page_source
                items.extend(self._extract_due_items_from_html(html, course))
            time.sleep(random.uniform(0.6, 1.2))
        except Exception as e:
            logger.debug(f"Activity scrape error ({course.get('code')}): {e}")
            if self.debug_scrape:
                print(f"❌ DEBUG: Exception in course scraping: {e}")
        
        if items:
            logger.info(f"  • {course.get('code', course.get('name'))}: {len(items)} items with due/open dates")
        else:
            logger.debug(f"No dated items found for course {course.get('code', course.get('name'))}")
            if self.debug_scrape:
                print(f"⚠️ DEBUG: No items found for {course.get('code', 'UNKNOWN')}")
        return items

    # ---------------- Extraction Helpers ---------------- #
    def _extract_due_items_from_html(self, html: str, course: Dict) -> List[Dict]:
        # Prefer structured parsing with BeautifulSoup if available
        if BS4_AVAILABLE:
            try:
                return self._extract_with_bs4(html, course)
            except Exception as e:
                logger.debug(f"BeautifulSoup parsing failed, falling back to regex: {e}")
        return self._extract_with_regex(html, course)

    def _extract_with_bs4(self, html: str, course: Dict) -> List[Dict]:
        results: List[Dict] = []
        soup = BeautifulSoup(html, 'html.parser')
        containers = soup.select('div.activity-grid, li.activity, [class*="modtype_"], div.activity-item, div.section li.activity')
        seen_keys = set()
        for cont in containers:
            try:
                classes = cont.get('class', [])
                modtype = None
                for c in classes:
                    if c.startswith('modtype_'):
                        modtype = c.replace('modtype_', '')
                        break
                if not modtype:
                    # try descendant with modtype_
                    mod_el = cont.select_one('[class*="modtype_"]')
                    if mod_el:
                        for c in mod_el.get('class', []):
                            if c.startswith('modtype_'):
                                modtype = c.replace('modtype_', '')
                                break
                anchor = (cont.select_one('.activityname a, .activitytitle a, a.aalink, a.activityname') or cont.find('a'))
                if not anchor:
                    continue
                link = anchor.get('href') or ''
                inst_name_el = anchor.select_one('.instancename') or anchor
                raw_title = inst_name_el.get_text(separator=' ', strip=True)
                raw_title = re.sub(r'\s+(Assignment|Quiz|URL)$', '', raw_title, flags=re.IGNORECASE)
                if not raw_title:
                    continue
                # Deduplicate early by link+title
                dedup_key = (raw_title.lower(), link.split('#')[0])
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                # Date regions (multiple fallbacks)
                date_region = cont.select_one('[data-region="activity-dates"], .activity-dates, .activity-dates-container')
                opening_date, due_date = self._extract_dates_from_region(date_region, cont)
                if not (opening_date or due_date):
                    # Fallback: fuzzy scan text for date lines
                    text_block = cont.get_text("\n", strip=True)
                    opening_date, due_date = self._fuzzy_extract_dates(text_block)
                if not (opening_date or due_date):
                    continue  # still nothing useful
                course_code = course.get('code')
                formatted = self._format_assignment_title(raw_title, course_code)
                if modtype == 'url' and re.search(r'\b(quiz|exam|test)\b', raw_title, re.IGNORECASE):
                    modtype = 'quiz_link'
                assignment = {
                    'title': formatted.get('display') or raw_title,
                    'title_normalized': formatted.get('normalized') or raw_title.lower(),
                    'raw_title': raw_title,
                    'due_date': due_date or 'No due date',
                    'opening_date': opening_date or 'No opening date',
                    'course': course.get('name'),
                    'course_code': course_code,
                    'status': 'Pending',
                    'source': 'scrape',
                    'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'activity_type': (modtype or '').lower(),
                    'origin_url': link
                }
                results.append(assignment)
            except Exception as e:
                logger.debug(f"Activity parse error: {e}")
                continue
        if self.debug_scrape:
            logger.info(f"Debug: Extracted {len(results)} candidate items before merge for course {course.get('code')}")
        return results

    def _extract_dates_from_region(self, dates_region, grid) -> Tuple[Optional[str], Optional[str]]:
        opening = None
        due = None
        if dates_region:
            for div in dates_region.select('div'):  # each date line
                text = div.get_text(separator=' ', strip=True)
                # Normalize
                text_clean = re.sub(r'\s+', ' ', text)
                m = re.match(r'(?i)(Opened|Opens|Available on)[:]?\s*(.+)', text_clean)
                if m:
                    opening_candidate = m.group(2).strip()
                    opening = self._parse_date(opening_candidate) or opening_candidate
                m2 = re.match(r'(?i)(Due|Closes|Closing date|Deadline|Until)[:]?\s*(.+)', text_clean)
                if m2:
                    due_candidate = m2.group(2).strip()
                    due = self._parse_date(due_candidate) or due_candidate
        # Look for availability window sentences in alt content
        if not (opening and due):
            alt = grid.select_one('.activity-altcontent, .activity-description')
            if alt:
                window_text = alt.get_text(separator=' ', strip=True)
                # Pattern: Available on October 30, 2024, from 9:30 AM to 11:59 PM
                w = re.search(r'Available on\s+([^,]+\s+\d{4}),?\s+from\s+\d{1,2}:\d{2}\s*[AP]M\s+to\s+\d{1,2}:\d{2}\s*[AP]M', window_text, re.IGNORECASE)
                if w:
                    date_part = w.group(1).strip()
                    parsed = self._parse_date(date_part)
                    if parsed:
                        if not opening:
                            opening = parsed
                        if not due:
                            due = parsed
        return opening, due

    def _fuzzy_extract_dates(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Fallback heuristic to find opening/due date lines in raw text."""
        opening = None
        due = None
        if not text:
            return opening, due
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for line in lines:
            low = line.lower()
            if any(k in low for k in ['due', 'deadline', 'closes', 'closing date', 'until']) and not due:
                # Extract date fragment
                frag = re.sub(r'(?i)(due|deadline|closes|closing date|until)[:\s-]*', '', line).strip()
                due = self._parse_date(frag) or frag
            if any(k in low for k in ['opens', 'opened', 'available on', 'start date']) and not opening:
                frag = re.sub(r'(?i)(opens|opened|available on|start date)[:\s-]*', '', line).strip()
                opening = self._parse_date(frag) or frag
        return opening, due

    def _extract_course_code_name(self, full_name: str) -> Tuple[str, str]:
        """Extract course code and clean name from full course title."""
        if not full_name:
            return 'UNKNOWN', 'Unknown Course'
        
        # Try to extract course code patterns like "ALGOCOM - ALGORITHMS AND COMPLEXITY (III-ACSAD)"
        # Pattern 1: CODE - NAME (SECTION)
        match = re.match(r'^([A-Z]{2,10})\s*[-–]\s*(.+?)\s*\(([^)]+)\)$', full_name.strip())
        if match:
            code, name, section = match.groups()
            return code.strip(), f"{name.strip()} ({section.strip()})"
        
        # Pattern 2: CODE - NAME
        match = re.match(r'^([A-Z]{2,10})\s*[-–]\s*(.+)$', full_name.strip())
        if match:
            code, name = match.groups()
            return code.strip(), name.strip()
        
        # Pattern 3: Look for course code at start
        match = re.match(r'^([A-Z]{2,10}[0-9]*)\b(.*)$', full_name.strip())
        if match:
            code, rest = match.groups()
            name = rest.strip(' -()').strip()
            return code.strip(), name if name else full_name
        
        # Fallback: use first word as code if it looks like one
        words = full_name.split()
        if words and len(words[0]) <= 10 and re.match(r'^[A-Z][A-Z0-9]*$', words[0]):
            return words[0], ' '.join(words[1:]) if len(words) > 1 else full_name
        
        return 'COURSE', full_name

    def _extract_with_regex(self, html: str, course: Dict) -> List[Dict]:
        results: List[Dict] = []
        # Existing li-based pattern (legacy)
        li_pattern = re.compile(r'<li[^>]*class="[^"]*activity[^"]*modtype_([a-z0-9]+)[^"]*"[\s\S]*?<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>[\s\S]*?</li>', re.IGNORECASE)
        # New div.activity-grid pattern
        div_pattern = re.compile(r'<div[^>]*class="[^"]*activity-grid[^"]*"[\s\S]*?</div>\s*</div>', re.IGNORECASE)
        blocks = []
        blocks.extend(li_pattern.finditer(html))
        # For div based, just capture raw blocks then parse per-block
        for m in li_pattern.finditer(html):
            # Already processed via iteration above (kept for structural similarity)
            pass
        # Parse li-based results first
        for m in li_pattern.finditer(html):
            try:
                modtype, link, anchor_inner = m.groups()
                title_match = re.search(r'<span[^>]*class="[^"]*instancename[^"]*"[^>]*>([\s\S]*?)</span>', anchor_inner, re.IGNORECASE)
                raw_title = self._clean_html(title_match.group(1)) if title_match else self._clean_html(anchor_inner)
                if not raw_title:
                    continue
                li_block = m.group(0)
                due_text = self._find_due_text(li_block)
                opening_date = None
                parsed_due = None
                if due_text:
                    parsed_due = self._parse_date(due_text)
                course_code = course.get('code')
                formatted = self._format_assignment_title(raw_title, course_code)
                assignment = {
                    'title': formatted.get('display') or raw_title,
                    'title_normalized': formatted.get('normalized') or raw_title.lower(),
                    'raw_title': raw_title,
                    'due_date': parsed_due or (due_text or 'No due date'),
                    'opening_date': opening_date or 'No opening date',
                    'course': course.get('name'),
                    'course_code': course_code,
                    'status': 'Pending',
                    'source': 'scrape',
                    'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'origin_url': link,
                    'activity_type': modtype.lower()
                }
                if due_text:
                    results.append(assignment)
            except Exception:
                continue
        # Parse div.activity-grid blocks if BeautifulSoup unavailable
        if not BS4_AVAILABLE:
            for dm in re.finditer(r'<div[^>]*class="[^"]*activity-grid[^"]*"[\s\S]*?</div>\s*</div>', html, re.IGNORECASE):
                block = dm.group(0)
                try:
                    # modtype
                    mod_match = re.search(r'modtype_([a-z0-9]+)', block, re.IGNORECASE)
                    modtype = mod_match.group(1) if mod_match else 'activity'
                    # link
                    link_match = re.search(r'<a[^>]*href="([^"]+)"[^>]*>\s*<span[^>]*class="[^"]*instancename', block, re.IGNORECASE)
                    if not link_match:
                        continue
                    link = link_match.group(1)
                    title_match = re.search(r'<span[^>]*class="[^"]*instancename[^"]*"[^>]*>([\s\S]*?)</span>', block, re.IGNORECASE)
                    raw_title = self._clean_html(title_match.group(1)) if title_match else ''
                    raw_title = re.sub(r'\s+(Assignment|Quiz|URL)$', '', raw_title, flags=re.IGNORECASE)
                    # dates lines
                    opening_date, due_date = None, None
                    for line in re.findall(r'<div>\s*<strong>([^<:]+):</strong>\s*([^<]+)</div>', block, re.IGNORECASE):
                        label, value = line
                        label_low = label.lower().strip()
                        value = value.strip()
                        if label_low in ['opened', 'opens', 'available on'] and not opening_date:
                            opening_date = self._parse_date(value) or value
                        elif label_low in ['due', 'closes', 'closing date', 'deadline', 'until'] and not due_date:
                            due_date = self._parse_date(value) or value
                    if not (due_date or opening_date):
                        continue
                    course_code = course.get('code')
                    formatted = self._format_assignment_title(raw_title, course_code)
                    if modtype == 'url' and re.search(r'\b(quiz|exam|test)\b', raw_title, re.IGNORECASE):
                        modtype = 'quiz_link'
                    assignment = {
                        'title': formatted.get('display') or raw_title,
                        'title_normalized': formatted.get('normalized') or raw_title.lower(),
                        'raw_title': raw_title,
                        'due_date': due_date or 'No due date',
                        'opening_date': opening_date or 'No opening date',
                        'course': course.get('name'),
                        'course_code': course_code,
                        'status': 'Pending',
                        'source': 'scrape',
                        'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'origin_url': link,
                        'activity_type': modtype.lower()
                    }
                    results.append(assignment)
                except Exception:
                    continue
        return results

    # ---------------- Formatting & Duplicate Logic (adapted from email fetcher) ---------------- #
    def _format_assignment_title(self, title: str, course_code: str) -> Dict[str, str]:
        if not title:
            return {"display": "", "normalized": ""}
        try:
            t = title.strip()
            t = re.sub(r'\s+', ' ', t)
            activity_match = re.search(r'(ACTIVITY\s+\d+)', t, re.IGNORECASE)
            display = t.title()
            normalized = t.lower()
            if activity_match and course_code:
                act = activity_match.group(1).title()
                remainder = t[activity_match.end():].strip(' -:')
                if remainder:
                    formatted_main = f"{course_code.upper()} - {act.title()} ({remainder.title()})"
                else:
                    formatted_main = f"{course_code.upper()} - {act.title()}"
                display = formatted_main
                normalized = formatted_main.lower()
            else:
                number_match = re.search(r'(\d+)', t)
                if number_match and course_code:
                    num = number_match.group(1)
                    name_part = re.sub(r'(?i)activity\s+\d+', '', t).strip(' -:')
                    if name_part:
                        display = f"{course_code.upper()} - Activity {num} ({name_part.title()})"
                        normalized = display.lower()
                    else:
                        display = f"{course_code.upper()} - Activity {num}"
                        normalized = display.lower()
            return {"display": display, "normalized": normalized}
        except Exception:
            return {"display": title, "normalized": title.lower()}

    def _normalize_title(self, title: str) -> str:
        if not title:
            return ''
        title = title.lower().strip()
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'[^\w\s-]', '', title)
        title = re.sub(r'\b(activity|assignment|task|project)\s*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*-\s*', ' ', title)
        return title.strip()

    def _fuzzy_match(self, a: str, b: str, threshold: float) -> bool:
        if not a or not b:
            return False
        a = self._normalize_title(a)
        b = self._normalize_title(b)
        if a == b:
            return True
        def bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))
        bg_a, bg_b = bigrams(a), bigrams(b)
        if not bg_a and not bg_b:
            return True
        if not bg_a or not bg_b:
            return False
        sim = len(bg_a & bg_b) / len(bg_a | bg_b)
        return sim >= threshold

    # ---------------- Date Parsing (adapted) ---------------- #
    def _parse_date(self, date_string: str) -> Optional[str]:
        if not date_string:
            return None
        try:
            ds = date_string.strip()
            date_patterns = [
                (r'(\d{4}-\d{2}-\d{2})', ['%Y-%m-%d']),
                (r'(\d{1,2}/\d{1,2}/\d{4})', ['%m/%d/%Y', '%d/%m/%Y']),
                (r'(\d{1,2}-\d{1,2}-\d{4})', ['%m-%d-%Y', '%d-%m-%Y']),
                (r'([A-Za-z]+\s+\d{1,2},\s+\d{4})', ['%B %d, %Y', '%b %d, %Y']),
                (r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})', ['%d %B %Y', '%d %b %Y']),
                (r'[A-Za-z]+,\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})', ['%d %B %Y', '%d %b %Y'])
            ]
            from datetime import datetime as _dt
            for pat, fmts in date_patterns:
                m = re.search(pat, ds)
                if m:
                    frag = m.group(1)
                    for fmt in fmts:
                        try:
                            dt = _dt.strptime(frag, fmt)
                            return dt.date().isoformat()
                        except Exception:
                            continue
            direct = ['%Y-%m-%d','%d/%m/%Y','%m/%d/%Y','%d-%m-%Y','%m-%d-%Y','%B %d, %Y','%b %d, %Y','%d %B %Y','%d %b %Y']
            for fmt in direct:
                try:
                    dt = _dt.strptime(ds, fmt)
                    return dt.date().isoformat()
                except Exception:
                    continue
        except Exception:
            pass
        return date_string

    # ---------------- Persistence & Merge ---------------- #
    def _save_json(self, path: str, data: List[Dict]):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_json(self, path: str) -> List[Dict]:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def merge_into_main(self) -> Tuple[List[Dict], int, int]:
        existing = self._load_json(self.main_file)
        scraped = self._scraped_items or self._load_json(self.scraped_file)
        new_count = 0
        updated = 0
        index = {}
        for a in existing:
            key = (a.get('title_normalized') or a.get('title','')).lower(), a.get('course_code','')
            index[key] = a
        for item in scraped:
            key = (item.get('title_normalized') or item.get('title','')).lower(), item.get('course_code','')
            current = index.get(key)
            if not current:
                existing.append(item)
                index[key] = item
                new_count += 1
            else:
                changed = False
                # Update due date if changed
                if item.get('due_date') and item.get('due_date') != current.get('due_date'):
                    current['due_date'] = item['due_date']
                    changed = True
                # Add opening date if current lacks it or has placeholder
                if item.get('opening_date') and (not current.get('opening_date') or current.get('opening_date') in [None, 'No opening date']):
                    current['opening_date'] = item['opening_date']
                    changed = True
                # Merge source label if not already present
                if current.get('source') == 'email' and 'scrape' not in current.get('source',''):
                    current['source'] = 'email+scrape'
                if changed:
                    current['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    updated += 1
        self._save_json(self.main_file, existing)
        return existing, new_count, updated

    # ---------------- Public Convenience ---------------- #
    def manual_scrape(self, merge: bool = True):
        items = self.scrape_all_due_items(auto_merge=merge)
        return items

    def check_login_status(self) -> Dict[str, any]:
        """Lightweight status check used by run_fetcher.
        Starts browser if needed and evaluates current login signals."""
        if not (self.session.page or self.session.driver):
            started = self.session.start_browser()
            if not started:
                return {
                    'logged_in': False,
                    'error': 'Could not start browser',
                    'login_url': f"{self.moodle_url.rstrip('/')}/login/index.php",
                    'moodle_url': self.moodle_url,
                    'browser_ready': False
                }
        is_logged_in = self.session._check_login_status(skip_navigation=True)
        return {
            'logged_in': is_logged_in,
            'login_url': f"{self.moodle_url.rstrip('/')}/login/index.php",
            'moodle_url': self.moodle_url,
            'browser_ready': True
        }

    def interactive_login(self, timeout_minutes: int = 10) -> bool:
        """Open login page and wait for manual (or automated) completion."""
        if not self.session.start_browser():
            return False
        
        # CRITICAL: Check if already logged in FIRST before attempting any login flow
        if self.session._check_login_status(skip_navigation=True):
            logger.info("✅ Already logged in with valid session, skipping login flow")
            return True
        
        if not self.session.open_login_page():
            return False
        
        # Use automated login if credentials are provided
        if self.session.google_email and self.session.google_password:
            return self.session.automated_google_login(timeout_minutes)
        else:
            return self.session.wait_for_user_login(timeout_minutes)

    def close(self):
        """Close underlying session/browser resources (compatibility with run_fetcher)."""
        try:
            self.session.close()
        except Exception:
            pass
