"""Search service implementing price-aware product discovery."""

from __future__ import annotations

import allure
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from pages.search_page import SearchPage
from utils.config_loader import ConfigLoader


class SearchService:
    """Business logic for searching products under a price threshold."""

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Wires the search page object with the active browser page and config.
        self.page = page
        self.config = config or ConfigLoader()
        self.search_page = SearchPage(page, self.config)

    @allure.step("searchItemsByNameUnderPrice: query={query}, maxPrice={maxPrice}")
    def searchItemsByNameUnderPrice(
        self,
        query: str,
        maxPrice: float,
        limit: int = 5,
    ) -> list[str]:
        # Searches by query, applies price filter, and returns up to limit qualifying item URLs.
        try:
            self.search_page.search(query, max_price=maxPrice)
            self.search_page.apply_price_filter(max_price=maxPrice)
            urls = self.search_page.collect_item_urls_under_price_xpath(
                max_price=maxPrice,
                limit=limit,
            )
        except PlaywrightError as exc:
            allure.attach(
                str(exc),
                name="Search flow Playwright error",
                attachment_type=allure.attachment_type.TEXT,
            )
            raise

        allure.attach(
            "\n".join(urls) if urls else "No matching items found",
            name="Collected item URLs",
            attachment_type=allure.attachment_type.TEXT,
        )
        return urls
