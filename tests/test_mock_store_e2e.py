"""Focused mock-store coverage for pagination and multi-price filtering."""

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.search_page import SearchPage
from utils.config_loader import ConfigLoader
from utils.price_parser import PriceParser


@pytest.mark.smoke
@pytest.mark.mock_store
def test_search_pagination_clicks_next(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    # Proves SearchPage.go_to_next_page() clicks Next and loads the following results page.
    search_page = SearchPage(page, app_config)
    search_page.search("shoes", max_price=220)

    page_status = page.get_by_text("Showing page")
    page_one_titles = [
        title.strip()
        for title in page.locator(".s-item__title").all_inner_texts()
        if title.strip() and "shop on ebay" not in title.lower()
    ]

    assert "page 1" in page_status.inner_text().lower()
    assert search_page.go_to_next_page() is True

    page_two_titles = [
        title.strip()
        for title in page.locator(".s-item__title").all_inner_texts()
        if title.strip()
    ]

    assert "page 2" in page_status.inner_text().lower()
    assert page_one_titles
    assert page_two_titles
    assert page_one_titles != page_two_titles


@pytest.mark.smoke
@pytest.mark.mock_store
def test_price_filter_applied_three_times_with_changing_max(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    # Applies the price filter three times in one run, each time with a different max price.
    search_page = SearchPage(page, app_config)
    search_page.search("shoes", max_price=220)

    filter_prices = [220, 100, 60]
    for max_price in filter_prices:
        with allure.step(f"Apply price filter with max_price={max_price}"):
            search_page.apply_price_filter(max_price=max_price)

            assert page.locator('input[name="_udhi"]').input_value() == str(int(max_price))
            assert f"filtered max price: ${int(max_price)}" in page.get_by_text(
                "Filtered max price"
            ).inner_text().lower()

            product_prices = page.locator("li.s-item:not(.sponsored) .s-item__price")
            assert product_prices.count() > 0
            for index in range(product_prices.count()):
                price_text = product_prices.nth(index).inner_text()
                assert PriceParser.is_within_budget(price_text, max_price), (
                    f"Visible price {price_text!r} exceeds filter {max_price}"
                )
