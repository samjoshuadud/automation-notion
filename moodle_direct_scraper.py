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
        self.on_login_callback = None  # callback to trigger once when login confirmed
        self._login_announced = False

    
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
    
    def __init__(self, moodle_url: str = None, headless: bool = False, auto_scrape_on_login: Optional[bool] = None, auto_scrape_background: bool = True):
        """Create a scraper.
        auto_scrape_on_login:
          True  -> always auto-scrape right after login
          False -> never auto-scrape (you must call scrape_all_due_items manually)
          None  -> infer: auto-scrape only when headless (recommended so interactive sessions stay manual)
        auto_scrape_background: if auto-scrape enabled, run in background thread (non-blocking)
        """
        load_dotenv()
        self.moodle_url = moodle_url or os.getenv('MOODLE_URL')
        self.session = MoodleSession(self.moodle_url, headless)
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
                    time.sleep(random.uniform(0.8, 1.6))
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
                time.sleep(random.uniform(1.0, 2.0))
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
        """Open login page and wait for manual (or auto-SSO) completion."""
        if not self.session.start_browser():
            return False
        if not self.session.open_login_page():
            return False
        return self.session.wait_for_user_login(timeout_minutes)

    def close(self):
        """Close underlying session/browser resources (compatibility with run_fetcher)."""
        try:
            self.session.close()
        except Exception:
            pass
