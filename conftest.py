# ============================================================
# Browser setup used by every test (the `page` you get in tests)
# ============================================================
import pytest

import config


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "headless": config.HEADLESS}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1366, "height": 900}}


@pytest.fixture
def page(page):
    page.set_default_timeout(config.DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(config.NAV_TIMEOUT)
    yield page


# ============================================================
# Result summary at the end of the run, e.g.
#   Test case 1 - Onboarding ............ PASSED  (3m 30s)
# ============================================================
RESULTS = []


def test_case_label(function_name):
    """test_01_onboarding -> 'Test case 1 - Onboarding'"""
    name = function_name.removeprefix("test_")
    number, _, rest = name.partition("_")
    if number.isdigit():
        return f"Test case {int(number)} - {rest.replace('_', ' ').title()}"
    return name.replace("_", " ").title()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    # record the test result (or a setup error, e.g. browser did not start)
    if report.when == "call" or (report.when == "setup" and not report.passed):
        RESULTS.append((test_case_label(item.originalname or item.name), report.outcome, report.duration))


def pytest_terminal_summary(terminalreporter):
    if not RESULTS:
        return
    terminalreporter.section("TEST CASE RESULTS")
    for label, outcome, seconds in RESULTS:
        status = "PASSED" if outcome == "passed" else "FAILED"
        minutes, secs = divmod(int(seconds), 60)
        line = f"{label} {'.' * max(3, 45 - len(label))} {status}  ({minutes}m {secs}s)"
        terminalreporter.write_line(line, green=(status == "PASSED"), red=(status == "FAILED"), bold=True)
    passed = sum(1 for _, o, _ in RESULTS if o == "passed")
    terminalreporter.write_line(f"\nTotal: {len(RESULTS)}   Passed: {passed}   Failed: {len(RESULTS) - passed}", bold=True)
