from config import NAV_TIMEOUT, SLOW_TIMEOUT
from pages.base_page import BasePage


class RoaEmailPage(BasePage):

    def complete(self, user):
        self.wait_for_page("/setup-roa-email/step-1", timeout=SLOW_TIMEOUT)
        self.choose_suggested_email()

        # verify forwarding email with OTP
        self.fill(self.input("forwarding_email"), user["email"])
        self.click(self.button("Send code"))
        self.enter_otp()
        self.wait_visible(self.page.get_by_text("Forwarding email verified successfully"))

        if not self.page.locator("input[type='checkbox']").last.is_checked():
            self.click(self.page.get_by_text("I acknowledge that my Realty of America email", exact=False))

        # Next + confirm popup (the email dropdown sometimes resets -> pick again)
        old_url = self.page.url
        for attempt in range(1, 4):
            self.click(self.next_button())
            try:
                self.confirm_popup(timeout=8_000)
                break
            except Exception:
                print(f"ROA email not accepted (attempt {attempt}), selecting again")
                self.choose_suggested_email()
                self.page.wait_for_timeout(1000)
        else:
            raise AssertionError("Could not submit ROA email")
        self.wait_for_url_change(old_url)

        self.wait_for_page("/setup-roa-email/step-2")
        self.click(self.button("Continue: Transfer License"), NAV_TIMEOUT)
        self.confirm_popup_if_present()

    def choose_suggested_email(self):
        self.select_first_option("Suggested ROA Email Address", close_after=False)
        self.wait_visible(self.page.get_by_text("This email address is available!"))
