"""eBay product details page object."""

from __future__ import annotations

import random

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_loader import ConfigLoader


class ProductPage(BasePage):
    """Product detail interactions including variant selection."""

    ADD_TO_CART = (
        '#atcRedesign_id, button:has-text("Add to cart"), '
        'button[data-testid="x-atc-action"], a:has-text("Add to cart")'
    )
    VARIANT_SELECTORS = "select.x-msku__select, select.msku-sel"
    QUANTITY_INPUT = '#qtyTextBox, input[name="quantity"], input#qtySubTxt'

    def open_product(self, url: str) -> None:
        # Navigates to a product detail page and waits for it to load.
        self.goto(url)
        self.dismiss_popups()
        self.wait_for_load()

    def select_random_variants(self) -> None:
        # Picks random available options for size, color, and quantity dropdowns.
        selects = self.page.locator(self.VARIANT_SELECTORS)
        for index in range(selects.count()):
            select = selects.nth(index)
            if not select.is_visible(timeout=1000):
                continue

            options = select.locator("option")
            valid_indexes = [
                option_index
                for option_index in range(options.count())
                if options.nth(option_index).get_attribute("value")
            ]
            if valid_indexes:
                select.select_option(index=random.choice(valid_indexes))

        quantity = self.page.locator(self.QUANTITY_INPUT).first
        if quantity.is_visible(timeout=1000):
            quantity.fill("1")

    def add_to_cart(self) -> None:
        # Selects variants if needed and clicks the Add to Cart button.
        self.select_random_variants()
        add_button = self.page.locator(self.ADD_TO_CART).first
        add_button.wait_for(state="visible", timeout=self.timeout)
        add_button.click()
        self.page.wait_for_timeout(1500)
