import uuid

from config import DEFAULT_TIMEOUT
from dummy_data import ADDRESS, BOARDS, DATE_OF_BIRTH, EMERGENCY_CONTACT, LICENSE, PROFESSIONAL
from pages.base_page import BasePage


class RoaApplicationPage(BasePage):

    def complete(self, user):
        """Fill every page of the ROA Application, in order."""
        self.about_yourself(user)
        self.residential_address()
        self.emergency_contact()
        self.answer_radio("/active-license", "Yes")
        self.answer_radio("/license-status", "I hold an active license")
        self.answer_radio("/licensed-in-multiple-states", "No")
        self.license_details()
        self.real_estate_boards()
        self.formal_actions()
        self.professional_experience()
        self.sponsoring_agent()
        self.answer_radio("/part-of-team", "No")
        self.success_page()

    def about_yourself(self, user):
        self.wait_for_page("/roa-application/about-yourself")
        # wait until the form has loaded the saved First Name / Phone
        self.page.wait_for_function(
            """() => {
                const fn = document.querySelector("input[name='first_name']");
                const ph = document.querySelector("input[name='phone_number']");
                return fn && fn.value.trim() !== '' && ph && ph.value.trim() !== '';
            }""",
            timeout=DEFAULT_TIMEOUT,
        )

        def fill_form():
            self.fill(self.input("preferred_name"), user["full_name"])
            self.click(self.page.locator("input[placeholder='MM/DD/YYYY']"))
            self.click(self.page.locator(f"div[role='option'][aria-label='{DATE_OF_BIRTH}']"))
        self.fill_and_next(fill_form)

    def residential_address(self):
        self.wait_for_page("/your-residential-address")

        def fill_form():
            self.fill(self.input("address_line_1"), ADDRESS["line1"])
            self.fill(self.input("city"), ADDRESS["city"])
            self.select_dropdown("State", ADDRESS["state"])
            self.fill(self.input("zipcode"), ADDRESS["zip"])
        self.fill_and_next(fill_form)

    def emergency_contact(self):
        self.wait_for_page("/your-emergency-contact")

        def fill_form():
            self.fill(self.input("ec_name"), EMERGENCY_CONTACT["name"])
            self.fill(self.input("ec_phone_number"), EMERGENCY_CONTACT["phone"])
            self.select_first_option("Relationship", close_after=False)
            self.fill(self.input("ec_email"), EMERGENCY_CONTACT["email"])
        self.fill_and_next(fill_form)

    def answer_radio(self, path, answer):
        """Pages with one question: pick the answer and click Next."""
        self.wait_for_page(path)
        self.fill_and_next(lambda: self.choose_radio(answer))

    def license_details(self):
        self.wait_for_page("/licensed-details")
        license_number = f"TEST-{uuid.uuid4().hex[:12].upper()}"
        print("License number:", license_number)

        def fill_form():
            self.select_dropdown("Primary State", LICENSE["state"])
            self.select_dropdown("What type of license is it?", LICENSE["type"])
            self.fill(self.input("licenses.0.license_no"), license_number)
            dates = self.page.locator("input[placeholder='MM/DD/YYYY']")
            self.pick_date(dates.nth(0), LICENSE["expiry_days_from_today"])
            self.pick_date(dates.nth(1), LICENSE["transfer_days_from_today"])
        self.fill_and_next(fill_form)

    def real_estate_boards(self):
        self.wait_for_page("/real-estate-boards")

        def fill_form():
            self.select_dropdown_containing("Real Estate Boards / Associations", BOARDS["board"])
            self.select_dropdown_containing("Multiple Listing Service (MLS)", BOARDS["mls"])
        self.fill_and_next(fill_form)

    def formal_actions(self):
        self.wait_for_page("/formal-actions")

        def fill_form():                       # answer "No" to every question
            no_answers = self.page.locator("//label[.//p[normalize-space()='No']]")
            self.wait_visible(no_answers.first)
            for i in range(no_answers.count()):
                self.click(no_answers.nth(i))
        self.fill_and_next(fill_form)

    def professional_experience(self):
        self.wait_for_page("/professional-experience")

        def fill_form():
            self.select_dropdown("How many transactions have you closed", PROFESSIONAL["transactions_36m"])
            self.select_dropdown("Select Transaction Count", PROFESSIONAL["transaction_count"])
            self.select_dropdown("What is your production volume", PROFESSIONAL["volume_12m"])
            self.select_dropdown("What type of transactions", PROFESSIONAL["transaction_type"], close_after=True)
            self.fill(self.input("nrds_id"), PROFESSIONAL["nrds_id"])
            self.fill(self.input("affiliated_brokerage"), PROFESSIONAL["brokerage"])
        self.fill_and_next(fill_form)

    def sponsoring_agent(self):
        """Continue without a sponsor (two confirm popups)."""
        self.wait_for_page("/sponsoring-agent")
        self.click_if_present(self.page.get_by_role("dialog").get_by_role("button", name="Close"), 8_000)

        self.click(self.next_button())
        self.click(self.page.get_by_text("I acknowledge that I am choosing not to name a sponsor."))
        self.confirm_popup()
        self.wait_visible(self.page.get_by_text("No Sponsor Selected").first)

        self.click(self.next_button())
        self.click(self.page.get_by_text("I acknowledge that I did not select any sponsor"))
        old_url = self.page.url
        self.confirm_popup()
        self.wait_for_url_change(old_url)

    def success_page(self):
        self.wait_for_page("/roa-application/success")
        self.click(self.button("Continue: Tax Information"))
        self.confirm_popup()
