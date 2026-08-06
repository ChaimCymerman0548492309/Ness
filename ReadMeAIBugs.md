# Static Review of Buggy Test Code

Target file: `resources/buggy_ai_test.py`

This document reviews a deliberately flawed Playwright test sample. The review is static only; the file is not meant to be executed.

The intended scenario is an e-commerce E2E flow:

1. Search products by name.
2. Keep products whose price is less than or equal to the budget.
3. Add matching products to the cart.
4. Assert that the cart total does not exceed the expected budget.

---

## Issue 1: Weak and incorrect selectors

### Problem

```python
page.fill("#search", query)
page.click("button")
items = page.query_selector_all(".item")
```

The selectors are too generic or do not match common eBay page structure:

- `#search` is not the usual eBay search input. Common selectors are `#gh-ac` or `input[name="_nkw"]`.
- `page.click("button")` clicks the first button on the page, which may be a cookie banner or another unrelated button.
- `.item` is not the usual result item class. Search results commonly use `li.s-item`.

### Impact

- Search may not run.
- The wrong button may be clicked.
- The item collection may return zero results even when results exist.

### Suggested fix

```python
search_box = page.locator('#gh-ac, input[name="_nkw"]').first
search_box.fill(query)
page.locator('#gh-search-btn, button[type="submit"]').first.click()
page.wait_for_load_state("domcontentloaded")

items = page.locator("li.s-item").all()
```

---

## Issue 2: Price parsing reads the entire item card

### Problem

```python
price_text = item.inner_text()
price = float(price_text.replace("$", ""))
if price < max_price:
```

`inner_text()` on the whole item card returns title, shipping text, labels, and price together. This cannot be parsed safely with `float()`.

Other problems:

- Price ranges are not handled.
- Thousands separators are not handled.
- The comparison uses `<` instead of `<=`.

### Impact

- `ValueError` may be raised.
- Items may be filtered incorrectly.
- Items exactly equal to `max_price` are rejected even though they should be accepted.

### Suggested fix

```python
import re


def parse_price(raw: str) -> float | None:
    match = re.search(r"[\d,]+\.?\d*", raw)
    if not match:
        return None
    return float(match.group().replace(",", ""))


price_text = item.locator(".s-item__price").first.inner_text()
price = parse_price(price_text)
if price is not None and price <= max_price:
    ...
```

---

## Issue 3: Missing pagination

### Problem

```python
for item in items:
    ...
    if len(urls) == limit:
        break
return urls
```

The code checks only the current search result page. If fewer than `limit` matching items are found, it does not continue to the next result page.

### Impact

The function may return fewer URLs than required even when more matching products exist on later pages.

### Suggested fix

```python
collected: list[str] = []

while len(collected) < limit:
    for item in page.locator("li.s-item").all():
        if len(collected) >= limit:
            break

        # collect matching items here

    next_button = page.locator('a.pagination__next, a[rel="next"]').first
    if not next_button.is_visible():
        break

    next_button.click()
    page.wait_for_load_state("domcontentloaded")

return collected[:limit]
```

---

## Issue 4: Missing null checks for product links

### Problem

```python
link = item.query_selector("a")
urls.append(link.get_attribute("href"))
```

The code assumes that every item has a link. If `query_selector("a")` returns `None`, the test raises `AttributeError`.

It also appends missing or irrelevant links without validation.

### Impact

- The test can crash on incomplete result cards.
- Invalid URLs may be returned.
- Promotional links may be included.

### Suggested fix

```python
link = item.locator("a.s-item__link").first
href = link.get_attribute("href")
title = item.locator(".s-item__title").first.inner_text()

if href and "shop on ebay" not in title.lower():
    urls.append(href)
```

---

## Issue 5: Cart total assertion uses a weak selector and wrong comparison

### Problem

```python
total_text = page.inner_text(".total")
total = float(total_text)
assert total < budget_per_item * items_count
```

Problems:

- `.total` is too generic and may not exist.
- The text may contain labels or currency symbols.
- The assertion uses `<` instead of `<=`.
- There is no screenshot or trace for evidence.

### Impact

- The total may not be found.
- The total may be parsed incorrectly.
- A valid total equal to the threshold may fail.
- The report has no useful evidence for debugging.

### Suggested fix

```python
total_text = page.locator('[data-testid="TOTAL"], .subtotal').first.inner_text()
total = parse_price(total_text)
threshold = budget_per_item * items_count

assert total is not None and total <= threshold, (
    f"Cart total {total} exceeds threshold {threshold}"
)

page.screenshot(path="reports/cart_assertion.png", full_page=True)
```

---

## Issue 6: Add-to-cart flow is incomplete

### Problem

```python
def add_items_to_cart(page: Page, urls):
    for url in urls:
        page.goto(url)
        page.click("text=Add to cart")
        page.go_back()
```

Problems:

- Product variants are not selected.
- The Add to cart selector is too broad.
- Some products cannot be added without size, color, or quantity selection.
- `go_back()` does not always return to the search page.
- No screenshot is saved after adding an item.

### Impact

The flow is likely to fail on real product pages and provides no useful report evidence.

### Suggested fix

Use dedicated page objects:

- `ProductPage.open_product()`
- `ProductPage.select_random_variants()`
- `ProductPage.add_to_cart()`
- `ScreenshotHelper.capture()`
- `CartService._return_to_search_context()`

---

## Issue 7: Login URL and selectors are incorrect

### Problem

```python
page.goto("https://www.ebay.com/login")
page.fill("#username", username)
page.fill("#password", password)
page.click("#login-button")
```

These selectors do not match common eBay sign-in pages. Common fields include `#userid`, `#pass`, `#signin-continue-btn`, and `#sgnBt`.

### Impact

The login flow will not work reliably.

### Suggested fix

```python
page.goto("https://www.ebay.com")
page.locator('a[href*="signin.ebay"], a:has-text("Sign in")').first.click()
page.locator("#userid").fill(username)
page.locator("#signin-continue-btn").click()
page.locator("#pass").fill(password)
page.locator("#sgnBt").click()
page.wait_for_load_state("domcontentloaded")
```

---

## Summary

| # | Area | Severity |
|---|------|----------|
| 1 | Selectors | High |
| 2 | Price parsing | High |
| 3 | Pagination | High |
| 4 | Link null safety | Medium |
| 5 | Cart total assertion | Medium |
| 6 | Add-to-cart flow | Medium |
| 7 | Login flow | Medium |

The corrected framework addresses these issues with page objects, resilient selectors, price parsing, pagination, variant selection, screenshots, traces, and data-driven scenarios.
