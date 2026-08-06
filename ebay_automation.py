"""
Public API facade exposing the four core automation functions.
"""

from __future__ import annotations

from playwright.sync_api import Page

from services.auth_service import AuthService
from services.cart_assertion_service import CartAssertionService
from services.cart_service import CartService
from services.search_service import SearchService
from utils.config_loader import ConfigLoader


class EbayAutomation:
    """High-level OOP facade for the e2e commerce workflow."""

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Creates all service instances bound to a single Playwright page.
        self._config = config or ConfigLoader()
        self._auth = AuthService(page, self._config)
        self._search = SearchService(page, self._config)
        self._cart = CartService(page, self._config)
        self._cart_assertion = CartAssertionService(page, self._config)

    def authenticate(self, username: str | None = None, password: str | None = None) -> None:
        # Delegates to AuthService to log in or continue as guest.
        self._auth.authenticate(username, password)

    def search_items_by_name_under_price(
        self,
        query: str,
        max_price: float,
        limit: int = 5,
    ) -> list[str]:
        # Delegates to SearchService to find item URLs under the given price.
        return self._search.search_items_by_name_under_price(query, max_price, limit)

    def add_items_to_cart(self, urls: list[str]) -> int:
        # Delegates to CartService to add each URL product to the shopping cart.
        return self._cart.add_items_to_cart(urls)

    def assert_cart_total_not_exceeds(self, budget_per_item: float, items_count: int) -> None:
        # Delegates to CartAssertionService to verify the cart total within budget.
        self._cart_assertion.assert_cart_total_not_exceeds(budget_per_item, items_count)
