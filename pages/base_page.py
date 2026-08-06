"""Base page object with shared Playwright helpers."""

from __future__ import annotations

import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from utils.config_loader import ConfigLoader


class BasePage:
    """Parent class for all page objects (POM)."""

    _RETRYABLE_NAV_ERRORS = (
        "ERR_ABORTED",
        "ERR_CONNECTION_RESET",
        "ERR_CONNECTION_CLOSED",
        "ERR_NETWORK_CHANGED",
        "Target crashed",
        "Target closed",
        "Page crashed",
        "frame was detached",
    )

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Stores the Playwright page instance and loads timeout from config.
        self.page = page
        self.config = config or ConfigLoader()
        self.timeout = int(self.config.get("timeout_ms", 30000))

    def goto(self, url: str) -> None:
        # Navigates with retries and progressively looser wait strategies for flaky networks.
        retries = int(self.config.get("navigation_retries", 2))
        wait_strategies = ("domcontentloaded", "commit", "load")
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            for wait_until in wait_strategies:
                try:
                    self.page.goto(url, wait_until=wait_until, timeout=self.timeout)
                    return
                except PlaywrightError as error:
                    last_error = error
                    if not self._is_retryable_navigation_error(error):
                        raise
            if attempt < retries:
                time.sleep(1 + attempt)

        if last_error:
            raise last_error

    def wait_for_load(self) -> None:
        # Waits until the page DOM content has finished loading.
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)
        except PlaywrightError:
            return

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
        try:
            for candidate in candidates:
                self.click_if_visible(candidate, timeout=2000)
        except PlaywrightError:
            return

    @classmethod
    def _is_retryable_navigation_error(cls, error: Exception) -> bool:
        message = str(error)
        return any(token in message for token in cls._RETRYABLE_NAV_ERRORS)

    def sync_page(self, page: Page) -> None:
        # Updates the internal page reference after tab switches or navigation.
        self.page = page
