"""Pytest fixtures and browser configuration."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from utils.config_loader import ConfigLoader, PROJECT_ROOT

config = ConfigLoader()
LIVE_EBAY_ENV_VALUES = {"1", "true", "yes", "on"}


def pytest_addoption(parser: pytest.Parser) -> None:
    # Live eBay tests are opt-in because the public site can throttle, CAPTCHA, or block automation.
    group = parser.getgroup("ebay")
    group.addoption(
        "--run-live-ebay",
        action="store_true",
        default=False,
        help="Run tests marked live_ebay against ebay.com.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "live_ebay: tests that exercise the live eBay website")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_live = config.getoption("--run-live-ebay") or (
        os.getenv("RUN_LIVE_EBAY", "").lower() in LIVE_EBAY_ENV_VALUES
    )
    if run_live:
        return

    skip_live = pytest.mark.skip(
        reason="live eBay test skipped by default; use --run-live-ebay or RUN_LIVE_EBAY=1"
    )
    for item in items:
        if "live_ebay" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session")
def app_config() -> ConfigLoader:
    # Provides the shared ConfigLoader instance for all tests in the session.
    return config


@pytest.fixture(scope="session")
def browser(app_config: ConfigLoader) -> Browser:
    # Launches a Chromium browser for the entire test session.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=bool(app_config.get("headless", True)),
            slow_mo=int(app_config.get("slow_mo", 0) or 0),
        )
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser, app_config: ConfigLoader) -> BrowserContext:
    # Creates a fresh isolated browser context for each test.
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="en-US",
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
