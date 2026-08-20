# סקירה סטטית — קוד בדיקה שנוצר ב-AI

הקוד שלהלן לא רץ כמו שצריך. הסקירה כאן היא בדיקה סטטית בלבד (בלי להריץ).

**קוד מקור (כפי שהגיע מהעובד):**
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

## 1. שגיאת הזחה — הקוד לא חוקי ב-Python

**שורות בעייתיות:**
```python
def test_search_functionality():
browser = sync_playwright().start().chromium.launch()
```

גוף הפונקציה חייב להיות מוזח פנימה. כפי שזה כתוב, Python יזרוק `IndentationError` עוד לפני ש-Pytest מגיע לבדיקה.

**תיקון:**
```python
def test_search_functionality():
    browser = sync_playwright().start().chromium.launch()
    page = browser.new_page()
    ...
```

---

## 2. ערבוב Selenium ו-Playwright

**שורה בעייתית:**
```python
from selenium import webdriver
```

ה-import של Selenium לא בשימוש בכלל, אבל Playwright כן. זה סימן קלאסי לקוד שה-AI "הדביק" משני מקורות — שני דрайверים שונים, API שונה, ולא עובדים יחד באותה בדיקה.

**תיקון:** להשאיר רק Playwright (או רק Selenium — לא את שניהם):
```python
from playwright.sync_api import sync_playwright
# מחק: from selenium import webdriver
```

---

## 3. ניהול משאבים לא תקין

**שורות בעייתיות:**
```python
browser = sync_playwright().start().chromium.launch()
...
browser.close()
```

קוראים ל-`.start()` על Playwright אבל אף פעם לא ל-`.stop()`. סגירת ה-browser בלבד עלולה להשאיר תהליך driver תלוי ברקע, במיוחד כשמריצים הרבה בדיקות.

**תיקון — context manager:**
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

## 4. `time.sleep` במקום המתנה מבוססת DOM

**שורות בעייתיות:**
```python
time.sleep(2)
...
time.sleep(3)
```

Sleep קבוע לא קשור לזמן טעינה אמיתי של הדף — על מכונה איטית הבדיקה נכשלת, על מכונה מהירה מבזבזים זמן. Playwright כבר ממתין אוטומטית לפעולות; כשצריך המתנה מפורשת, עדיף לחכות לאלמנט.

**תיקון:**
```python
search_box = page.locator("#search")
search_box.wait_for(state="visible", timeout=10_000)
search_box.fill("playwright testing")
page.locator(".button").click()
results = page.locator(".result-item")
results.first.wait_for(state="visible", timeout=10_000)
```

---

## 5. URL וסלקטורים שלא תואמים לאתר

**שורות בעייתיות:**
```python
page.goto("https://example.com")
search_box = page.locator("#search")
page.locator(".button").click()
results = page.locator(".result-item")
```

`example.com` הוא דף דוגמה — אין בו `#search`, `.button` או `.result-item`. גם `.button` גנרי מדי (יכול לפגוע בכפתור לא נכון). ה-AI כנראה המציא סלקטורים "סטנדרטיים" בלי לבדוק את ה-DOM האמיתי.

**תיקון:** לבחור אתר יעד אמיתי, לפתוח DevTools, ולכתוב locators ספציפיים. לדוגמה באתר עם חיפוש:
```python
page.goto("https://www.example-store.com/search")
search_box = page.get_by_role("searchbox", name="Search products")
search_box.fill("playwright testing")
page.get_by_role("button", name="Search").click()
results = page.locator("[data-testid='search-result']")
```

---

## 6. אין assertion — הבדיקה תמיד "עוברת"

**שורות בעייתיות:**
```python
results = page.locator(".result-item")
browser.close()
```

המשתנה `results` נוצר אבל לא נבדק. גם אם החיפוש נכשל או מחזיר 0 תוצאות, Pytest יסמן את הבדיקה כ-passed.

**תיקון:**
```python
results = page.locator(".result-item")
assert results.count() > 0, "Expected at least one search result"
assert "playwright" in results.first.inner_text().lower()
```

---

## סיכום

| # | בעיה | חומרה |
|---|------|--------|
| 1 | הזחה — SyntaxError | גבוהה |
| 2 | Selenium + Playwright מעורבבים | בינונית |
| 3 | `.start()` בלי `.stop()` | בינונית |
| 4 | `time.sleep` במקום wait | בינונית |
| 5 | URL/סלקטורים לא קיימים | גבוהה |
| 6 | אין assertion | גבוהה |

**גרסה מתוקנת (מינימלית):**
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

הערה: הסלקטורים בגרסה המתוקנת הם דוגמה — חייבים להתאים ל-DOM של האתר שבוחרים לבדוק.
