from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class LoginKeywords:
    """Robot Framework library for login automation tests."""
    
    ROBOT_LIBRARY_SCOPE = 'SUITE'
    
    def __init__(self, timeout=30):
        self.driver = None
        self.timeout = timeout
        self.wait = None

    def open_browser(self, url="https://www.saucedemo.com"):
        """Open browser and navigate to the specified URL.
        
        Args:
            url: The URL to navigate to (default: https://www.saucedemo.com)
        """
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-infobars')
        options.add_argument('--remote-debugging-port=9222')

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.get(url)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, self.timeout)

    def login_with_credentials(self, username, password):
        """Login with the provided username and password.
        
        Args:
            username: The username to use for login
            password: The password to use for login
        """
        self.driver.find_element(By.ID, "user-name").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "login-button").click()
        time.sleep(2)

    def verify_login_success(self):
        """Verify that login was successful by checking current URL."""
        assert "inventory.html" in self.driver.current_url, \
            f"Expected to be on inventory page, but got: {self.driver.current_url}"

    def verify_login_failed(self):
        """Verify that login failed by checking error message."""
        error_msg = self.driver.find_element(
            By.XPATH, 
            "//h3[@data-test='error']"
        ).text
        assert "Username and password do not match any user in this service" in error_msg, \
            f"Expected error message not found. Got: {error_msg}"

    def close_browser(self):
        """Close the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None

