"""Cart assertion service."""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from pages.cart_page import CartPage
from utils.config_loader import ConfigLoader, PROJECT_ROOT
from utils.screenshot_helper import ScreenshotHelper


class CartAssertionService:
    """Validates cart totals against a computed budget threshold."""

    def __init__(self, page: Page, config: ConfigLoader | None = None) -> None:
        # Wires the cart page object with screenshot helper utilities.
        self.page = page
        self.config = config or ConfigLoader()
        self.cart_page = CartPage(page, self.config)
        self.screenshot_helper = ScreenshotHelper(self.config)

    @allure.step("assertCartTotalNotExceeds")
    def assertCartTotalNotExceeds(self, budgetPerItem: float, itemsCount: int) -> None:
        # Verifies the cart total is within budgetPerItem multiplied by itemsCount.
        threshold = budgetPerItem * itemsCount
        trace_dir = PROJECT_ROOT / self.config.get("trace_dir", "reports/traces")
        trace_dir.mkdir(parents=True, exist_ok=True)
        trace_path = trace_dir / "cart_assertion_trace.zip"

        self.page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        try:
            self.cart_page.open_cart()
            actual_total = self.cart_page.get_cart_total()
            self.screenshot_helper.capture(self.page, "cart_total_assertion")

            allure.attach(
                f"Threshold: {threshold}\nActual: {actual_total}",
                name="Cart total comparison",
                attachment_type=allure.attachment_type.TEXT,
            )

            assert actual_total <= threshold, (
                f"Cart total {actual_total} exceeds threshold {threshold} "
                f"({budgetPerItem} x {itemsCount})"
            )
        finally:
            self.page.context.tracing.stop(path=str(trace_path))
            self.screenshot_helper.attach_trace(trace_path, name="Cart assertion trace")
