# Requirements Compliance — Section 4

This document **displays every assignment requirement** from section 4 and maps it to the Python + Playwright implementation.

Public API facade: [`ebay_automation.py`](../ebay_automation.py)

Function names match the brief **exactly**:

```python
automation.authenticate()
urls = automation.searchItemsByNameUnderPrice("shoes", 220, 5)
automation.addItemsToCart(urls)
automation.assertCartTotalNotExceeds(220, len(urls))
```

---

## 4. Project description — four core functions

| # | Requirement | Exact name in code | Status | Implementation |
|---|-------------|--------------------|--------|----------------|
| 1 | הזדהות | `authenticate()` | ✅ | `AuthService` → `LoginPage` |
| 2 | פונקציית חיפוש עם תנאי מחיר | `searchItemsByNameUnderPrice(query, maxPrice, limit=5)` | ✅ | `SearchService` → `SearchPage` |
| 3 | `addItemsToCart` | `addItemsToCart(urls)` | ✅ | `CartService` → `ProductPage` |
| 4 | `assertCartTotalNotExceeds` | `assertCartTotalNotExceeds(budgetPerItem, itemsCount)` | ✅ | `CartAssertionService` → `CartPage` |

---

## 4.1 Search with price condition

### Required signature (from brief)

```typescript
async function searchItemsByNameUnderPrice(
  query: string,
  maxPrice: number,
  limit = 5,
): Promise<string[]>
```

### Python (same names)

```python
def searchItemsByNameUnderPrice(
    query: str,
    maxPrice: float,
    limit: int = 5,
) -> list[str]
```

### Behavior checklist

| Requirement | Status | Where |
|-------------|--------|-------|
| Search by `query` | ✅ | `SearchPage.search(query, max_price=...)` |
| If a price filter exists on the page, use min/max to narrow results | ✅ | `SearchPage.apply_price_filter(min_price, max_price)` |
| Collect with **XPath** up to `limit` items whose price is **<= maxPrice** | ✅ | `SearchPage.collect_item_urls_under_price_xpath()` + `PriceParser.is_within_budget()` (`<=`) |
| Special case — fewer than `limit` items on the current page: if **Next** / paging exists, go to the next page and keep collecting until `limit` or pages end | ✅ | `SearchPage.go_to_next_page()` inside the collect loop |
| If no paging is available, return however many were found (even if less than `limit`) | ✅ | Loop exits when Next is missing; returns `collected[:limit]` |
| Return: array of URLs (up to `limit`) that meet the price condition | ✅ | `list[str]` of product hrefs |
| If fewer found, return what exists (**0 is valid**) | ✅ | Empty list when nothing qualifies |

### Usage example from brief

```python
urls = automation.searchItemsByNameUnderPrice("shoes", 220, 5)
```

---

## 4.2 Add items to cart

### Required signature

```typescript
async function addItemsToCart(urls: string[]): Promise<void>
```

### Python (same name)

```python
def addItemsToCart(urls: list[str]) -> None
```

### Behavior checklist

| Requirement | Status | Where |
|-------------|--------|-------|
| Loop over every URL and open the product page | ✅ | `CartService.addItemsToCart()` → `ProductPage.open_product()` |
| If variants are required (size/color/qty), choose random available values | ✅ | `ProductPage.select_random_variants()` (called from `add_to_cart`) |
| Click **Add to cart** | ✅ | `ProductPage.add_to_cart()` |
| Return to the search screen / tab | ✅ | `CartService._return_to_search_context()` |
| Save a screenshot log for every added item | ✅ | `ScreenshotHelper.capture(... added_to_cart_item_N)` → `reports/screenshots/` + Allure |

---

## 4.3 Assert cart total does not exceed budget

### Required signature

```typescript
async function assertCartTotalNotExceeds(
  budgetPerItem: number,
  itemsCount: number,
): Promise<void>
```

### Python (same name)

```python
def assertCartTotalNotExceeds(
    budgetPerItem: float,
    itemsCount: int,
) -> None
```

### Behavior checklist

| Requirement | Status | Where |
|-------------|--------|-------|
| Open the shopping cart | ✅ | `CartPage.open_cart()` |
| Read subtotal / order total as shown on the page | ✅ | `CartPage.get_cart_total()` + `PriceParser` |
| Compute threshold: `budgetPerItem * itemsCount` | ✅ | `threshold = budgetPerItem * itemsCount` |
| Assert total does **not exceed** the threshold (`total <= threshold`) | ✅ | `assert actual_total <= threshold` |
| Save Screenshot / Trace of the cart page | ✅ | Screenshot via `ScreenshotHelper` + Playwright `tracing` ZIP in `reports/traces/` attached to Allure |

---

## Full scenario from the brief

| Step | Brief | Code |
|------|-------|------|
| 1 | `searchItemsByNameUnderPrice("shoes", 220, 5)` | same name |
| 2 | `addItemsToCart(urls)` | same name |
| 3 | `assertCartTotalNotExceeds(220, urls.length)` | `assertCartTotalNotExceeds(220, len(urls))` |

Implemented in: `tests/test_ebay_e2e.py::test_full_e2e_shopping_flow`

```python
urls = automation.searchItemsByNameUnderPrice(
    query=scenario["query"],
    maxPrice=scenario["max_price"],
    limit=scenario["limit"],
)
automation.addItemsToCart(urls)
automation.assertCartTotalNotExceeds(
    budgetPerItem=scenario["budget_per_item"],
    itemsCount=len(urls),
)
```

---

## Out of scope for section 4 (extra / supporting)

| Extra | Purpose |
|-------|---------|
| Mock store | Stable demos/reports without live CAPTCHA |
| Data-driven JSON/YAML | Assignment data-driven criterion |
| 3× price-filter smoke test | Extra UI coverage; not required by §4.1 |
| Click highlighter | Demo visibility only |

---

## Other assignment areas (summary)

| Area | Status | Location |
|------|--------|----------|
| POM / OOP / SRP / Utils | ✅ | `pages/`, `services/`, `utils/`, `ebay_automation.py` |
| Data-Driven JSON/YAML | ✅ | `data/`, `DataLoader` |
| Reports Allure / HTML / JUnit | ✅ | `pytest.ini`, `reports/` |
| Static AI code review | ✅ | `ReadMeAIBugs.md`, `resources/buggy_ai_test.py` |
| README + architecture | ✅ | `README.md`, `docs/ARCHITECTURE.md` |
