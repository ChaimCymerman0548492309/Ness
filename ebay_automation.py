"""
Public API — four core functions with exact assignment brief names (camelCase).

TypeScript brief signatures (Python equivalents):

    authenticate()
    searchItemsByNameUnderPrice(query, maxPrice, limit=5) -> list[str]
    addItemsToCart(urls) -> None
    assertCartTotalNotExceeds(budgetPerItem, itemsCount) -> None
"""

from __future__ import annotations

from playwright.sync_api import Page

from services.auth_service import AuthService
from services.cart_assertion_service import CartAssertionService
from services.cart_service import CartService
from services.search_service import SearchService
from utils.config_loader import ConfigLoader

__all__ = [
    "EbayAutomation",
    "authenticate",
    "searchItemsByNameUnderPrice",
    "addItemsToCart",
    "assertCartTotalNotExceeds",
]


def authenticate(
    page: Page,
    username: str | None = None,
    password: str | None = None,
    config: ConfigLoader | None = None,
) -> None:
    # הזדהות — login or continue as guest (Login Stub / Guest).
    AuthService(page, config).authenticate(username, password)


def searchItemsByNameUnderPrice(
    page: Page,
    query: str,
    maxPrice: float,
    limit: int = 5,
    config: ConfigLoader | None = None,
) -> list[str]:
    # Returns up to `limit` item URLs with price <= maxPrice (XPath + paging).
    return SearchService(page, config).searchItemsByNameUnderPrice(query, maxPrice, limit)


def addItemsToCart(
    page: Page,
    urls: list[str],
    config: ConfigLoader | None = None,
) -> None:
    # Opens each product, selects variants, adds to cart, returns to search, screenshots.
    CartService(page, config).addItemsToCart(urls)


def assertCartTotalNotExceeds(
    page: Page,
    budgetPerItem: float,
    itemsCount: int,
    config: ConfigLoader | None = None,
) -> None:
    # Asserts cart total <= budgetPerItem * itemsCount; saves screenshot/trace.
    CartAssertionService(page, config).assertCartTotalNotExceeds(budgetPerItem, itemsCount)


class EbayAutomation:
    """High-level OOP facade for the e2e commerce workflow."""

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        self._page = page
        self._config = config or ConfigLoader()

    def authenticate(self, username: str | None = None, password: str | None = None) -> None:
        authenticate(self._page, username, password, self._config)

    def searchItemsByNameUnderPrice(
        self,
        query: str,
        maxPrice: float,
        limit: int = 5,
    ) -> list[str]:
        return searchItemsByNameUnderPrice(self._page, query, maxPrice, limit, self._config)

    def addItemsToCart(self, urls: list[str]) -> None:
        addItemsToCart(self._page, urls, self._config)

    def assertCartTotalNotExceeds(self, budgetPerItem: float, itemsCount: int) -> None:
        assertCartTotalNotExceeds(self._page, budgetPerItem, itemsCount, self._config)
