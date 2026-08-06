"""Deterministic E2E coverage for the commerce flow using mocked eBay pages."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from playwright.sync_api import Page, Route

from ebay_automation import EbayAutomation
from utils.config_loader import ConfigLoader
from utils.data_loader import DataLoader


PRODUCTS = [
    {"id": "shoes-1", "title": "Running shoes", "price": 120},
    {"id": "shoes-2", "title": "Walking shoes", "price": 180},
    {"id": "shoes-3", "title": "Kids shoes", "price": 50},
    {"id": "shoes-4", "title": "Leather shoes", "price": 210},
    {"id": "shoes-5", "title": "Trail shoes", "price": 60},
    {"id": "shoes-6", "title": "Premium shoes", "price": 260},
]


@pytest.fixture
def mock_ebay_store(page: Page) -> None:
    # Fulfills ebay.com requests with deterministic pages while exercising real Playwright flows.
    cart_prices: list[float] = []

    def product_url(product: dict) -> str:
        return f"https://www.ebay.com/itm/{product['id']}?price={product['price']}"

    def search_page(page_number: int) -> str:
        page_size = 3
        start = (page_number - 1) * page_size
        visible_products = PRODUCTS[start : start + page_size]
        items = "\n".join(
            f"""
            <li class="s-item">
              <a class="s-item__link" href="{product_url(product)}">
                <span class="s-item__title">{product['title']}</span>
              </a>
              <span class="s-item__price">${product['price']:.2f}</span>
            </li>
            """
            for product in visible_products
        )
        next_link = ""
        if start + page_size < len(PRODUCTS):
            query = urlencode({"_nkw": "shoes", "_udlo": "0", "_udhi": "220", "_pgn": page_number + 1})
            next_link = f'<a class="pagination__next" rel="next" href="/sch/i.html?{query}">Next</a>'

        return f"""
        <html>
          <body>
            <input name="_udlo" aria-label="Minimum" value="0" />
            <input name="_udhi" aria-label="Maximum" value="220" />
            <button>Apply</button>
            <ul>{items}</ul>
            {next_link}
            <a id="gh-cart" href="/cart" aria-label="cart">Cart</a>
          </body>
        </html>
        """

    def product_page(price: str) -> str:
        return f"""
        <html>
          <body>
            <select class="x-msku__select">
              <option value="">Choose size</option>
              <option value="M">M</option>
              <option value="L">L</option>
            </select>
            <button id="atcRedesign_id" onclick="fetch('/cart/add?price={price}')">Add to cart</button>
            <a id="gh-cart" href="/cart" aria-label="cart">Cart</a>
          </body>
        </html>
        """

    def route_handler(route: Route) -> None:
        parsed = urlparse(route.request.url)
        params = parse_qs(parsed.query)

        if parsed.path.startswith("/sch/i.html"):
            page_number = int(params.get("_pgn", ["1"])[0])
            route.fulfill(status=200, content_type="text/html", body=search_page(page_number))
            return

        if parsed.path.startswith("/itm/"):
            price = params.get("price", ["0"])[0]
            route.fulfill(status=200, content_type="text/html", body=product_page(price))
            return

        if parsed.path == "/cart/add":
            cart_prices.append(float(params.get("price", ["0"])[0]))
            route.fulfill(status=200, content_type="text/plain", body="added")
            return

        if parsed.path == "/cart":
            total = sum(cart_prices)
            route.fulfill(
                status=200,
                content_type="text/html",
                body=f"<html><body><div data-testid=\"TOTAL\">Order total ${total:.2f}</div></body></html>",
            )
            return

        route.fulfill(
            status=200,
            content_type="text/html",
            body="<html><body><a id='gh-cart' href='/cart' aria-label='cart'>Cart</a></body></html>",
        )

    page.route("https://www.ebay.com/**", route_handler)


@pytest.mark.e2e
@pytest.mark.data_driven
@pytest.mark.mock_store
def test_full_e2e_shopping_flow_with_mock_store(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    # Proves the full required flow deterministically while live eBay remains optional.
    scenario = DataLoader().get_scenario("shoes_under_budget")
    automation = EbayAutomation(page, app_config)

    automation.authenticate()
    urls = automation.search_items_by_name_under_price(
        query=scenario["query"],
        max_price=scenario["max_price"],
        limit=scenario["limit"],
    )

    assert len(urls) == scenario["limit"]

    added_count = automation.add_items_to_cart(urls)
    assert added_count == len(urls)

    automation.assert_cart_total_not_exceeds(
        budget_per_item=scenario["budget_per_item"],
        items_count=added_count,
    )
