from dummy_data import ADDRESS, TAX
from pages.base_page import BasePage


class TaxInformationPage(BasePage):

    def complete(self, user):
        self.wait_for_page("/tax-information/step-1")
        self.click_next()

        self.wait_for_page("/tax-information/step-2")

        def fill_w9_form():
            self.choose_radio("Individual")
            self.fill(self.input("tax_information.identity"), user["full_name"])
            ssn = self.input("tax_information.taxpayer_id")
            self.fill(ssn, "")
            self.type_slowly(ssn, TAX["ssn"])
            self.select_dropdown("Tax Classification", TAX["classification"])
            self.fill(self.input("tax_information.address_line_1"), ADDRESS["line1"])
            self.fill(self.input("tax_information.city"), ADDRESS["city"])
            self.select_dropdown("State", ADDRESS["state"])
            self.fill(self.input("tax_information.zipcode"), ADDRESS["zip"])
        self.fill_and_next(fill_w9_form)

        self.wait_for_page("/tax-information/step-3")
        self.click(self.button("Continue: Sign Your ICA"))
        self.confirm_popup_if_present()
