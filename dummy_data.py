# ============================================================
# DUMMY DATA - values typed into the forms
# ============================================================
from pathlib import Path

from config import EMAIL_DOMAIN

# ---------- fixed values ----------
ADDRESS = {"line1": "123 Main Street", "city": "Birmingham", "state": "Alabama", "zip": "35203"}
PRIMARY_STATE = "Alabama"
DATE_OF_BIRTH = "Choose Sunday, October 31st, 2010"      # calendar day label

EMERGENCY_CONTACT = {"name": "guna", "phone": "3128585585", "email": "roa-test-001@mailinator.com"}

LICENSE = {"state": "Alabama", "type": "Salesperson",
           "expiry_days_from_today": 400, "transfer_days_from_today": 14}

BOARDS = {"board": "Birmingham Association of REALTORS", "mls": "Greater Alabama MLS"}

PROFESSIONAL = {"transactions_36m": "Less than 3", "transaction_count": "2",
                "volume_12m": "$0-$1M", "transaction_type": "Residential Sales",
                "nrds_id": "123456789", "brokerage": "Test Realty LLC"}

TAX = {"ssn": "123456789", "classification": "Individual"}

# Stripe TEST card - never charges real money
CARD = {"number": "4242424242424242", "expiry": "12 / 34", "cvc": "123", "zip": "35203", "country": "US"}


# ---------- new user every run ----------
# The two counter files only go up, so every run gets a new name, email and phone.
NAME_COUNTER_FILE = Path(__file__).with_name("email_counter.txt")
PHONE_COUNTER_FILE = Path(__file__).with_name("phone_counter.txt")

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
# Fictional phone numbers NNN-555-0100 ... 0199 (100 per area code)
PHONE_AREA_CODES = [
    "312", "646", "212", "415", "305", "213", "617", "702", "404", "206",
    "303", "512", "602", "615", "713", "214", "503", "612", "704", "816",
]


def new_user():
    """Returns a new user, e.g.
    {"first_name": "Ava", "last_name": "Morgan", "full_name": "Ava Morgan", "initials": "AM",
     "email": "ava.morgan@mailinator.com", "phone_number": "3125550198"}"""
    number = int(NAME_COUNTER_FILE.read_text(encoding="utf-8-sig").strip()) if NAME_COUNTER_FILE.exists() else 1
    phone_index = int(PHONE_COUNTER_FILE.read_text(encoding="utf-8-sig").strip()) if PHONE_COUNTER_FILE.exists() else 0

    first = FIRST_NAMES[number % 100]
    last = LAST_NAMES[(number + number // 100) % 100]
    phone = f"{PHONE_AREA_CODES[phone_index // 100]}555{100 + phone_index % 100:04d}"

    NAME_COUNTER_FILE.write_text(str(number + 1))
    PHONE_COUNTER_FILE.write_text(str(phone_index + 1))

    return {
        "first_name": first,
        "last_name": last,
        "full_name": f"{first} {last}",
        "initials": (first[0] + last[0]).upper(),
        "email": f"{first.lower()}.{last.lower()}@{EMAIL_DOMAIN}",
        "phone_number": phone,
    }
