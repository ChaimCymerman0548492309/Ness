"""Base page object with shared Playwright helpers."""

from __future__ import annotations

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from utils.config_loader import ConfigLoader


class BasePage:
    """Parent class for all page objects (POM)."""

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Stores the Playwright page instance and loads timeout from config.
        self.page = page
        self.config = config or ConfigLoader()
        self.timeout = int(self.config.get("timeout_ms", 30000))

    def goto(self, url: str) -> None:
        # Navigates the browser to the given URL and waits for DOM content.
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

    def wait_for_load(self) -> None:
        # Waits until the page DOM content has finished loading.
        self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)

    def click_if_visible(self, locator: Locator, timeout: int | None = None) -> bool:
        # Clicks the first matching element only if it is visible within the timeout.
        timeout = timeout or self.timeout
        try:
            if locator.first.is_visible(timeout=timeout):
                locator.first.click(timeout=timeout)
                return True
        except (PlaywrightTimeoutError, PlaywrightError):
            return False
        return False

    def dismiss_popups(self) -> None:
        # Attempts to close cookie/consent banners that may block interactions.
        candidates = [
            self.page.get_by_role("button", name="Accept"),
            self.page.get_by_role("button", name="Accept all"),
            self.page.get_by_role("button", name="Agree"),
            self.page.locator("#gdpr-banner-accept"),
        ]
        for candidate in candidates:
            self.click_if_visible(candidate, timeout=2000)

    def sync_page(self, page: Page) -> None:
        # Updates the internal page reference after tab switches or navigation.
        self.page = page
