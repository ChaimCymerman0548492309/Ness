# Static Review — `resources/buggy_ai_test.py`

Review only. Do not run this file.

The flow should be: search by name → filter by price → add to cart → assert total.

---

## 1. Wrong selectors (search)

**Code:**
```python
page.fill("#search", query)
page.click("button")
items = page.query_selector_all(".item")
```

`#search` and `.item` are not eBay selectors. `button` matches the first button on the page (cookie banner, menu, etc.).

**Fix:**
```python
page.locator('#gh-ac, input[name="_nkw"]').first.fill(query)
page.locator('#gh-search-btn, button[type="submit"]').first.click()
items = page.locator("li.s-item").all()
```

---

## 2. Price parsed from the whole card

**Code:**
```python
price_text = item.inner_text()
price = float(price_text.replace("$", ""))
if price < max_price:
```

`inner_text()` returns title + shipping + labels + price. `float()` will fail or return wrong values. Also uses `<` instead of `<=`.

**Fix:**
```python
price_text = item.locator(".s-item__price").first.inner_text()
# parse first number only, handle commas
if price is not None and price <= max_price:
```

Use a small helper (regex) like in `utils/price_parser.py`.

---

## 3. No pagination

**Code:**
```python
for item in items:
    ...
    if len(urls) == limit:
        break
return urls
```

Only the current page is scanned. If there are fewer than `limit` matches here, the code never clicks Next.

**Fix:** loop with `while len(collected) < limit`, and after each page try `a.pagination__next` / `a[rel="next"]` before giving up.

---

## 4. Missing link check + weak cart assert

**Search — code:**
```python
link = item.query_selector("a")
urls.append(link.get_attribute("href"))
```

If `link` is `None` → `AttributeError`. Sponsored items can slip in.

**Fix:** use `a.s-item__link`, check `href`, skip "Shop on eBay" titles.

**Cart — code:**
```python
total_text = page.inner_text(".total")
total = float(total_text)
assert total < budget_per_item * items_count
```

`.total` is too generic. Same parse/assert issues as above (`<=` not `<`). No screenshot for the report.

**Fix:**
```python
total_text = page.locator('[data-testid="TOTAL"], .subtotal').first.inner_text()
assert total <= budget_per_item * items_count
page.screenshot(path="reports/cart_assertion.png")
```

---

## 5. Incomplete add-to-cart

**Code:**
```python
page.goto(url)
page.click("text=Add to cart")
page.go_back()
```

No size/color/qty selection. `go_back()` may not return to search. No screenshot per item.

**Fix:** select variants first, use a specific Add button locator, return to search context explicitly, save a screenshot after each add (see `ProductPage` / `CartService` in this project).

---

## Summary

| Issue | Severity |
|-------|----------|
| Selectors | High |
| Price parsing | High |
| Pagination | High |
| Links + cart assert | Medium |
| Add to cart | Medium |

The main framework fixes these with POM, XPath collection, `PriceParser`, paging, and screenshots/traces.
