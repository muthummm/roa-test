"""
ROA Agent Onboarding - full end-to-end flow (staging)

Sign up -> ROA Application -> Tax Information -> Sign ICA (Dropbox Sign)
-> Customize Agent Tools -> Pay & Checkout (Stripe TEST card)
-> Setup ROA Email -> Transfer License (confirm checkbox)

Run:
    pytest test_roa_onboarding.py -s
    $env:HEADLESS="1"; pytest test_roa_onboarding.py -s     # headless run
"""

import datetime as dt
import os
import re
import uuid
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE_URL = "https://roa-onboarding-staging.vercel.app"
HEADLESS = os.getenv("HEADLESS", "0") == "1"

DEFAULT_TIMEOUT = 30_000      # every action waits up to 30s for the element
NAV_TIMEOUT = 60_000          # page-to-page transitions
SLOW_TIMEOUT = 90_000         # payment / e-sign callbacks

COUNTER_FILE = Path(__file__).with_name("email_counter.txt")
PHONE_COUNTER_FILE = Path(__file__).with_name("phone_counter.txt")

OTP = "112244"
EMAIL_DOMAIN = "mailinator.com"   # inbox viewable at https://www.mailinator.com
PASSWORD = "1999@#$onboard"

# ----------------------------------------------------------------------------
# Dummy data
# ----------------------------------------------------------------------------
ADDRESS = {
    "line1": "123 Main Street",
    "city": "Birmingham",
    "state": "Alabama",
    "zip": "35203",
}
EMERGENCY_CONTACT = {
    "name": "guna",
    "phone": "3128585585",
    "email": "roa-test-001@mailinator.com",
}
LICENSE = {
    "state": "Alabama",
    "type": "Salesperson",
    "expiry_days_from_today": 400,
    "transfer_days_from_today": 14,
}
BOARDS = {                       # Alabama options marked "Active" on staging
    "board": "Birmingham Association of REALTORS",
    "mls": "Greater Alabama MLS",
}
PROFESSIONAL = {
    "transactions_36m": "Less than 3",
    "transaction_count": "2",
    "volume_12m": "$0-$1M",
    "transaction_type": "Residential Sales",
    "nrds_id": "123456789",
    "brokerage": "Test Realty LLC",
}
TAX = {
    "ssn": "123456789",              # dummy SSN (field is masked, typed key by key)
    "classification": "Individual",
}
# Stripe official TEST card - only works with a pk_test_ key, never charges.
CARD = {
    "number": "4242424242424242",
    "expiry": "12 / 34",
    "cvc": "123",
    "zip": "35203",
    "country": "US",
}


# ----------------------------------------------------------------------------
# Test data - counters in email_counter.txt / phone_counter.txt keep going up,
# so every run gets a new name, email and phone number.
# ----------------------------------------------------------------------------
# Fictional numbers: NNN-555-0100 ... NNN-555-0199 are reserved for fiction in
# every US area code. 100 numbers per area code x 20 area codes = 2000 numbers.
# 312 stays first so existing phone_counter.txt values keep working.
PHONE_AREA_CODES = [
    "312", "646", "212", "415", "305", "213", "617", "702", "404", "206",
    "303", "512", "602", "615", "713", "214", "503", "612", "704", "816",
]
MAX_PHONES = len(PHONE_AREA_CODES) * 100


def phone_for_index(index):
    area = PHONE_AREA_CODES[index // 100]
    return f"{area}555{100 + index % 100:04d}"


# Realistic dummy names. 100 first x 100 last = 10,000 unique combinations.
# Letters only (the Last Name field rejects digits).
FIRST_NAMES = [
    "James", "Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Mason", "Isabella",
    "Logan", "Mia", "Lucas", "Amelia", "Jacob", "Harper", "Aiden", "Evelyn", "Jackson", "Abigail",
    "Elijah", "Emily", "Carter", "Ella", "Wyatt", "Avery", "Owen", "Scarlett", "Caleb", "Grace",
    "Henry", "Chloe", "Levi", "Victoria", "Isaac", "Riley", "Gabriel", "Aria", "Julian", "Lily",
    "Wesley", "Zoey", "Nathan", "Nora", "Hunter", "Hannah", "Connor", "Layla", "Eli", "Lillian",
    "Landon", "Addison", "Adrian", "Aubrey", "Asher", "Ellie", "Dylan", "Stella", "Miles", "Natalie",
    "Grayson", "Leah", "Thomas", "Hazel", "Charles", "Violet", "Ezra", "Aurora", "Colton", "Savannah",
    "Jordan", "Audrey", "Brayden", "Brooklyn", "Nolan", "Bella", "Easton", "Claire", "Parker", "Skylar",
    "Cooper", "Lucy", "Roman", "Paisley", "Austin", "Everly", "Jaxon", "Anna", "Bentley", "Caroline",
    "Silas", "Madelyn", "Declan", "Kennedy", "Weston", "Sadie", "Micah", "Allison", "Ryder", "Gabriella",
]
LAST_NAMES = [
    "Carter", "Bennett", "Hayes", "Brooks", "Foster", "Sullivan", "Morgan", "Reed", "Coleman", "Parker",
    "Hughes", "Price", "Myers", "Ford", "Hamilton", "Graham", "Wallace", "West", "Cole", "Jordan",
    "Reynolds", "Fisher", "Ellis", "Harrison", "Gibson", "Mcdonald", "Cruz", "Marshall", "Owens", "Burns",
    "Gordon", "Shaw", "Holmes", "Rice", "Robertson", "Hunt", "Black", "Daniels", "Palmer", "Mills",
    "Nichols", "Grant", "Knight", "Ferguson", "Rose", "Stone", "Hawkins", "Dunn", "Perkins", "Hudson",
    "Spencer", "Gardner", "Stephens", "Payne", "Pierce", "Berry", "Matthews", "Arnold", "Wagner", "Willis",
    "Ray", "Watkins", "Olson", "Carroll", "Duncan", "Snyder", "Hart", "Cunningham", "Bradley", "Lane",
    "Andrews", "Ruiz", "Harper", "Fox", "Riley", "Armstrong", "Carpenter", "Weaver", "Greene", "Lawrence",
    "Elliott", "Chavez", "Sims", "Austin", "Peters", "Kelley", "Franklin", "Lawson", "Fields", "Ryan",
    "Schmidt", "Carr", "Vasquez", "Castillo", "Wheeler", "Chapman", "Oliver", "Montgomery", "Richards", "Williamson",
]
MAX_NAMES = len(FIRST_NAMES) * len(LAST_NAMES)


def name_for_index(index):
    # Both parts change every run; the shift (index // 100) keeps all
    # 10,000 first/last combinations unique.
    n = len(FIRST_NAMES)
    first = FIRST_NAMES[index % n]
    last = LAST_NAMES[(index + index // n) % len(LAST_NAMES)]
    return first, last


def get_next_test_data():
    number = int(COUNTER_FILE.read_text().strip()) if COUNTER_FILE.exists() else 1
    if number >= MAX_NAMES:
        raise ValueError(f"All {MAX_NAMES} dummy names have been used.")

    phone_index = (
        int(PHONE_COUNTER_FILE.read_text().strip())
        if PHONE_COUNTER_FILE.exists()
        else 0
    )
    if phone_index >= MAX_PHONES:
        raise ValueError(f"All {MAX_PHONES} fictional 555-01xx sample numbers have been used.")

    first_name, last_name = name_for_index(number)
    phone_number = phone_for_index(phone_index)

    COUNTER_FILE.write_text(str(number + 1))
    PHONE_COUNTER_FILE.write_text(str(phone_index + 1))

    return {
        "first_name": first_name,
        "last_name": last_name,
        # Email matches the generated name: James Carter -> james.carter@mailinator.com
        # (public test inbox, so OTP / forwarding mails never reach real people)
        "email": f"{first_name.lower()}.{last_name.lower()}@{EMAIL_DOMAIN}",
        "phone_number": phone_number,
    }


# ----------------------------------------------------------------------------
# Wait-first helpers: every interaction waits until the element is visible
# ----------------------------------------------------------------------------
def visible(locator, timeout=DEFAULT_TIMEOUT):
    locator.wait_for(state="visible", timeout=timeout)
    return locator


def click(locator, timeout=DEFAULT_TIMEOUT):
    visible(locator, timeout).click()


def fill(locator, value, timeout=DEFAULT_TIMEOUT):
    visible(locator, timeout).fill(value)


def type_slowly(locator, value, timeout=DEFAULT_TIMEOUT):
    """For masked inputs (TIN) where .fill() is rejected."""
    visible(locator, timeout).click()
    locator.press_sequentially(value, delay=80)


def by_name(page: Page, name):
    return page.locator(f"input[name='{name}']")


def next_button(page: Page):
    return page.locator("//button[@type='submit' and normalize-space()='Next']")


def click_and_wait_for_new_url(page: Page, locator, timeout=NAV_TIMEOUT):
    old_url = page.url
    click(locator)
    page.wait_for_url(lambda url: url != old_url, timeout=timeout)


def click_next(page: Page):
    click_and_wait_for_new_url(page, next_button(page))


def fill_and_submit(page: Page, fill_page, attempts=3):
    """
    Some ROA pages load saved data asynchronously and reset the form after
    we start typing. Fill -> Next; if we are still on the same page
    (validation errors), wait for the form to settle and fill again.
    """
    page.wait_for_timeout(1500)          # let the form hydrate
    for attempt in range(1, attempts + 1):
        fill_page()
        old_url = page.url
        click(next_button(page))
        try:
            page.wait_for_url(lambda url: url != old_url, timeout=15_000)
            return
        except Exception:
            print(f"Form did not submit on {old_url} (attempt {attempt}), refilling")
            page.wait_for_timeout(2000)
    raise AssertionError(f"Could not submit form on {page.url}")


def wait_for_path(page: Page, path, timeout=NAV_TIMEOUT):
    page.wait_for_url(f"**{path}**", timeout=timeout)
    print("On page:", page.url)


def select_combobox(page: Page, label_text, option_text, close_after=False):
    """Chakra/react-select dropdown located by its <label> text."""
    combo = page.locator(
        f"xpath=//label[contains(normalize-space(), \"{label_text}\")]"
        "/following::input[@role='combobox'][1]"
    )
    visible(combo).focus()
    page.keyboard.press("ArrowDown")          # opens the menu reliably
    click(page.get_by_role("option", name=option_text, exact=True))
    if close_after:                           # multi-select menus stay open
        page.keyboard.press("Escape")


def select_option_containing(page: Page, label_text, text):
    """Multi-select (boards / MLS): options read e.g. 'Greater Alabama MLS  Active'.
    Skips silently if the option is already selected (not listed any more)."""
    combo = page.locator(
        f"xpath=//label[contains(normalize-space(), \"{label_text}\")]"
        "/following::input[@role='combobox'][1]"
    )
    visible(combo).focus()
    page.keyboard.press("ArrowDown")
    visible(page.locator("[role='option']").first)
    option = page.locator("[role='option']", has_text=text)
    if option.count():
        option.first.click()
    page.keyboard.press("Escape")


def select_first_option(page: Page, label_text, close_after=True):
    combo = page.locator(
        f"xpath=//label[contains(normalize-space(), \"{label_text}\")]"
        "/following::input[@role='combobox'][1]"
    )
    visible(combo).focus()
    page.keyboard.press("ArrowDown")
    click(page.locator("[role='option']").first)
    if close_after:
        page.keyboard.press("Escape")


def choose_radio(page: Page, text, index=0):
    click(page.locator(f"//label[.//p[normalize-space()='{text}']]").nth(index))


def confirm_dialog(page: Page, timeout=DEFAULT_TIMEOUT):
    click(page.get_by_role("dialog").get_by_role("button", name="Confirm"), timeout)


def confirm_dialog_if_present(page: Page, timeout=5_000):
    try:
        confirm_dialog(page, timeout)
    except Exception:
        pass


def _ordinal(day):
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    return f"{day}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') }"


def pick_date(page: Page, date_input, date: dt.date):
    """Date pickers ignore typing - open calendar and page with 'Next Month'."""
    click(date_input)
    label = f"Choose {date.strftime('%A, %B')} {_ordinal(date.day)}, {date.year}"
    day = page.locator(f"div[role='option'][aria-label='{label}']")
    next_month = page.get_by_role("button", name="Next Month")
    for _ in range(60):
        if day.count() and day.first.is_visible():
            day.first.click()
            return
        click(next_month)
    raise AssertionError(f"Could not reach date in calendar: {label}")


# ----------------------------------------------------------------------------
# Steps
# ----------------------------------------------------------------------------
def sign_up(page: Page, data):
    page.goto(f"{BASE_URL}/login")
    click(page.locator("//a[@href='/sign-up']"))

    fill(by_name(page, "email"), data["email"])
    click(page.locator("//button[@type='submit' and normalize-space()='Get started']"))

    pins = page.locator("input[aria-label='Please enter your pin code']")
    visible(pins.first)
    for i, digit in enumerate(OTP):
        fill(pins.nth(i), digit)
    click(page.locator("//button[@type='button' and normalize-space()='Continue']"))

    # Create an Account (step 2/2)
    fill(by_name(page, "first_name"), data["first_name"])
    fill(by_name(page, "last_name"), data["last_name"])
    fill(by_name(page, "phone_number"), data["phone_number"])
    select_combobox(page, "Primary State", "Alabama")
    fill(page.locator("input[name='password'][type='password']"), PASSWORD)
    fill(page.locator("input[name='confirm_password'][type='password']"), PASSWORD)
    click(page.locator("//button[@type='submit' and normalize-space()='Get started']"))


def roa_application(page: Page, data):
    # About yourself
    wait_for_path(page, "/roa-application/about-yourself")
    # The form pre-fills from the server and RESETS anything typed before that
    # finishes -> wait until First Name / Phone are populated first.
    page.wait_for_function(
        """() => {
            const fn = document.querySelector("input[name='first_name']");
            const ph = document.querySelector("input[name='phone_number']");
            return fn && fn.value.trim() !== '' && ph && ph.value.trim() !== '';
        }""",
        timeout=DEFAULT_TIMEOUT,
    )
    preferred = f"{data['first_name']} {data['last_name']}"
    birth_input = page.locator("input[placeholder='MM/DD/YYYY']")

    def about_yourself():
        fill(by_name(page, "preferred_name"), preferred)
        click(birth_input)
        click(page.locator(
            "div[role='option'][aria-label='Choose Sunday, October 31st, 2010']"
        ))
    fill_and_submit(page, about_yourself)

    # Residential details
    wait_for_path(page, "/your-residential-address")

    def residential():
        fill(by_name(page, "address_line_1"), ADDRESS["line1"])
        fill(by_name(page, "city"), ADDRESS["city"])
        select_combobox(page, "State", ADDRESS["state"])
        fill(by_name(page, "zipcode"), ADDRESS["zip"])
    fill_and_submit(page, residential)

    # Emergency contact
    wait_for_path(page, "/your-emergency-contact")

    def emergency():
        fill(by_name(page, "ec_name"), EMERGENCY_CONTACT["name"])
        fill(by_name(page, "ec_phone_number"), EMERGENCY_CONTACT["phone"])
        select_first_option(page, "Relationship", close_after=False)
        fill(by_name(page, "ec_email"), EMERGENCY_CONTACT["email"])
    fill_and_submit(page, emergency)

    # Active license? -> Yes
    wait_for_path(page, "/active-license")
    fill_and_submit(page, lambda: choose_radio(page, "Yes"))

    # License status -> I hold an active license
    wait_for_path(page, "/license-status")
    fill_and_submit(page, lambda: choose_radio(page, "I hold an active license"))

    # Licensed in multiple states? -> No
    wait_for_path(page, "/licensed-in-multiple-states")
    fill_and_submit(page, lambda: choose_radio(page, "No"))

    # License details
    wait_for_path(page, "/licensed-details")
    today = dt.date.today()
    license_number = f"TEST-{uuid.uuid4().hex[:12].upper()}"
    print("License number:", license_number)

    def license_details():
        select_combobox(page, "Primary State", LICENSE["state"])
        select_combobox(page, "What type of license is it?", LICENSE["type"])
        fill(by_name(page, "licenses.0.license_no"), license_number)
        dates = page.locator("input[placeholder='MM/DD/YYYY']")
        pick_date(page, dates.nth(0), today + dt.timedelta(days=LICENSE["expiry_days_from_today"]))
        pick_date(page, dates.nth(1), today + dt.timedelta(days=LICENSE["transfer_days_from_today"]))
    fill_and_submit(page, license_details)

    # Real estate boards / MLS (pick ACTIVE ones by name)
    wait_for_path(page, "/real-estate-boards")

    def boards():
        select_option_containing(page, "Real Estate Boards / Associations", BOARDS["board"])
        select_option_containing(page, "Multiple Listing Service (MLS)", BOARDS["mls"])
    fill_and_submit(page, boards)

    # Formal actions -> No to both questions
    wait_for_path(page, "/formal-actions")

    def formal_actions():
        no_labels = page.locator("//label[.//p[normalize-space()='No']]")
        visible(no_labels.first)
        for i in range(no_labels.count()):
            click(no_labels.nth(i))
    fill_and_submit(page, formal_actions)

    # Professional experience
    wait_for_path(page, "/professional-experience")

    def professional():
        select_combobox(page, "How many transactions have you closed", PROFESSIONAL["transactions_36m"])
        select_combobox(page, "Select Transaction Count", PROFESSIONAL["transaction_count"])
        select_combobox(page, "What is your production volume", PROFESSIONAL["volume_12m"])
        select_combobox(page, "What type of transactions", PROFESSIONAL["transaction_type"], close_after=True)
        fill(by_name(page, "nrds_id"), PROFESSIONAL["nrds_id"])
        fill(by_name(page, "affiliated_brokerage"), PROFESSIONAL["brokerage"])
    fill_and_submit(page, professional)

    # Sponsoring agent -> no sponsor (video modal opens automatically)
    wait_for_path(page, "/sponsoring-agent")
    video_close = page.get_by_role("dialog").get_by_role("button", name="Close")
    try:
        click(video_close, timeout=8_000)
    except Exception:
        pass
    click(next_button(page))
    click(page.get_by_text("I acknowledge that I am choosing not to name a sponsor."))
    confirm_dialog(page)
    visible(page.get_by_text("No Sponsor Selected").first)
    click(next_button(page))
    click(page.get_by_text("I acknowledge that I did not select any sponsor"))
    old_url = page.url
    confirm_dialog(page)
    page.wait_for_url(lambda url: url != old_url, timeout=NAV_TIMEOUT)

    # Part of a team? -> No
    wait_for_path(page, "/part-of-team")
    fill_and_submit(page, lambda: choose_radio(page, "No"))

    # Success -> Continue to Tax Information
    wait_for_path(page, "/roa-application/success")
    click(page.locator("button", has_text="Continue: Tax Information"))
    confirm_dialog(page)


def tax_information(page: Page, data):
    wait_for_path(page, "/tax-information/step-1")
    click_next(page)

    wait_for_path(page, "/tax-information/step-2")

    def w9_form():
        choose_radio(page, "Individual")            # auto-selects SSN
        fill(by_name(page, "tax_information.identity"), f"{data['first_name']} {data['last_name']}")
        tin = by_name(page, "tax_information.taxpayer_id")
        visible(tin).fill("")
        type_slowly(tin, TAX["ssn"])                # masked input: type key by key
        select_combobox(page, "Tax Classification", TAX["classification"])
        fill(by_name(page, "tax_information.address_line_1"), ADDRESS["line1"])
        fill(by_name(page, "tax_information.city"), ADDRESS["city"])
        select_combobox(page, "State", ADDRESS["state"])
        fill(by_name(page, "tax_information.zipcode"), ADDRESS["zip"])
    fill_and_submit(page, w9_form)

    wait_for_path(page, "/tax-information/step-3")
    click(page.locator("button", has_text="Continue: Sign Your ICA"))
    confirm_dialog_if_present(page)


def sign_ica(page: Page, data):
    wait_for_path(page, "/sign-your-ica")
    # For a new user the signature request is generated in the background;
    # the button does nothing until it's ready -> click until the iframe opens.
    esign_button = page.get_by_role("button", name="Continue to E-Sign ICA")
    esign_frame = page.locator("iframe[name='x-hellosign-embedded']")
    for attempt in range(1, 11):
        click(esign_button)
        try:
            # iframe is added to the DOM first, then becomes visible
            esign_frame.first.wait_for(state="attached", timeout=20_000)
            break
        except Exception:
            print(f"E-sign iframe not open yet (attempt {attempt}), retrying")
    else:
        raise AssertionError("Dropbox Sign iframe never opened")
    # Never click the button again from here on -> a 2nd click opens a 2nd (blank) iframe
    visible(esign_frame.first, SLOW_TIMEOUT)
    assert esign_frame.count() == 1, "More than one Dropbox Sign iframe is open"

    ds = page.frame_locator("iframe[name='x-hellosign-embedded']")
    click(ds.get_by_role("button", name="OK"), SLOW_TIMEOUT)     # "not legally binding" popup
    click(ds.get_by_role("button", name="Get started"))

    full_name = f"{data['first_name']} {data['last_name']}"
    initials = (data["first_name"][0] + data["last_name"][0]).upper()

    def type_in_signing_modal(text, everywhere):
        type_tab = ds.get_by_role("tab", name="Type")
        try:
            visible(type_tab, 8_000)
        except Exception:
            return                     # signature remembered -> inserted directly
        type_tab.click()
        fill(ds.locator("input[data-qa-ref='signing-modal--type-in-field']"), text)
        if everywhere:
            click(ds.get_by_test_id("insert-everywhere-btn"))
        else:
            click(ds.get_by_test_id("singing-modal--insert-btn"))
        type_tab.wait_for(state="hidden", timeout=DEFAULT_TIMEOUT)   # modal closed

    # MANDATORY fields only: Dropbox Sign marks them with an inner "__required--" element.
    # Optional fields (e.g. Tickbox8/9, text boxes on the W-9 page) are left untouched.
    REQUIRED = ":has([class*='__required--'])"
    req_initials = ds.locator(
        f"[data-qa-ref='field-initials']{REQUIRED} [data-qa-ref='initials-input']",
        has_text="Click to initial",
    )
    req_signature = ds.locator(
        f"[data-qa-ref='field-signature']{REQUIRED} [data-qa-ref='signature-input']",
        has_text="Click to sign",
    )
    req_checkbox = ds.locator(
        f"[data-qa-ref='field-checkbox']{REQUIRED}"
        ":has(input[data-qa-ref='checkbox']:not(:checked))"
    )

    fields_left = ds.locator(".m-signature-request--header-fields-left-count")
    visible(fields_left)                       # "REQ* FIELDS LEFT 13"
    visible(ds.locator("[data-qa-ref='page-0']"))
    stuck = 0
    for _ in range(40):
        if fields_left.count() == 0 or not fields_left.is_visible():
            break                              # counter disappears when all done
        before = fields_left.inner_text()
        print("Required signature fields left:", before)

        if req_initials.count():
            target, kind = req_initials.first, "initials"
        elif req_signature.count():
            target, kind = req_signature.first, "signature"
        elif req_checkbox.count():
            target, kind = req_checkbox.first, "checkbox"
        else:
            # remaining required fields are on pages not rendered yet
            click(ds.locator("[data-qa-ref='button-next']"))
            page.wait_for_timeout(1500)
            continue

        target.scroll_into_view_if_needed()
        visible(target).click()
        if kind == "initials":
            type_in_signing_modal(initials, everywhere=True)
        elif kind == "signature":
            type_in_signing_modal(full_name, everywhere=False)
        page.wait_for_timeout(1000)

        if fields_left.count() and fields_left.is_visible() and fields_left.inner_text() == before:
            stuck += 1
            if stuck >= 5:
                raise AssertionError(f"Signing is stuck at {before} required fields")
        else:
            stuck = 0

    click(ds.locator("[data-qa-ref='button-next']", has_text="Continue"))
    click(ds.locator("[data-qa-ref='button-agree']"))
    visible(ds.get_by_text("Thanks for submitting your document!"), SLOW_TIMEOUT)

    # The app moves on once Dropbox Sign notifies it; reload if it doesn't.
    try:
        wait_for_path(page, "/customize-agent-tools", timeout=30_000)
    except Exception:
        page.reload()
        wait_for_path(page, "/customize-agent-tools", timeout=SLOW_TIMEOUT)


def customize_agent_tools(page: Page):
    wait_for_path(page, "/customize-agent-tools")

    # "Stay Connected with the ROA Network" modal (both boxes pre-checked)
    agree = page.locator("button:visible", has_text="Agree and Continue")
    try:
        click(agree, timeout=15_000)
    except Exception:
        pass

    # Pick a CRM (Follow Up Boss - no additional cost)
    if not page.get_by_text("Your Selected CRM Tool").is_visible():
        click(page.locator("button:visible", has_text="Add at No Additional Cost").first)
        visible(page.get_by_text("Your Selected CRM Tool"))

    click(page.locator("button:visible", has_text="Continue: Pay & Checkout"))
    confirm_dialog_if_present(page)


def pay_and_checkout(page: Page, data):
    wait_for_path(page, "/pay-and-checkout")
    checkout = page.frame_locator("iframe[name='embedded-checkout']")
    visible(checkout.locator("#cardNumber"), SLOW_TIMEOUT)

    # Safety: never type a card into a live Stripe checkout
    assert any(
        re.search(r"publishableKey=pk_test_", frame.url) for frame in page.frames
    ), "Stripe checkout is NOT in test mode - aborting payment step."

    fill(checkout.locator("#cardNumber"), CARD["number"])
    fill(checkout.locator("#cardExpiry"), CARD["expiry"])
    fill(checkout.locator("#cardCvc"), CARD["cvc"])
    fill(checkout.locator("#billingName"), f"{data['first_name']} {data['last_name']}")
    visible(checkout.locator("#billingCountry")).select_option(CARD["country"])
    fill(checkout.locator("#billingPostalCode"), CARD["zip"])

    save_info = checkout.locator("#enableStripePass")
    if save_info.count() and save_info.is_checked():
        save_info.uncheck()

    page.wait_for_timeout(1500)                 # let Stripe validate the fields
    old_url = page.url
    pay_button = checkout.locator("button[type='submit']", has_text="Pay").first
    for attempt in range(1, 4):
        visible(pay_button).scroll_into_view_if_needed()
        pay_button.click()
        try:
            page.wait_for_url(lambda url: url != old_url, timeout=45_000)
            break
        except Exception:
            print(f"Payment not completed yet (attempt {attempt}), clicking Pay again")
    else:
        raise AssertionError("Stripe payment did not complete")


def setup_roa_email(page: Page, data):
    wait_for_path(page, "/setup-roa-email/step-1", timeout=SLOW_TIMEOUT)

    select_first_option(page, "Suggested ROA Email Address", close_after=False)
    visible(page.get_by_text("This email address is available!"))

    fill(by_name(page, "forwarding_email"), data["email"])
    click(page.locator("button:visible", has_text="Send code"))
    pins = page.locator("input[aria-label='Please enter your pin code']")
    visible(pins.first)
    for i, digit in enumerate(OTP):
        fill(pins.nth(i), digit)
    visible(page.get_by_text("Forwarding email verified successfully"))

    ack = page.locator("input[type='checkbox']").last
    if not ack.is_checked():
        click(page.get_by_text("I acknowledge that my Realty of America email", exact=False))

    # The suggested-email dropdown can be reset by a late data reload;
    # if Next shows "This field is required" instead of the confirm dialog,
    # pick the email again and retry.
    old_url = page.url
    for attempt in range(1, 4):
        click(next_button(page))
        try:
            confirm_dialog(page, timeout=8_000)    # "Confirm Your Email Details"
            break
        except Exception:
            print(f"ROA email not accepted (attempt {attempt}), reselecting")
            select_first_option(page, "Suggested ROA Email Address", close_after=False)
            visible(page.get_by_text("This email address is available!"))
            page.wait_for_timeout(1000)
    else:
        raise AssertionError("Could not submit ROA email form")
    page.wait_for_url(lambda url: url != old_url, timeout=NAV_TIMEOUT)

    wait_for_path(page, "/setup-roa-email/step-2")
    click(page.locator("button:visible", has_text="Continue: Transfer License"), timeout=NAV_TIMEOUT)
    confirm_dialog_if_present(page)


def transfer_license(page: Page):
    wait_for_path(page, "/transfer-license")
    click(page.get_by_text("I confirm that I have transferred my", exact=False).first)
    confirm_dialog(page)
    visible(page.get_by_text("Pending Broker Review"))
    print("License transfer submitted -> Pending Broker Review")


# ----------------------------------------------------------------------------
# Test
# ----------------------------------------------------------------------------
def test_roa_onboarding_full_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        page = context.new_page()
        page.set_default_timeout(DEFAULT_TIMEOUT)
        page.set_default_navigation_timeout(NAV_TIMEOUT)

        try:
            # If the generated email/phone is already registered on staging,
            # account creation won't move on -> take the next name/number.
            for attempt in range(1, 6):
                data = get_next_test_data()
                for key, value in data.items():
                    print(f"{key}: {value}")
                sign_up(page, data)
                try:
                    page.wait_for_url("**/roa-application/about-yourself**", timeout=45_000)
                    break
                except Exception:
                    print(f"Sign-up rejected for {data['email']} (attempt {attempt}), trying next name")
                    context.clear_cookies()
            else:
                raise AssertionError("Sign-up failed for 5 different names")

            roa_application(page, data)
            tax_information(page, data)
            sign_ica(page, data)
            customize_agent_tools(page)
            pay_and_checkout(page, data)
            setup_roa_email(page, data)
            transfer_license(page)
        except Exception:
            shot = Path(__file__).with_name("failure.png")
            page.screenshot(path=str(shot), full_page=True)
            print("Failed on:", page.url, "| screenshot:", shot)
            raise
        finally:
            context.close()
            browser.close()
