# ROA Automation

## Files

```
config.py          settings: URL, wait times, OTP, password
dummy_data.py      values typed into forms + new name/email/phone each run
email_counter.txt  \ counters for the next name / phone (only go up)
phone_counter.txt  /
pages/             one file per screen of the website
   base_page.py    common actions: click, fill, dropdown, popup, OTP, calendar
   signup_page.py, roa_application_page.py, tax_information_page.py,
   sign_ica_page.py, agent_tools_page.py, payment_page.py,
   roa_email_page.py, transfer_license_page.py, login_page.py
   admin_login_page.py   admin site login (email + OTP)
   admin_agent_page.py   admin: find agent > Transfer now > Onboard Agent > check Active
tests/
   regression.py      regression test cases
                      test_01_onboarding = agent onboarding + admin approval
conftest.py        browser setup (no need to touch)
pytest.ini         pytest options (no need to touch)
reports/           screenshot when a test fails
```

## Run

```powershell
.\venv1\Scripts\activate
pytest                          # browser visible
$env:HEADLESS="1"; pytest       # no browser window
```

## Add something new (3 steps)

1. Create `pages/my_page.py`:
   ```python
   from pages.base_page import BasePage

   class MyPage(BasePage):
       def complete(self):
           self.wait_for_page("/my-page")
           self.fill(self.input("first_name"), "James")
           self.click(self.button("Save"))
   ```
2. Create `tests/test_my_page.py` (file and function names must start with `test_`):
   ```python
   from pages.login_page import LoginPage
   from pages.my_page import MyPage

   def test_my_page(page):
       LoginPage(page).login("ava.morgan@mailinator.com")
       MyPage(page).complete()
   ```
3. Run it: `pytest tests/test_my_page.py`
