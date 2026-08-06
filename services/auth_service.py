"""Authentication service."""

from __future__ import annotations

import os

import allure
from playwright.sync_api import Page

from pages.login_page import LoginPage
from utils.config_loader import ConfigLoader


class AuthService:
    """Handles user authentication or guest continuation."""

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Wires the login page object with the active browser page and config.
        self.page = page
        self.config = config or ConfigLoader()
        self.login_page = LoginPage(page, self.config)

    @allure.step("Authenticate user")
    def authenticate(self, username: str | None = None, password: str | None = None) -> None:
        # Logs in with credentials or continues as guest when credentials are missing.
        guest_mode = self.config.section("cart").get("guest_mode", True)
        username = username or os.getenv("EBAY_USERNAME", "")
        password = password or os.getenv("EBAY_PASSWORD", "")

        if guest_mode and (not username or not password):
            self.login_page.continue_as_guest()
            allure.attach("Guest mode", name="Auth mode", attachment_type=allure.attachment_type.TEXT)
            return

        self.login_page.open()
        self.login_page.login(username, password)
