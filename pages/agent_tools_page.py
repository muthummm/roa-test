from pages.base_page import BasePage


class AgentToolsPage(BasePage):

    def complete(self):
        self.wait_for_page("/customize-agent-tools")

        # "Stay Connected" popup
        self.click_if_present(self.button("Agree and Continue"), 15_000)

        # pick the free CRM tool
        if not self.page.get_by_text("Your Selected CRM Tool").is_visible():
            self.click(self.button("Add at No Additional Cost").first)
            self.wait_visible(self.page.get_by_text("Your Selected CRM Tool"))

        self.click(self.button("Continue: Pay & Checkout"))
        self.confirm_popup_if_present()
