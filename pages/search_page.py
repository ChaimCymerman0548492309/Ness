"""eBay search results page object."""

from __future__ import annotations

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.config_loader import ConfigLoader
from utils.price_parser import PriceParser


class SearchPage(BasePage):
    """Search, price filtering, and result collection."""

    SEARCH_INPUT = '#gh-ac, input[name="_nkw"], input[aria-label="Search for anything"]'
    SEARCH_BUTTON = '#gh-search-btn, button[type="submit"]:has-text("Search")'
    MIN_PRICE_INPUT = 'input[aria-label*="Minimum"], input[name="_udlo"], #x-price-min-input'
    MAX_PRICE_INPUT = 'input[aria-label*="Maximum"], input[name="_udhi"], #x-price-max-input'
    APPLY_PRICE_FILTER = 'button:has-text("Apply"), button[aria-label*="Apply"]'
    RESULT_ITEMS = "li.s-item"
    NEXT_PAGE = 'a.pagination__next, a[rel="next"], a[aria-label="Go to next search page"]'

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Initializes the search page with the base URL from configuration.
        super().__init__(page, config)
        self.base_url = self.config.get("base_url", "https://www.ebay.com")
        self.short_timeout = int(self.config.section("search").get("short_timeout_ms", 1000))

    def open(self) -> None:
        # Opens the eBay homepage and dismisses any pop-up banners.
        self.goto(self.base_url)
        self.dismiss_popups()

    def search(self, query: str) -> None:
        # Types the search query and submits it to display results.
        search_box = self.page.locator(self.SEARCH_INPUT).first
        search_box.click()
        search_box.fill(query)
        self.page.locator(self.SEARCH_BUTTON).first.click()
        self.wait_for_load()
        self.dismiss_popups()

    def apply_price_filter(self, max_price: float, min_price: float = 0) -> None:
        # Sets the min/max price filter inputs and applies them when available.
        min_input = self.page.locator(self.MIN_PRICE_INPUT).first
        max_input = self.page.locator(self.MAX_PRICE_INPUT).first

        if min_input.is_visible(timeout=3000):
            min_input.fill(str(int(min_price)))
        if max_input.is_visible(timeout=3000):
            max_input.fill(str(int(max_price)))
            apply_button = self.page.locator(self.APPLY_PRICE_FILTER).first
            if apply_button.is_visible(timeout=2000):
                apply_button.click()
                self.wait_for_load()

    def _item_locators(self) -> list[Locator]:
        # Returns all search result item locators on the current page.
        return self.page.locator(self.RESULT_ITEMS).all()

    def collect_item_urls_under_price(self, max_price: float, limit: int) -> list[str]:
        # Collects up to limit item URLs with price <= max_price using CSS locators and paging.
        collected: list[str] = []
        visited_pages = 0
        max_pages = int(self.config.section("search").get("max_pages", 5))

        while len(collected) < limit and visited_pages < max_pages:
            for item in self._item_locators():
                if len(collected) >= limit:
                    break

                link = item.locator("a.s-item__link").first
                if not link.count():
                    continue

                href = self._safe_get_attribute(link, "href")
                title = self._safe_inner_text(item.locator(".s-item__title").first)
                if not href or "shop on ebay" in title.lower():
                    continue

                price_text = self._extract_price_text(item)
                if not PriceParser.is_within_budget(price_text, max_price):
                    continue

                if href not in collected:
                    collected.append(href)

            if len(collected) >= limit:
                break

            if not self.go_to_next_page():
                break
            visited_pages += 1

        return collected[:limit]

    def _safe_get_attribute(self, locator: Locator, name: str) -> str | None:
        # Avoids spending the full page timeout on stale result cards.
        try:
            return locator.get_attribute(name, timeout=self.short_timeout)
        except PlaywrightTimeoutError:
            return None

    def _safe_inner_text(self, locator: Locator) -> str:
        # Reads optional text with a short timeout so one bad item does not stall collection.
        try:
            return locator.inner_text(timeout=self.short_timeout)
        except PlaywrightTimeoutError:
            return ""

    def _extract_price_text(self, item: Locator) -> str:
        # Reads the displayed price text from a single search result item card.
        price_candidates = [
            ".s-item__price",
            ".s-item__detail--primary .s-item__price",
            "span:has-text('$')",
        ]
        for selector in price_candidates:
            locator = item.locator(selector).first
            if locator.count() and locator.is_visible(timeout=500):
                return self._safe_inner_text(locator)
        return ""

    def go_to_next_page(self) -> bool:
        # Clicks the Next pagination button and returns True if navigation succeeded.
        next_button = self.page.locator(self.NEXT_PAGE).first
        try:
            if next_button.count() and next_button.is_visible(timeout=2000):
                next_button.click()
                self.wait_for_load()
                return True
        except PlaywrightTimeoutError:
            return False
        return False

    def collect_item_urls_under_price_xpath(self, max_price: float, limit: int) -> list[str]:
        # Collects qualifying item URLs via XPath locators with pagination support.
        collected: list[str] = []
        visited_pages = 0
        max_pages = int(self.config.section("search").get("max_pages", 5))
        xpath = (
            "//li[contains(@class,'s-item')]"
            "[.//span[contains(@class,'s-item__price')]]"
            "[.//a[contains(@class,'s-item__link')]]"
        )

        while len(collected) < limit and visited_pages < max_pages:
            items = self.page.locator(f"xpath={xpath}")
            count = min(items.count(), int(self.config.section("search").get("max_items_per_page", 30)))

            for index in range(count):
                if len(collected) >= limit:
                    break

                item = items.nth(index)
                link = item.locator("a.s-item__link").first
                href = self._safe_get_attribute(link, "href")
                title = self._safe_inner_text(item.locator(".s-item__title").first)
                if not href or "shop on ebay" in title.lower():
                    continue

                price_text = self._safe_inner_text(item.locator(".s-item__price").first)
                if not PriceParser.is_within_budget(price_text, max_price):
                    continue

                if href not in collected:
                    collected.append(href)

            if len(collected) >= limit:
                break

            if not self.go_to_next_page():
                break
            visited_pages += 1

        return collected[:limit]
