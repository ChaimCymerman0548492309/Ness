# Requirements Compliance Checklist

This document maps every assignment requirement to its implementation in the project.

## General Requirements

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| E2E commerce scenario (search, price filter, cart, total validation) | ✅ | `tests/test_ebay_e2e.py` — full flow |
| Playwright framework | ✅ | `requirements.txt`, `conftest.py` |
| Python language | ✅ | All source files in Python 3.11+ |
| OOP development | ✅ | Classes in `pages/`, `services/`, `utils/`, `ebay_automation.py` |
| Page Object Model (POM) | ✅ | `pages/` directory |
| Data-Driven (JSON/CSV/YAML) | ✅ | `data/test_scenarios.json`, `data/test_scenarios.yaml`, `DataLoader` |
| Reports (Allure / HTML / JUnit XML) | ✅ | `pytest.ini` → Allure, HTML, JUnit XML |
| Clean architecture (SRP, Utils) | ✅ | Separated layers: pages / services / utils / config |

---

## Four Core Functions

### 1. Authentication (`authenticate`)

| Requirement | Status | Location |
|-------------|--------|----------|
| Login function exists | ✅ | `AuthService.authenticate()` |
| Guest stub when no credentials | ✅ | `LoginPage.continue_as_guest()` |
| ENV-based credentials | ✅ | `EBAY_USERNAME`, `EBAY_PASSWORD` in `.env` |

### 2. `search_items_by_name_under_price(query, max_price, limit=5)`

| Requirement | Status | Location |
|-------------|--------|----------|
| Search by query | ✅ | `SearchPage.search()` |
| Apply min/max price filter when available | ✅ | `SearchPage.apply_price_filter()` |
| XPath-based item collection | ✅ | `SearchPage.collect_item_urls_under_price_xpath()` |
| Price <= maxPrice validation | ✅ | `PriceParser.is_within_budget()` |
| Pagination via Next button | ✅ | `SearchPage.go_to_next_page()` |
| Return up to `limit` URLs (fewer if unavailable) | ✅ | Loop stops when limit reached or pages exhausted |
| Return 0 if nothing found | ✅ | Returns empty list |

### 3. `add_items_to_cart(urls)`

| Requirement | Status | Location |
|-------------|--------|----------|
| Loop over each URL | ✅ | `CartService.add_items_to_cart()` |
| Open product page | ✅ | `ProductPage.open_product()` |
| Random variant selection (size/color/qty) | ✅ | `ProductPage.select_random_variants()` |
| Click "Add to cart" | ✅ | `ProductPage.add_to_cart()` |
| Return to search screen/tab | ✅ | `CartService._return_to_search_context()` |
| Screenshot log per item | ✅ | `ScreenshotHelper.capture()` |

### 4. `assert_cart_total_not_exceeds(budget_per_item, items_count)`

| Requirement | Status | Location |
|-------------|--------|----------|
| Open shopping cart | ✅ | `CartPage.open_cart()` |
| Read subtotal/total | ✅ | `CartPage.get_cart_total()` |
| Threshold = budgetPerItem × itemsCount | ✅ | `CartAssertionService.assert_cart_total_not_exceeds()` |
| Assert total does not exceed threshold | ✅ | `assert actual_total <= threshold` |
| Screenshot / Trace of cart page | ✅ | Screenshot + Playwright trace attached to Allure |

---

## Full Scenario Example

```python
urls = search_items_by_name_under_price("shoes", 220, 5)
add_items_to_cart(urls)
assert_cart_total_not_exceeds(220, len(urls))
```

Implemented in: `tests/test_ebay_e2e.py::test_full_e2e_shopping_flow`

---

## AI Bug Exercise

| Requirement | Status | Location |
|-------------|--------|----------|
| Static code review (no execution) | ✅ | `ReadMeAIBugs.md` |
| At least 3 bugs identified | ✅ | 7 bugs documented |
| Detailed explanation per bug | ✅ | Each section has "What is the problem?" + impact |
| Suggested fix with code lines | ✅ | "Suggested fix" blocks per bug |
| Target file | ✅ | `resources/buggy_ai_test.py` |

---

## Submission Requirements

| Requirement | Status | Location |
|-------------|--------|----------|
| README — how to run | ✅ | `README.md` |
| README — architecture | ✅ | `README.md` + `docs/ARCHITECTURE.md` |
| README — limitations/assumptions | ✅ | `README.md` |
| Test report (Allure / HTML / JUnit) | ✅ | `reports/` after `pytest` |

---

## Evaluation Criteria Mapping

| Weight | Criterion | Implementation |
|--------|-----------|----------------|
| 45% | Architecture, POM, OOP, SRP, Utils | `pages/`, `services/`, `utils/`, `ebay_automation.py` |
| 35% | Robustness, smart locators, paging, variants, price parsing | XPath, fallback selectors, `PriceParser`, pagination |
| 15% | Data-Driven, ENV, profiles | `data/`, `config/settings.yaml`, `.env` |
| 15% | Reports & documentation | Allure, HTML, JUnit, README, this file |
