from config import ADMIN_URL
from pages.base_page import BasePage


class AdminAgentPage(BasePage):

    def complete(self, user):
        """Find the agent -> Transfer now -> Onboard Agent -> check status is Active."""
        self.open_agent(user["email"])
        self.approve_license_transfer()
        self.onboard_agent()
        self.check_status_active()

    def open_agent(self, email):
        """Agents > All Agents > search by email > open the agent."""
        self.page.goto(ADMIN_URL + "/agents/all-agents?page=1")
        self.fill(self.input("search"), email)
        self.click(self.page.get_by_text(email, exact=True).first)
        self.page.wait_for_url("**/agents/all-agents/detail/**")
        self.wait_visible(self.button("Approve Agent"))
        print("Opened agent:", self.page.url)

    def approve_license_transfer(self):
        """Transfer now -> Transfer -> Approve Transfer."""
        self.click(self.button("Transfer now"))
        self.click(self.page.get_by_role("dialog").get_by_role("button", name="Transfer", exact=True))
        self.click(self.page.get_by_role("button", name="Approve Transfer"))
        self.wait_visible(self.page.get_by_role("dialog").get_by_text("Transferred", exact=True))
        print("License transfer approved")
        self.page.reload()                          # closes the popup and refreshes the agent
        self.wait_visible(self.button("Approve Agent"))

    def onboard_agent(self):
        """Approve Agent -> Onboard Agent -> Confirm."""
        self.click(self.button("Approve Agent"))
        self.click(self.page.get_by_role("button", name="Onboard Agent"))
        confirm_popup = self.page.get_by_role("dialog").filter(has_text="Are you sure you want to approve")
        self.click(confirm_popup.get_by_role("button", name="Confirm"))
        self.page.wait_for_timeout(3000)
        print("Onboard Agent confirmed")

    def check_status_active(self):
        self.page.reload()
        status = self.page.get_by_text("Active", exact=True).first
        self.wait_visible(status)
        print("Agent status:", status.inner_text())
        assert status.inner_text().strip() == "Active", "Agent is NOT active"
