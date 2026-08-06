"""eBay shopping cart page object."""

from __future__ import annotations

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config_loader import ConfigLoader
from utils.price_parser import PriceParser


class CartPage(BasePage):
    """Cart navigation and total extraction."""

    CART_LINK = '#gh-cart, a[href*="myeBay?MyEbay"], a[aria-label*="cart"]'
    SUBTOTAL = (
        '.subtotal, [data-testid="x-subtotal"], '
        'div:has-text("Subtotal"), span:has-text("Subtotal")'
    )
    TOTAL = (
        '[data-testid="TOTAL"], .cart-summary .total, '
        'div:has-text("Order total"), span:has-text("Total")'
    )

    def open_cart(self) -> None:
        # Opens the shopping cart page via the header link or direct URL.
        cart = self.page.locator(self.CART_LINK).first
        if cart.is_visible(timeout=5000):
            cart.click()
        else:
            base_url = self.config.get("base_url", "https://www.ebay.com")
            self.goto(f"{base_url}/cart")
        self.wait_for_load()
        self.dismiss_popups()

    def get_cart_total(self) -> float:
        # Reads and parses the cart subtotal or total amount displayed on the page.
        candidates = [self.TOTAL, self.SUBTOTAL]
        for selector in candidates:
            locator = self.page.locator(selector)
            for index in range(locator.count()):
                text = locator.nth(index).inner_text(timeout=2000)
                parsed = PriceParser.parse(text)
                if parsed is not None:
                    return parsed

        body_text = self.page.locator("body").inner_text(timeout=3000)
        for line in body_text.splitlines():
            lower = line.lower()
            if "subtotal" in lower or "total" in lower:
                parsed = PriceParser.parse(line)
                if parsed is not None:
                    return parsed

        raise AssertionError("Could not locate cart total on the page.")
