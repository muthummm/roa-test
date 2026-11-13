from config import DEFAULT_TIMEOUT, SLOW_TIMEOUT
from pages.base_page import BasePage

ESIGN_FRAME = "iframe[name='x-hellosign-embedded']"
REQUIRED = ":has([class*='__required--'])"      # Dropbox Sign marks mandatory fields like this


class SignIcaPage(BasePage):

    def complete(self, user):
        self.wait_for_page("/sign-your-ica")
        self.open_esign()

        esign = self.page.frame_locator(ESIGN_FRAME)
        self.click(esign.get_by_role("button", name="OK"), SLOW_TIMEOUT)
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

    def open_esign(self):
        """Click 'Continue to E-Sign ICA' until the signing window opens (max 10 tries)."""
        button = self.page.get_by_role("button", name="Continue to E-Sign ICA")
        frame = self.page.locator(ESIGN_FRAME)
        for attempt in range(1, 11):
            self.click(button)
            try:
                frame.first.wait_for(state="attached", timeout=20_000)
                break
            except Exception:
                print(f"E-sign not open yet (attempt {attempt}), retrying")
        else:
            raise AssertionError("E-sign window never opened")
        # do NOT click the button again - it would open a second, empty window
        self.wait_visible(frame.first, SLOW_TIMEOUT)
        assert frame.count() == 1, "More than one e-sign window is open"

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

        stuck = 0
        for _ in range(40):
            if fields_left.count() == 0 or not fields_left.is_visible():
                break                                   # all mandatory fields done
            before = fields_left.inner_text()
            print("Mandatory fields left:", before)

            if initials.count():
                initials.first.scroll_into_view_if_needed()
                self.click(initials.first)
                self.type_signature(user["initials"], insert_everywhere=True)
            elif signatures.count():
                signatures.first.scroll_into_view_if_needed()
                self.click(signatures.first)
                self.type_signature(user["full_name"], insert_everywhere=False)
            elif checkboxes.count():
                checkboxes.first.scroll_into_view_if_needed()
                self.click(checkboxes.first)
            else:
                # remaining fields are on pages not loaded yet -> go to next field
                self.click(esign.locator("[data-qa-ref='button-next']"))
                self.page.wait_for_timeout(1500)
                continue
            self.page.wait_for_timeout(1000)

            if fields_left.count() and fields_left.is_visible() and fields_left.inner_text() == before:
                stuck += 1
                if stuck >= 5:
                    raise AssertionError(f"Signing stuck at {before} fields")
            else:
                stuck = 0
