# ============================================================
# SETTINGS - change website URL, wait times, OTP, password here
# ============================================================
import os

BASE_URL = "https://roa-onboarding-staging.vercel.app"

# Run without a browser window:  $env:HEADLESS="1"; pytest
HEADLESS = os.getenv("HEADLESS", "0") == "1"

# Wait times in milliseconds (1000 = 1 second)
DEFAULT_TIMEOUT = 40_000      # wait for an element to be visible
NAV_TIMEOUT = 60_000          # wait for the next page to open
SLOW_TIMEOUT = 90_000         # payment / e-sign

OTP = "112244"
PASSWORD = "1999@#$onboard"
EMAIL_DOMAIN = "mailinator.com"

# ---------- Admin site ----------
ADMIN_URL = "https://roa-admin-staging-v3.vercel.app"
ADMIN_EMAIL = "prem@cyces.co"
ADMIN_OTP = "112244"
