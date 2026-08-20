# Static Review — AI-Generated Test Code

The code below does not run as expected. This review is static only (not executed).

**Source code (as received from the teammate):**
```python
from playwright.sync_api import sync_playwright
from selenium import webdriver
import time

def test_search_functionality():
browser = sync_playwright().start().chromium.launch()
page
=
browser.new_page()
page.goto("https://example.com")
time.sleep(2)
search_box = page.locator("#search")
search_box.fill("playwright testing")
page.locator (".button").click()
time.sleep(3)
results = page.locator(".result-item")
browser.close()
```

---

## 1. Mixed Selenium and Playwright

**Problematic line:**
```python
from selenium import webdriver
```

The Selenium import is never used, while Playwright is. This is a common sign of AI-generated code pasted from two sources — different drivers, different APIs, and they do not work together in the same test.

**Fix:** keep Playwright only (or Selenium only — not both):
```python
from playwright.sync_api import sync_playwright
# remove: from selenium import webdriver
```

---

## 2. Improper resource cleanup

**Problematic lines:**
```python
browser = sync_playwright().start().chromium.launch()
...
browser.close()
```

`.start()` is called on Playwright but `.stop()` never is. Closing the browser alone can leave a driver process running in the background, especially when running many tests.

**Fix — use a context manager:**
```python
def test_search_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://example.com")
            ...
        finally:
            browser.close()
```

---

## 3. `time.sleep` instead of DOM-based waits

**Problematic lines:**
```python
time.sleep(2)
...
time.sleep(3)
```

Fixed sleeps are not tied to actual page load time — the test fails on a slow machine and wastes time on a fast one. Playwright already auto-waits on actions; when an explicit wait is needed, wait for an element instead.

**Fix:**
```python
search_box = page.locator("#search")
search_box.wait_for(state="visible", timeout=10_000)
search_box.fill("playwright testing")
page.locator(".button").click()
results = page.locator(".result-item")
results.first.wait_for(state="visible", timeout=10_000)
```

---

## 4. URL and selectors do not match the site

**Problematic lines:**
```python
page.goto("https://example.com")
search_box = page.locator("#search")
page.locator(".button").click()
results = page.locator(".result-item")
```

`example.com` is a placeholder page — it has no `#search`, `.button`, or `.result-item`. `.button` is also too generic (can match the wrong button). The AI likely invented “standard” selectors without checking the real DOM.

**Fix:** pick a real target site, open DevTools, and write specific locators. Example for a site with search:
```python
page.goto("https://www.example-store.com/search")
search_box = page.get_by_role("searchbox", name="Search products")
search_box.fill("playwright testing")
page.get_by_role("button", name="Search").click()
results = page.locator("[data-testid='search-result']")
```

---

## 5. No assertion — the test always “passes”

**Problematic lines:**
```python
results = page.locator(".result-item")
browser.close()
```

The `results` variable is created but never checked. Even if search fails or returns zero results, Pytest will mark the test as passed.

**Fix:**
```python
results = page.locator(".result-item")
assert results.count() > 0, "Expected at least one search result"
assert "playwright" in results.first.inner_text().lower()
```

---

## Summary

| # | Issue | Severity |
|---|-------|----------|
| 1 | Selenium + Playwright mixed | Medium |
| 2 | `.start()` without `.stop()` | Medium |
| 3 | `time.sleep` instead of wait | Medium |
| 4 | URL/selectors do not exist | High |
| 5 | No assertion | High |

**Minimal corrected version:**
```python
from playwright.sync_api import sync_playwright

def test_search_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://www.example-store.com/search")
            search_box = page.get_by_role("searchbox")
            search_box.wait_for(state="visible")
            search_box.fill("playwright testing")
            page.get_by_role("button", name="Search").click()
            results = page.locator("[data-testid='search-result']")
            results.first.wait_for(state="visible")
            assert results.count() > 0
        finally:
            browser.close()
```

Note: selectors in the corrected version are examples — they must match the DOM of the site under test.
