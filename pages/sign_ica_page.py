from config import DEFAULT_TIMEOUT, SLOW_TIMEOUT
from pages.base_page import BasePage

ESIGN_FRAME = "iframe[name='x-hellosign-embedded']"
REQUIRED = ":has([class*='__required--'])"      # Dropbox Sign marks mandatory fields like this


class SignIcaPage(BasePage):

    def complete(self, user):
        self.wait_for_page("/sign-your-ica")
        self.open_esign()

        esign = self.page.frame_locator(ESIGN_FRAME)
        self.click(esign.get_by_role("button", name="OK"))          # "not legally binding" popup
        self.click(esign.get_by_role("button", name="Get started"))

        self.fill_mandatory_fields(user)

        self.click(esign.locator("[data-qa-ref='button-next']", has_text="Continue"))
        self.click(esign.locator("[data-qa-ref='button-agree']"))
        self.wait_visible(esign.get_by_text("Thanks for submitting your document!"), SLOW_TIMEOUT)

        # the app moves to the next page by itself; reload if it does not
        try:
            self.wait_for_page("/customize-agent-tools", timeout=30_000)
        except Exception:
            self.page.reload()
            self.wait_for_page("/customize-agent-tools", timeout=SLOW_TIMEOUT)

    def open_esign(self, attempts=6):
        """Open the Dropbox Sign window and wait until it has fully loaded (its 'OK' popup shows).

        - Wait for the page to settle first: clicking too early lets a page refresh close the window.
        - Only click when NO e-sign window exists (a 2nd click opens a 2nd, empty window).
        - If the window does not load, reload the page and try again.
        """
        button = self.page.get_by_role("button", name="Continue to E-Sign ICA")
        frame = self.page.locator(ESIGN_FRAME)
        ok_button = self.page.frame_locator(ESIGN_FRAME).get_by_role("button", name="OK")

        for attempt in range(1, attempts + 1):
            self.wait_visible(button)
            self.page.wait_for_timeout(3000)               # let the page finish loading
            if frame.count() == 0:
                self.click(button)
            try:
                self.wait_visible(ok_button, 45_000)        # e-sign document loaded
                assert frame.count() == 1, "More than one e-sign window is open"
                return
            except AssertionError:
                raise
            except Exception:
                print(f"E-sign window did not load (attempt {attempt}), reloading page")
                self.page.reload()
        raise AssertionError("E-sign window never loaded")

    def type_signature(self, text, insert_everywhere):
        esign = self.page.frame_locator(ESIGN_FRAME)
        type_tab = esign.get_by_role("tab", name="Type")
        try:
            self.wait_visible(type_tab, 8_000)
        except Exception:
            return                      # signature already remembered
        type_tab.click()
        self.fill(esign.locator("input[data-qa-ref='signing-modal--type-in-field']"), text)
        if insert_everywhere:
            self.click(esign.get_by_test_id("insert-everywhere-btn"))
        else:
            self.click(esign.get_by_test_id("singing-modal--insert-btn"))
        type_tab.wait_for(state="hidden", timeout=DEFAULT_TIMEOUT)

    def fill_mandatory_fields(self, user):
        esign = self.page.frame_locator(ESIGN_FRAME)
        initials = esign.locator(f"[data-qa-ref='field-initials']{REQUIRED} [data-qa-ref='initials-input']",
                                 has_text="Click to initial")
        signatures = esign.locator(f"[data-qa-ref='field-signature']{REQUIRED} [data-qa-ref='signature-input']",
                                   has_text="Click to sign")
        checkboxes = esign.locator(f"[data-qa-ref='field-checkbox']{REQUIRED}"
                                   ":has(input[data-qa-ref='checkbox']:not(:checked))")
        fields_left = esign.locator(".m-signature-request--header-fields-left-count")
        self.wait_visible(fields_left)
        self.wait_visible(esign.locator("[data-qa-ref='page-0']"))

        # skip[kind] = how many fields of that kind did NOT change the counter when clicked
        # (already filled / not really required) -> next time click the following one instead
        skip = {"initials": 0, "signature": 0, "checkbox": 0}
        stuck = 0
        for _ in range(40):
            if fields_left.count() == 0 or not fields_left.is_visible():
                break                                   # all mandatory fields done
            before = fields_left.inner_text()
            print("Mandatory fields left:", before)

            if initials.count() > skip["initials"]:
                kind, field = "initials", initials.nth(skip["initials"])
            elif signatures.count() > skip["signature"]:
                kind, field = "signature", signatures.nth(skip["signature"])
            elif checkboxes.count() > skip["checkbox"]:
                kind, field = "checkbox", checkboxes.nth(skip["checkbox"])
            else:
                # remaining fields are on pages not loaded yet -> jump to the next field
                self.click(esign.locator("[data-qa-ref='button-next']"))
                self.page.wait_for_timeout(1500)
                stuck += 1
                if stuck >= 15:
                    raise AssertionError(f"Signing stuck at {before} fields")
                continue

            field.scroll_into_view_if_needed()
            self.click(field)
            if kind == "initials":
                self.type_signature(user["initials"], insert_everywhere=True)
                # 'Insert everywhere' updates the other pages a moment later
                self.page.wait_for_timeout(1500)
            elif kind == "signature":
                self.type_signature(user["full_name"], insert_everywhere=False)
            self.page.wait_for_timeout(1000)

            if fields_left.count() and fields_left.is_visible() and fields_left.inner_text() == before:
                # nothing changed: close any 'Edit / Clear' menu and try the next field
                self.page.keyboard.press("Escape")
                skip[kind] += 1
                stuck += 1
                print(f"{kind} field did not count, trying the next one")
                if stuck >= 15:
                    raise AssertionError(f"Signing stuck at {before} fields")
            else:
                stuck = 0
                skip = {"initials": 0, "signature": 0, "checkbox": 0}
