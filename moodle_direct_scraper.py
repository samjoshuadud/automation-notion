"""
Moodle Direct Scraper - Human-like browser automation for Moodle scraping
"""

import os
import sys
import logging
import time
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
    
    def __init__(self, moodle_url: str = None, headless: bool = False):
        load_dotenv()
        self.moodle_url = moodle_url or os.getenv('MOODLE_URL', 'https://your-moodle-site.com')
        self.headless = headless
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

    def _attempt_auto_sso_login(self) -> bool:
        """Attempt automatic Google SSO click if login form is present.
        Returns True if a click was issued (then we wait for redirects)."""
        if getattr(self, '_sso_attempted', False):
            return False
        if not self.page:
            return False
        try:
            # Candidate selectors (provided snippet + fallbacks)
            selectors = [
                'a.login-identityprovider-btn[href*="oauth2/login.php"][href*="id=1"]',
                'a.login-identityprovider-btn[href*="oauth2/login.php"]',
                'a[href*="auth/oauth2/login.php"][class*="identityprovider"]',
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
                    if any(k in text_content for k in ['university', 'google', 'makati']):
                        logger.info(f"⚡ Auto-clicking SSO button via selector: {sel}")
                        self._sso_attempted = True
                        el.click()
                        return True
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
                        self.page.goto(dashboard_url, wait_until='domcontentloaded', timeout=10000)
                    except Exception as nav_e:
                        logger.debug(f"Dashboard nav error: {nav_e}")
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
                # Auto SSO if on login page, have Moodle cookie OR Google cookies (heuristic) and not logged
                if not (strict_logged_in or relaxed_candidate) and signals['login_form']:
                    if self._attempt_auto_sso_login():
                        logger.info("🔄 Waiting for SSO redirect...")
                        time.sleep(2)
                        return False  # next iteration will re-evaluate
                if strict_logged_in:
                    self._relaxed_success_count = 0
                    if not getattr(self, '_first_login_snapshot', False):
                        self._capture_debug_snapshot('strict_detect')
                        self._first_login_snapshot = True
                    return True
                if relaxed_candidate:
                    self._relaxed_success_count = getattr(self, '_relaxed_success_count', 0) + 1
                    if self._relaxed_success_count >= 3:
                        if not getattr(self, '_first_login_snapshot', False):
                            self._capture_debug_snapshot('relaxed_detect')
                            self._first_login_snapshot = True
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
                        logger.debug(f"Dashboard nav error (selenium): {nav_e}")
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
                    return True
                if relaxed_candidate:
                    self._relaxed_success_count = getattr(self, '_relaxed_success_count', 0) + 1
                    if self._relaxed_success_count >= 3:
                        return True
                else:
                    self._relaxed_success_count = 0
                return False
            return False
        except Exception as e:
            logger.debug(f"Error checking login status: {e}")
            return False
    
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
    
    def __init__(self, moodle_url: str = None, headless: bool = False):
        load_dotenv()
        self.moodle_url = moodle_url or os.getenv('MOODLE_URL')
        self.session = MoodleSession(self.moodle_url, headless)
        if not self.moodle_url:
            raise ValueError("Moodle URL not provided. Set MOODLE_URL environment variable or pass moodle_url parameter.")
    
    def check_login_status(self) -> Dict[str, any]:
        if not (self.session.page or self.session.driver):
            browser_started = self.session.start_browser()
            if not browser_started:
                return {
                    'logged_in': False,
                    'error': 'Could not start browser',
                    'login_url': f"{self.moodle_url.rstrip('/')}/login/index.php",
                    'moodle_url': self.moodle_url
                }
        is_logged_in = self.session._check_login_status(skip_navigation=True)
        return {
            'logged_in': is_logged_in,
            'login_url': f"{self.moodle_url.rstrip('/')}/login/index.php",
            'moodle_url': self.moodle_url,
            'browser_ready': True
        }
    
    def interactive_login(self, timeout_minutes: int = 10) -> bool:
        if not self.session.start_browser():
            return False
        if not self.session.open_login_page():
            return False
        return self.session.wait_for_user_login(timeout_minutes)
    
    def fetch_courses(self) -> List[Dict]:
        if not self.session._check_login_status(skip_navigation=True):
            raise Exception("Not logged in to Moodle")
        # TODO: implement actual scraping
        return []
    
    def fetch_assignments(self) -> List[Dict]:
        if not self.session._check_login_status(skip_navigation=True):
            raise Exception("Not logged in to Moodle")
        # TODO: implement actual scraping
        return []
    
    def fetch_forum_posts(self) -> List[Dict]:
        if not self.session._check_login_status(skip_navigation=True):
            raise Exception("Not logged in to Moodle")
        # TODO: implement actual scraping
        return []
    
    def close(self):
        self.session.close()

__all__ = ["MoodleDirectScraper", "MoodleSession"]
