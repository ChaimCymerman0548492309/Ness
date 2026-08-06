"""Cart manipulation service."""

from __future__ import annotations

import allure
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from pages.product_page import ProductPage
from pages.search_page import SearchPage
from utils.config_loader import ConfigLoader
from utils.screenshot_helper import ScreenshotHelper


class CartService:
    """Adds products to the cart and captures evidence."""

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Wires product and search page objects with screenshot helper utilities.
        self.page = page
        self.config = config or ConfigLoader()
        self.product_page = ProductPage(page, self.config)
        self.search_page = SearchPage(page, self.config)
        self.screenshot_helper = ScreenshotHelper(self.config)

    @allure.step("Add items to cart")
    def add_items_to_cart(self, urls: list[str]) -> int:
        # Opens each product URL, adds it to cart, captures a screenshot, and returns to search.
        if not urls:
            allure.attach("No URLs provided", name="Cart action", attachment_type=allure.attachment_type.TEXT)
            return 0

        added_count = 0
        for index, url in enumerate(urls, start=1):
            with allure.step(f"Add item {index} to cart"):
                try:
                    self.product_page.open_product(url)
                    self.product_page.add_to_cart()
                    self.screenshot_helper.capture(self.page, f"added_to_cart_item_{index}")
                    added_count += 1
                    self._return_to_search_context()
                except PlaywrightError as exc:
                    allure.attach(
                        f"{url}\n\n{exc}",
                        name=f"Skipped cart item {index}",
                        attachment_type=allure.attachment_type.TEXT,
                    )

        return added_count

    def _return_to_search_context(self) -> None:
        # Navigates back to the search results tab or page after adding an item.
        try:
            if len(self.page.context.pages) > 1:
                self.page = self.page.context.pages[0]
                self.page.bring_to_front()
            else:
                self.page.go_back(wait_until="domcontentloaded")
            self._sync_pages()
            self.search_page.wait_for_load()
        except PlaywrightError as exc:
            allure.attach(
                str(exc),
                name="Return to search fallback",
                attachment_type=allure.attachment_type.TEXT,
            )
            self._sync_pages()

    def _sync_pages(self) -> None:
        # Keeps all page objects pointing to the same active Playwright page instance.
        self.product_page.sync_page(self.page)
        self.search_page.sync_page(self.page)
