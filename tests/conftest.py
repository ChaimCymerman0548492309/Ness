"""Pytest fixtures shared by mock-store and live-opt-in suites."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from tests.support.mock_ebay_store import install_mock_ebay_store


@pytest.fixture
def mock_ebay_store(page: Page) -> None:
    # Installs a fresh mock route set per test on the shared session page.
    try:
        page.unroute("https://www.ebay.com/**")
    except Exception:
        pass
    install_mock_ebay_store(page)
