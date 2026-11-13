# ============================================================
# REGRESSION TEST CASES
# Run all:   pytest tests/regression.py
# Run one:   pytest tests/regression.py -k test_01_onboarding
#
# Add the next test case at the bottom as:  def test_02_<name>(page):
# ============================================================
from pages.admin_agent_page import AdminAgentPage
from pages.admin_login_page import AdminLoginPage
from pages.agent_tools_page import AgentToolsPage
from pages.payment_page import PaymentPage
from pages.roa_application_page import RoaApplicationPage
from pages.roa_email_page import RoaEmailPage
from pages.sign_ica_page import SignIcaPage
from pages.signup_page import SignUpPage
from pages.tax_information_page import TaxInformationPage
from pages.transfer_license_page import TransferLicensePage


# ------------------------------------------------------------
# Test case 1: full agent onboarding (staging)
#   Part 1 - agent side:  sign up ... transfer license
#   Part 2 - admin side:  transfer now -> onboard agent -> status Active
# ------------------------------------------------------------
def test_01_onboarding(page):
    # ---------- Part 1: agent onboarding ----------
    user = SignUpPage(page).create_new_user()
    RoaApplicationPage(page).complete(user)
    TaxInformationPage(page).complete(user)
    SignIcaPage(page).complete(user)
    AgentToolsPage(page).complete()
    PaymentPage(page).complete(user)
    RoaEmailPage(page).complete(user)
    TransferLicensePage(page).complete()
    # ---------- Part 2: admin approves the same agent ----------
    AdminLoginPage(page).login()
    AdminAgentPage(page).complete(user)
