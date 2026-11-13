from config import PASSWORD
from dummy_data import PRIMARY_STATE, new_user
from pages.base_page import BasePage


class SignUpPage(BasePage):

    def sign_up(self, user):
        # Step 1 - email + OTP
        self.open("/login")
        self.click(self.page.locator("//a[@href='/sign-up']"))
        self.fill(self.input("email"), user["email"])
        self.click(self.page.locator("//button[@type='submit' and normalize-space()='Get started']"))
        self.enter_otp()
        self.click(self.page.locator("//button[@type='button' and normalize-space()='Continue']"))

        # Step 2 - account details
        self.fill(self.input("first_name"), user["first_name"])
        self.fill(self.input("last_name"), user["last_name"])
        self.fill(self.input("phone_number"), user["phone_number"])
        self.select_dropdown("Primary State", PRIMARY_STATE)
        self.fill(self.page.locator("input[name='password'][type='password']"), PASSWORD)
        self.fill(self.page.locator("input[name='confirm_password'][type='password']"), PASSWORD)
        self.click(self.page.locator("//button[@type='submit' and normalize-space()='Get started']"))

    def create_new_user(self):
        """Sign up a new user. If the email/phone is already used, try the next one (max 5)."""
        for attempt in range(1, 6):
            user = new_user()
            print("User:", user["full_name"], "|", user["email"], "|", user["phone_number"])
            self.sign_up(user)
            try:
                self.page.wait_for_url("**/roa-application/about-yourself**", timeout=45_000)
                return user
            except Exception:
                print(f"Sign-up failed for {user['email']} (attempt {attempt}), trying next user")
                self.page.context.clear_cookies()
        raise AssertionError("Sign-up failed 5 times")
