from pages.base_page import BasePage


class TransferLicensePage(BasePage):

    def complete(self):
        self.wait_for_page("/transfer-license")
        self.click(self.page.get_by_text("I confirm that I have transferred my", exact=False).first)
        self.confirm_popup()
        self.wait_visible(self.page.get_by_text("Pending Broker Review"))
        print("Done -> Pending Broker Review")
