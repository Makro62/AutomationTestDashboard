from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

class LoginKeywords:
    def __init__(self):
        self.driver = None

    def open_browser(self):
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
        self.driver.get("https://www.saucedemo.com")
        self.driver.maximize_window()

    def login_with_credentials(self, username, password):
        self.driver.find_element(By.ID, "user-name").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "login-button").click()
        time.sleep(2)

    def verify_login_success(self):
        assert "inventory.html" in self.driver.current_url

    def verify_login_failed(self):
        error_msg = self.driver.find_element(By.XPATH, "//h3[@data-test='error']").text
        assert "Username and password do not match any user in this service" in error_msg

    def close_browser(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

