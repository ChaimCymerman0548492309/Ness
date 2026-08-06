"""Pytest fixtures and browser configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from utils.config_loader import ConfigLoader, PROJECT_ROOT

config = ConfigLoader()

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
BROWSER_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
]


@pytest.fixture(scope="session")
def app_config() -> ConfigLoader:
    # Provides the shared ConfigLoader instance for all tests in the session.
    return config


@pytest.fixture(scope="function")
def browser(app_config: ConfigLoader) -> Browser:
    # Launches an isolated Chromium browser per test to avoid cross-test crashes.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=bool(app_config.get("headless", True)),
            slow_mo=int(app_config.get("slow_mo", 0) or 0),
            args=BROWSER_LAUNCH_ARGS,
        )
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser, app_config: ConfigLoader) -> BrowserContext:
    # Creates a fresh isolated browser context for each test.
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="en-US",
        user_agent=DEFAULT_USER_AGENT,
        ignore_https_errors=True,
    )
    context.set_default_timeout(int(app_config.get("timeout_ms", 30000)))
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    # Opens a new browser tab (page) inside the test context.
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def reports_dir() -> Path:
    # Ensures all report output directories exist before tests run.
    reports_path = PROJECT_ROOT / "reports"
    reports_path.mkdir(exist_ok=True)
    (reports_path / "screenshots").mkdir(exist_ok=True)
    (reports_path / "traces").mkdir(exist_ok=True)
    (reports_path / "allure-results").mkdir(exist_ok=True)
    return reports_path
