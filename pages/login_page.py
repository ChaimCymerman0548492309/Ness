"""eBay login page object."""

from __future__ import annotations

import os

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_loader import ConfigLoader


class LoginPage(BasePage):
    """Handles authentication or guest continuation."""

    SIGN_IN_BUTTON = 'a[href*="signin.ebay"], a:has-text("Sign in")'
    USERNAME_INPUT = "#userid"
    PASSWORD_INPUT = "#pass"
    CONTINUE_BUTTON = "#signin-continue-btn"
    SIGN_IN_SUBMIT = "#sgnBt"

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Initializes the login page with the base URL from configuration.
        super().__init__(page, config)
        self.base_url = self.config.get("base_url", "https://www.ebay.com")

    def open(self) -> None:
        # Opens the eBay homepage and dismisses any pop-up banners.
        self.goto(self.base_url)
        self.dismiss_popups()

    def login(self, username: str | None = None, password: str | None = None) -> None:
        # Performs a full sign-in flow when valid credentials are provided.
        username = username or os.getenv("EBAY_USERNAME", "")
        password = password or os.getenv("EBAY_PASSWORD", "")

        if not username or not password:
            return

        sign_in = self.page.locator(self.SIGN_IN_BUTTON).first
        if sign_in.is_visible(timeout=5000):
            sign_in.click()

        self.page.locator(self.USERNAME_INPUT).fill(username)
        self.page.locator(self.CONTINUE_BUTTON).click()
        self.page.locator(self.PASSWORD_INPUT).fill(password)
        self.page.locator(self.SIGN_IN_SUBMIT).click()
        self.wait_for_load()

    def continue_as_guest(self) -> None:
        # Opens the homepage without signing in (guest mode stub).
        self.open()
