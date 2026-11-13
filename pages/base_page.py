# ============================================================
# BASE PAGE - common actions used by every page
# Every page class starts with:  class MyPage(BasePage):
# Every action first WAITS until the element is visible.
# ============================================================
import datetime as dt

from config import BASE_URL, DEFAULT_TIMEOUT, NAV_TIMEOUT, OTP


class BasePage:
    def __init__(self, page):
        self.page = page

    # ---------- open / wait for pages ----------
    def open(self, path):
        self.page.goto(BASE_URL + path)

    def wait_for_page(self, path, timeout=NAV_TIMEOUT):
        self.page.wait_for_url(f"**{path}**", timeout=timeout)
        print("On page:", self.page.url)

    def wait_for_url_change(self, old_url, timeout=NAV_TIMEOUT):
        self.page.wait_for_url(lambda url: url != old_url, timeout=timeout)

    # ---------- click / type ----------
    def wait_visible(self, locator, timeout=DEFAULT_TIMEOUT):
        locator.wait_for(state="visible", timeout=timeout)
        return locator

    def click(self, locator, timeout=DEFAULT_TIMEOUT):
        self.wait_visible(locator, timeout).click()

    def click_if_present(self, locator, timeout=5_000):
        try:
            self.click(locator, timeout)
        except Exception:
            pass

    def fill(self, locator, value, timeout=DEFAULT_TIMEOUT):
        self.wait_visible(locator, timeout).fill(value)

    def type_slowly(self, locator, value):
        """For masked fields (SSN) where fill() does not work."""
        self.click(locator)
        locator.press_sequentially(value, delay=80)

    # ---------- find elements ----------
    def input(self, name):
        """<input name='...'>"""
        return self.page.locator(f"input[name='{name}']")

    def button(self, text):
        """Visible button that contains this text."""
        return self.page.locator("button:visible", has_text=text)

    def next_button(self):
        return self.page.locator("//button[@type='submit' and normalize-space()='Next']")

    # ---------- Next button ----------
    def click_next(self):
        old_url = self.page.url
        self.click(self.next_button())
        self.wait_for_url_change(old_url)

    def fill_and_next(self, fill_form, attempts=3):
        """Fill the form, click Next. Some forms reset themselves after loading,
        so if the page did not change we fill it again (max 3 times)."""
        self.page.wait_for_timeout(1500)
        for attempt in range(1, attempts + 1):
            fill_form()
            old_url = self.page.url
            self.click(self.next_button())
            try:
                self.wait_for_url_change(old_url, timeout=15_000)
                return
            except Exception:
                print(f"Form not submitted (attempt {attempt}), filling again")
                self.page.wait_for_timeout(2000)
        raise AssertionError(f"Could not submit form on {self.page.url}")

    # ---------- dropdowns / radio buttons ----------
    def dropdown(self, label):
        return self.page.locator(
            f"xpath=//label[contains(normalize-space(), \"{label}\")]/following::input[@role='combobox'][1]"
        )

    def open_dropdown(self, label):
        self.wait_visible(self.dropdown(label)).focus()
        self.page.keyboard.press("ArrowDown")

    def select_dropdown(self, label, option, close_after=False):
        """Pick the option with exactly this text."""
        self.open_dropdown(label)
        self.click(self.page.get_by_role("option", name=option, exact=True))
        if close_after:
            self.page.keyboard.press("Escape")

    def select_dropdown_containing(self, label, text):
        """Multi-select: pick the option that contains this text (skip if already picked)."""
        self.open_dropdown(label)
        self.wait_visible(self.page.locator("[role='option']").first)
        option = self.page.locator("[role='option']", has_text=text)
        if option.count():
            option.first.click()
        self.page.keyboard.press("Escape")

    def select_first_option(self, label, close_after=True):
        self.open_dropdown(label)
        self.click(self.page.locator("[role='option']").first)
        if close_after:
            self.page.keyboard.press("Escape")

    def choose_radio(self, text):
        self.click(self.page.locator(f"//label[.//p[normalize-space()='{text}']]").first)

    # ---------- popups ----------
    def confirm_popup(self, timeout=DEFAULT_TIMEOUT):
        self.click(self.page.get_by_role("dialog").get_by_role("button", name="Confirm"), timeout)

    def confirm_popup_if_present(self):
        try:
            self.confirm_popup(timeout=5_000)
        except Exception:
            pass

    # ---------- OTP / calendar ----------
    def enter_otp(self):
        boxes = self.page.locator("input[aria-label='Please enter your pin code']")
        self.wait_visible(boxes.first)
        for i, digit in enumerate(OTP):
            self.fill(boxes.nth(i), digit)

    def pick_date(self, date_input, days_from_today):
        """Open the calendar and click the date (typing a date does not work)."""
        date = dt.date.today() + dt.timedelta(days=days_from_today)
        day = date.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        label = f"Choose {date.strftime('%A, %B')} {day}{suffix}, {date.year}"

        self.click(date_input)
        day_cell = self.page.locator(f"div[role='option'][aria-label='{label}']")
        for _ in range(60):
            if day_cell.count() and day_cell.first.is_visible():
                day_cell.first.click()
                return
            self.click(self.page.get_by_role("button", name="Next Month"))
        raise AssertionError(f"Date not found in calendar: {label}")
