"""Deterministic mocked eBay HTML store for Playwright route interception."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse

from playwright.sync_api import Page, Route

PRODUCT_CATALOG: dict[str, list[dict]] = {
    "shoes": [
        {"id": "shoes-1", "title": "Running shoes", "price": 120, "seller": "Sport Direct", "shipping": "Free shipping", "thumb": "SHOE"},
        {"id": "shoes-2", "title": "Walking shoes", "price": 180, "seller": "Urban Outlet", "shipping": "$9.90 shipping", "thumb": "SHOE"},
        {"id": "shoes-3", "title": "Kids shoes", "price": 50, "seller": "Family Deals", "shipping": "Free returns", "thumb": "SHOE"},
        {"id": "shoes-4", "title": "Leather shoes", "price": 210, "seller": "Classic Store", "shipping": "Ships today", "thumb": "SHOE"},
        {"id": "shoes-5", "title": "Trail shoes", "price": 60, "seller": "Outdoor Hub", "shipping": "Free shipping", "thumb": "SHOE"},
        {"id": "shoes-6", "title": "Premium shoes", "price": 260, "seller": "Luxury Market", "shipping": "Express shipping", "thumb": "SHOE"},
    ],
    "headphones": [
        {"id": "hp-1", "title": "Wireless headphones", "price": 45, "seller": "Audio Hub", "shipping": "Free shipping", "thumb": "HP"},
        {"id": "hp-2", "title": "Studio headphones", "price": 70, "seller": "Sound Lab", "shipping": "$4.99 shipping", "thumb": "HP"},
        {"id": "hp-3", "title": "Kids headphones", "price": 25, "seller": "Family Deals", "shipping": "Free returns", "thumb": "HP"},
        {"id": "hp-4", "title": "Premium headphones", "price": 120, "seller": "Luxury Audio", "shipping": "Express shipping", "thumb": "HP"},
        {"id": "hp-5", "title": "Sport earbuds", "price": 55, "seller": "Outdoor Hub", "shipping": "Free shipping", "thumb": "HP"},
    ],
}

ALL_PRODUCTS: list[dict] = [item for items in PRODUCT_CATALOG.values() for item in items]

CLICK_HIGHLIGHT_STYLE = """
  .pw-auto-highlight {
    outline: 3px solid #ff6b00 !important;
    outline-offset: 2px !important;
    box-shadow:
      0 0 0 8px rgba(255, 107, 0, 0.35),
      0 0 22px rgba(255, 107, 0, 0.55) !important;
    filter: brightness(1.05);
    transition: outline 80ms ease, box-shadow 80ms ease !important;
    position: relative;
    z-index: 2147483646 !important;
  }
"""

CLICK_HIGHLIGHT_SCRIPT = """
<script>
(() => {
  if (window.__pwClickHighlightInstalled) return;
  window.__pwClickHighlightInstalled = true;
  const highlight = (target) => {
    const el = target && target.nodeType === 1 ? target : target && target.parentElement;
    if (!el || !el.classList) return;
    el.classList.add("pw-auto-highlight");
    setTimeout(() => el.classList.remove("pw-auto-highlight"), 450);
  };
  window.addEventListener("mousedown", (event) => highlight(event.target), true);
  window.addEventListener("click", (event) => highlight(event.target), true);
  window.addEventListener("focusin", (event) => highlight(event.target), true);
})();
</script>
"""

BASE_STYLE = """
<style>
  body {
    margin: 0;
    background: #f7f7f7;
    color: #191919;
    font-family: Arial, Helvetica, sans-serif;
  }
  .top-strip {
    background: #fff;
    border-bottom: 1px solid #ddd;
    color: #555;
    display: flex;
    font-size: 13px;
    justify-content: space-between;
    padding: 8px 28px;
  }
  .header {
    align-items: center;
    background: #fff;
    border-bottom: 1px solid #ddd;
    display: flex;
    gap: 18px;
    padding: 16px 28px;
  }
  .logo {
    font-size: 34px;
    font-weight: 700;
    letter-spacing: -2px;
  }
  .logo span:nth-child(1) { color: #e53238; }
  .logo span:nth-child(2) { color: #0064d2; }
  .logo span:nth-child(3) { color: #f5af02; }
  .logo span:nth-child(4) { color: #86b817; }
  .search-box {
    border: 2px solid #333;
    border-radius: 24px;
    flex: 1;
    font-size: 16px;
    padding: 12px 18px;
  }
  .search-button,
  .primary-button {
    background: #3665f3;
    border: 0;
    border-radius: 24px;
    color: #fff;
    cursor: pointer;
    font-size: 16px;
    padding: 12px 28px;
  }
  .page {
    display: grid;
    gap: 24px;
    grid-template-columns: 240px 1fr;
    padding: 24px 32px;
  }
  .filters,
  .summary-card,
  .product-panel {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    padding: 18px;
  }
  .filters h3,
  .results h2 {
    margin-top: 0;
  }
  .price-row {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }
  .price-row input {
    border: 1px solid #bbb;
    border-radius: 8px;
    padding: 10px;
    width: 80px;
  }
  .s-item {
    align-items: flex-start;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 12px;
    display: grid;
    gap: 18px;
    grid-template-columns: 150px 1fr 140px;
    list-style: none;
    margin-bottom: 14px;
    padding: 16px;
  }
  .thumb {
    align-items: center;
    background: linear-gradient(135deg, #e8eefc, #fff);
    border: 1px solid #ddd;
    border-radius: 10px;
    display: flex;
    font-size: 42px;
    height: 120px;
    justify-content: center;
  }
  .s-item__link {
    color: #111820;
    font-size: 18px;
    font-weight: 600;
    text-decoration: none;
  }
  .s-item__price {
    display: block;
    font-size: 22px;
    font-weight: 700;
    margin-top: 12px;
  }
  .meta,
  .shipping,
  .seller {
    color: #555;
    font-size: 14px;
    margin-top: 6px;
  }
  .badge {
    background: #f5af02;
    border-radius: 999px;
    display: inline-block;
    font-size: 12px;
    margin-bottom: 8px;
    padding: 4px 10px;
  }
  .pagination__next {
    background: #fff;
    border: 1px solid #3665f3;
    border-radius: 24px;
    color: #3665f3;
    display: inline-block;
    font-weight: 700;
    padding: 12px 26px;
    text-decoration: none;
  }
  .product-layout {
    display: grid;
    gap: 28px;
    grid-template-columns: 48% 1fr;
    padding: 32px;
  }
  .gallery {
    align-items: center;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 14px;
    display: flex;
    font-size: 120px;
    height: 460px;
    justify-content: center;
  }
  .variant-row {
    margin: 16px 0;
  }
  .variant-row label {
    display: block;
    font-weight: 700;
    margin-bottom: 6px;
  }
  select,
  #qtyTextBox {
    border: 1px solid #aaa;
    border-radius: 8px;
    font-size: 15px;
    padding: 10px;
    width: 220px;
  }
  .cart-layout {
    display: grid;
    gap: 24px;
    grid-template-columns: 1fr 330px;
    padding: 32px;
  }
  .cart-line {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 12px;
    margin-bottom: 12px;
    padding: 16px;
  }
  [data-testid="TOTAL"] {
    font-size: 26px;
    font-weight: 700;
    margin-top: 14px;
  }
""" + CLICK_HIGHLIGHT_STYLE + """
</style>
"""


def _products_for_query(query: str) -> list[dict]:
    normalized = (query or "shoes").strip().lower()
    if normalized in PRODUCT_CATALOG:
        return PRODUCT_CATALOG[normalized]
    for key, products in PRODUCT_CATALOG.items():
        if key in normalized or normalized in key:
            return products
    return PRODUCT_CATALOG["shoes"]


def install_mock_ebay_store(page: Page) -> None:
    """Route ebay.com traffic to deterministic HTML pages for the full commerce flow."""
    cart_prices: list[float] = []

    def product_url(product: dict) -> str:
        return f"https://www.ebay.com/itm/{product['id']}?price={product['price']}"

    def header(search_value: str = "shoes") -> str:
        return f"""
        <div class="top-strip">
          <div>Hi! Sign in or continue as guest</div>
          <div>Daily Deals | Help & Contact | Sell | Watchlist | My eBay</div>
        </div>
        <header class="header">
          <div class="logo"><span>e</span><span>b</span><span>a</span><span>y</span></div>
          <input class="search-box" name="_nkw" value="{search_value}" aria-label="Search for anything" />
          <button class="search-button">Search</button>
          <a id="gh-cart" href="/cart" aria-label="cart">Cart</a>
        </header>
        """

    def search_page(query: str, max_price: str, page_number: int) -> str:
        try:
            max_price_value = float(max_price) if max_price not in {"", None} else 9999.0
        except ValueError:
            max_price_value = 9999.0

        products = [
            product
            for product in _products_for_query(query)
            if product["price"] <= max_price_value
        ]
        page_size = 3
        start = (page_number - 1) * page_size
        visible_products = products[start : start + page_size]
        display_max = str(int(max_price_value)) if max_price_value < 9999 else (max_price or "9999")
        category = query.title() if query else "All"

        sponsored_item = ""
        if page_number == 1:
            sponsored_item = """
            <li class="s-item sponsored">
              <div class="thumb">AD</div>
              <div>
                <span class="badge">Sponsored</span>
                <a class="s-item__link" href="https://www.ebay.com/deals">
                  <span class="s-item__title">Shop on eBay</span>
                </a>
                <div class="meta">Promoted marketplace link</div>
                <span class="s-item__price">$9.99</span>
              </div>
              <div class="shipping">Ad placement</div>
            </li>
            """

        items = "\n".join(
            f"""
            <li class="s-item">
              <div class="thumb">{product.get('thumb', 'ITEM')}</div>
              <div>
                <a class="s-item__link" href="{product_url(product)}">
                  <span class="s-item__title">{product['title']}</span>
                </a>
                <div class="meta">New with box | Buy It Now</div>
                <div class="seller">Seller: {product['seller']}</div>
                <div class="shipping">{product['shipping']}</div>
                <span class="s-item__price">${product['price']:.2f}</span>
              </div>
              <div>
                <div class="badge">Top Rated</div>
                <div class="meta">30-day returns</div>
                <div class="meta">More options available</div>
              </div>
            </li>
            """
            for product in visible_products
        )

        next_link = ""
        if start + page_size < len(products):
            next_query = urlencode(
                {
                    "_nkw": query or "shoes",
                    "_udlo": "0",
                    "_udhi": display_max,
                    "_pgn": page_number + 1,
                }
            )
            next_link = f'<a class="pagination__next" rel="next" href="/sch/i.html?{next_query}">Next</a>'

        return f"""
        <html>
          <head>{BASE_STYLE}</head>
          <body>
            {header(query or "shoes")}
            <main class="page">
              <aside class="filters">
                <h3>Filters</h3>
                <p class="meta">Category: {category}</p>
                <p class="meta">Condition: New</p>
                <p class="meta">Buying format: Buy It Now</p>
                <h3>Price</h3>
                <div class="price-row">
                  <input name="_udlo" aria-label="Minimum" value="0" />
                  <input name="_udhi" aria-label="Maximum" value="{display_max}" />
                </div>
                <button
                  class="primary-button"
                  onclick="
                    const min = document.querySelector('input[name=_udlo]').value || '0';
                    const max = document.querySelector('input[name=_udhi]').value || '9999';
                    const q = document.querySelector('input[name=_nkw]').value || '{query or "shoes"}';
                    location.href = '/sch/i.html?' + new URLSearchParams({{
                      _nkw: q,
                      _udlo: min,
                      _udhi: max,
                      _pgn: '1'
                    }});
                  "
                >
                  Apply
                </button>
              </aside>
              <section class="results">
                <h2>Results for {query or "shoes"}</h2>
                <p class="meta">Showing page {page_number}. Filtered max price: ${display_max}.</p>
                <ul>{sponsored_item}{items}</ul>
                {next_link}
              </section>
            </main>
          {CLICK_HIGHLIGHT_SCRIPT}
          </body>
        </html>
        """

    def product_page(product: dict) -> str:
        thumb = product.get("thumb", "ITEM")
        return f"""
        <html>
          <head>{BASE_STYLE}</head>
          <body>
            {header()}
            <main class="product-layout">
              <section class="gallery">{thumb}</section>
              <section class="product-panel">
                <h1>{product['title']}</h1>
                <p class="seller">Seller: {product['seller']} | 98.7% positive feedback</p>
                <p class="meta">Condition: New with box</p>
                <div class="s-item__price">${product['price']:.2f}</div>
                <p class="shipping">{product['shipping']}</p>
                <div class="variant-row">
                  <label>Size</label>
                  <select class="x-msku__select">
                    <option value="">Choose size</option>
                    <option value="M">M</option>
                    <option value="L">L</option>
                  </select>
                </div>
                <div class="variant-row">
                  <label>Color</label>
                  <select class="x-msku__select">
                    <option value="">Choose color</option>
                    <option value="black">Black</option>
                    <option value="blue">Blue</option>
                  </select>
                </div>
                <div class="variant-row">
                  <label>Quantity</label>
                  <input id="qtyTextBox" name="quantity" value="1" />
                </div>
                <button
                  id="atcRedesign_id"
                  class="primary-button"
                  onclick="fetch('/cart/add?price={product['price']}')"
                >
                  Add to cart
                </button>
              </section>
            </main>
          {CLICK_HIGHLIGHT_SCRIPT}
          </body>
        </html>
        """

    def route_handler(route: Route) -> None:
        parsed = urlparse(route.request.url)
        params = parse_qs(parsed.query)

        if parsed.path.startswith("/sch/i.html"):
            query = params.get("_nkw", ["shoes"])[0]
            max_price = params.get("_udhi", ["9999"])[0]
            page_number = int(params.get("_pgn", ["1"])[0])
            route.fulfill(
                status=200,
                content_type="text/html",
                body=search_page(query, max_price, page_number),
            )
            return

        if parsed.path.startswith("/itm/"):
            product_id = parsed.path.rsplit("/", maxsplit=1)[-1]
            product = next((item for item in ALL_PRODUCTS if item["id"] == product_id), ALL_PRODUCTS[0])
            route.fulfill(status=200, content_type="text/html", body=product_page(product))
            return

        if parsed.path == "/cart/add":
            cart_prices.append(float(params.get("price", ["0"])[0]))
            route.fulfill(status=200, content_type="text/plain", body="added")
            return

        if parsed.path == "/cart":
            total = sum(cart_prices)
            lines = "\n".join(
                f'<div class="cart-line">Mock product #{index}: ${price:.2f}</div>'
                for index, price in enumerate(cart_prices, start=1)
            )
            route.fulfill(
                status=200,
                content_type="text/html",
                body=f"""
                <html>
                  <head>{BASE_STYLE}</head>
                  <body>
                    {header()}
                    <main class="cart-layout">
                      <section>
                        <h1>Shopping cart</h1>
                        {lines}
                      </section>
                      <aside class="summary-card">
                        <h2>Order summary</h2>
                        <div>Items: {len(cart_prices)}</div>
                        <div>Shipping: Included or shown by seller</div>
                        <div data-testid="TOTAL">Order total ${total:.2f}</div>
                      </aside>
                    </main>
                  {CLICK_HIGHLIGHT_SCRIPT}
                  </body>
                </html>
                """,
            )
            return

        route.fulfill(
            status=200,
            content_type="text/html",
            body=(
                f"<html><head>{BASE_STYLE}</head><body>{header()}"
                f"{CLICK_HIGHLIGHT_SCRIPT}</body></html>"
            ),
        )

    page.route("https://www.ebay.com/**", route_handler)
