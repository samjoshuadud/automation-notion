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
        self.session_dir = Path('data/moodle_session')
        self.session_dir.mkdir(exist_ok=True, parents=True)
        
        self.cookies_file = self.session_dir / 'cookies.pkl'
        self.user_data_dir = self.session_dir / 'browser_data'
        
        self.browser = None
        self.context = None
        self.page = None
        self.driver = None  # For selenium fallback
        
        # Human-like behavior settings
        self.typing_delay = (50, 150)  # Random delay between keystrokes (ms)
        self.click_delay = (100, 300)  # Random delay before/after clicks (ms)
        self.page_load_wait = (2, 5)   # Random wait after page loads (seconds)
    
    def _random_delay(self, min_ms: int, max_ms: int):
        """Add random human-like delay"""
        import random
        delay = random.randint(min_ms, max_ms) / 1000.0
        time.sleep(delay)
    
    def _init_playwright_browser(self) -> bool:
        """Initialize Playwright browser with human-like settings"""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        try:
            self.playwright = sync_playwright().start()
            
            # Use persistent context to maintain sessions
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                viewport={'width': 1366, 'height': 768},  # Common resolution
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                # Human-like browser settings
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-first-run',
                    '--disable-extensions-except',
                    '--disable-plugins-discovery',
                    '--no-sandbox'
                ]
            )
            
            self.page = self.context.new_page()
            
            # Set realistic properties to avoid detection
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            logger.info("✅ Playwright browser initialized successfully")
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
                options.add_argument('--headless')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Selenium browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            return False
    
    def start_browser(self) -> bool:
        """Start browser session with user interaction capability"""
        # Try Playwright first, then Selenium
        if self._init_playwright_browser():
            logger.info("🌐 Using Playwright for browser automation")
            return True
        elif self._init_selenium_browser():
            logger.info("🌐 Using Selenium for browser automation")
            return True
        else:
            logger.error("❌ No web automation framework available. Please install playwright or selenium.")
            return False
    
    def open_login_page(self) -> bool:
        """Open Moodle login page for user interaction"""
        try:
            login_url = f"{self.moodle_url.rstrip('/')}/login/index.php"
            
            if self.page:  # Playwright
                logger.info(f"🔗 Opening Moodle login page: {login_url}")
                self.page.goto(login_url, wait_until='networkidle')
                self._random_delay(1000, 3000)  # Human-like delay
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
        logger.info("💡 Please login manually in the browser window")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                if self._check_login_status():
                    logger.info("✅ Login detected! User is now logged in")
                    self._save_session()
                    return True
                
                # Check every 2 seconds
                time.sleep(2)
                
            except Exception as e:
                logger.debug(f"Error during login check: {e}")
                time.sleep(2)
        
        logger.warning(f"⏰ Login timeout after {timeout_minutes} minutes")
        return False
    
    def _check_login_status(self) -> bool:
        """Check if user is currently logged in"""
        try:
            # Navigate to dashboard to check login status
            dashboard_url = f"{self.moodle_url.rstrip('/')}/my/"
            
            if self.page:  # Playwright
                current_url = self.page.url
                if 'login' not in current_url.lower():
                    # Try to access dashboard
                    self.page.goto(dashboard_url, wait_until='domcontentloaded', timeout=5000)
                
                # Check for login indicators
                login_indicators = [
                    '.usermenu',
                    '.dashboard-card-deck', 
                    'a[href*="logout"]',
                    '.coursebox',
                    '.block_myoverview'
                ]
                
                for indicator in login_indicators:
                    try:
                        if self.page.query_selector(indicator):
                            return True
                    except:
                        continue
                        
                # Check if we're on login page (negative indicator)
                if 'login' in self.page.url.lower():
                    return False
                    
                # Check for login form (negative indicator)
                login_form = self.page.query_selector('#login, .loginform, form[action*="login"]')
                return login_form is None
            
            elif self.driver:  # Selenium
                current_url = self.driver.current_url
                if 'login' not in current_url.lower():
                    self.driver.get(dashboard_url)
                
                # Check for login indicators
                login_indicators = [
                    (By.CLASS_NAME, 'usermenu'),
                    (By.CLASS_NAME, 'dashboard-card-deck'),
                    (By.PARTIAL_LINK_TEXT, 'logout'),
                    (By.CLASS_NAME, 'coursebox')
                ]
                
                for by, value in login_indicators:
                    try:
                        element = self.driver.find_element(by, value)
                        if element:
                            return True
                    except:
                        continue
                
                # Check if we're on login page
                return 'login' not in self.driver.current_url.lower()
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking login status: {e}")
            return False
    
    def _save_session(self):
        """Save current session"""
        try:
            # The persistent context will automatically save cookies and session data
            logger.info("💾 Session saved successfully")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def is_logged_in(self) -> bool:
        """Public method to check login status"""
        if not (self.page or self.driver):
            return False
        return self._check_login_status()
    
    def close(self):
        """Close browser and clean up"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
            if self.driver:
                self.driver.quit()
            logger.info("🔒 Browser session closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")


class MoodleDirectScraper:
    """Main class for scraping Moodle content directly with human-like behavior"""
    
    def __init__(self, moodle_url: str = None, headless: bool = False):
        load_dotenv()  # Load environment variables
        self.moodle_url = moodle_url or os.getenv('MOODLE_URL')
        self.session = MoodleSession(self.moodle_url, headless)
        
        if not self.moodle_url:
            raise ValueError("Moodle URL not provided. Set MOODLE_URL environment variable or pass moodle_url parameter.")
    
    def check_login_status(self) -> Dict[str, any]:
        """Check if user is logged in and return status info"""
        # Start browser if not already started
        if not (self.session.page or self.session.driver):
            browser_started = self.session.start_browser()
            if not browser_started:
                return {
                    'logged_in': False,
                    'error': 'Could not start browser',
                    'login_url': f"{self.moodle_url.rstrip('/')}/login/index.php",
                    'moodle_url': self.moodle_url
                }
        
        # Check login status
        is_logged_in = self.session.is_logged_in()
        
        return {
            'logged_in': is_logged_in,
            'login_url': f"{self.moodle_url.rstrip('/')}/login/index.php",
            'moodle_url': self.moodle_url,
            'browser_ready': True
        }
    
    def interactive_login(self, timeout_minutes: int = 10) -> bool:
        """Start interactive login process"""
        logger.info("🚀 Starting interactive Moodle login process")
        
        # Start browser
        if not self.session.start_browser():
            logger.error("❌ Failed to start browser")
            return False
        
        # Open login page
        if not self.session.open_login_page():
            logger.error("❌ Failed to open login page")
            return False
        
        # Wait for user to login
        return self.session.wait_for_user_login(timeout_minutes)
    
    def fetch_courses(self) -> List[Dict]:
        """Fetch enrolled courses (placeholder - will implement later)"""
        if not self.session.is_logged_in():
            raise Exception("Not logged in to Moodle")
        
        logger.info("📚 Fetching enrolled courses...")
        # TODO: Implement course fetching in next step
        return []
    
    def fetch_assignments(self) -> List[Dict]:
        """Fetch assignments from all courses (placeholder - will implement later)"""
        if not self.session.is_logged_in():
            raise Exception("Not logged in to Moodle")
        
        logger.info("📝 Fetching assignments...")
        # TODO: Implement assignment fetching in next step
        return []
    
    def fetch_forum_posts(self) -> List[Dict]:
        """Fetch forum posts from all courses (placeholder - will implement later)"""
        if not self.session.is_logged_in():
            raise Exception("Not logged in to Moodle")
        
        logger.info("💬 Fetching forum posts...")
        # TODO: Implement forum post fetching in next step
        return []
    
    def close(self):
        """Close the scraper and browser session"""
        self.session.close()
