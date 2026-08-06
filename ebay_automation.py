"""
Public API facade exposing the four core automation functions.
Names match the assignment brief exactly (camelCase).
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
        # הזדהות — login or continue as guest.
        self._auth.authenticate(username, password)

    def searchItemsByNameUnderPrice(
        self,
        query: str,
        maxPrice: float,
        limit: int = 5,
    ) -> list[str]:
        # Returns up to `limit` item URLs with price <= maxPrice.
        return self._search.searchItemsByNameUnderPrice(query, maxPrice, limit)

    def addItemsToCart(self, urls: list[str]) -> None:
        # Opens each product, selects variants, adds to cart, returns to search, screenshots.
        self._cart.addItemsToCart(urls)

    def assertCartTotalNotExceeds(self, budgetPerItem: float, itemsCount: int) -> None:
        # Asserts cart total <= budgetPerItem * itemsCount and saves screenshot/trace.
        self._cart_assertion.assertCartTotalNotExceeds(budgetPerItem, itemsCount)
