from config import ADMIN_EMAIL, ADMIN_OTP, ADMIN_URL, NAV_TIMEOUT
from pages.base_page import BasePage


class AdminLoginPage(BasePage):

    def login(self, email=ADMIN_EMAIL, otp=ADMIN_OTP):
        self.page.goto(ADMIN_URL + "/login")
        self.page.wait_for_timeout(3000)          # let the login form load
        self.fill(self.input("email"), email)
        self.click(self.button("Continue"))
        self.fill(self.input("otp"), otp)
        self.click(self.button("Log In"))
        self.page.wait_for_url(lambda url: "/login" not in url, timeout=NAV_TIMEOUT)
        print("Admin logged in:", self.page.url)
