from config import NAV_TIMEOUT, PASSWORD
from pages.base_page import BasePage


class LoginPage(BasePage):

    def login(self, email, password=PASSWORD):
        """Log in an existing user (useful for testing a single step later)."""
        self.open("/login")
        self.fill(self.input("email"), email)
        self.fill(self.page.locator("input[type='password']"), password)
        self.click(self.page.locator("button[type='submit']"))
        self.page.wait_for_url(lambda url: "/agent-onboarding/" in url, timeout=NAV_TIMEOUT)
