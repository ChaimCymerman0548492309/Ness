# ניתוח סטטי של קוד באגי שנוצר ע"י AI

קובץ היעד לבדיקה: `resources/buggy_ai_test.py`

הקוד נועד לבצע תרחיש e2e דמוי eBay — חיפוש מוצרים תחת מחיר מקסימלי, הוספה לסל ואימות סכום.  
להלן **לפחות 3 בעיות מהותיות** שזוהו בבדיקה סטטית (ללא הרצה), כולל הסבר והצעת תיקון.

---

## בעיה 1: Locators שגויים ולא עמידים (Selectors)

### מה הבעיה?

הקוד משתמש ב-selectors גנריים שלא תואמים את מבנה ה-DOM האמיתי של eBay:

```python
page.fill("#search", query)
page.click("button")
items = page.query_selector_all(".item")
```

- `#search` — אין אלמנט כזה ב-eBay; שדה החיפוש הוא בדרך כלל `#gh-ac` או `input[name="_nkw"]`.
- `page.click("button")` — לוחץ על **הכפתור הראשון** בעמוד (לעיתים cookie banner, תפריט ניווט וכו'), לא בהכרח על כפתור החיפוש.
- `.item` — מחלקת תוצאות החיפוש ב-eBay היא `s-item`, לא `item`.

### השלכות

- החיפוש לא יתבצע או ילחץ על אלמנט שגוי.
- לולאת האיסוף תחזיר 0 פריטים גם כשיש תוצאות.
- הבדיקה תיכשל באופן לא דטרמיניסטי (flaky) בין סביבות.

### תיקון מוצע

```python
search_box = page.locator('#gh-ac, input[name="_nkw"]').first
search_box.fill(query)
page.locator('#gh-search-btn, button[type="submit"]').first.click()
page.wait_for_load_state("domcontentloaded")

items = page.locator("li.s-item").all()
```

**עקרון:** להשתמש ב-Playwright Locators, selectors ספציפיים, ו-`wait_for_load_state` במקום `wait_for_timeout` קבוע.

---

## בעיה 2: פרסור מחיר שגוי — `inner_text()` על כל הפריט

### מה הבעיה?

```python
price_text = item.inner_text()
price = float(price_text.replace("$", ""))
if price < max_price:
```

1. `inner_text()` על כל כרטיס הפריט מחזיר **את כל הטקסט** (כותרת, מחיר, משלוח, "מומלץ" וכו') — לא רק מחיר.
2. `float("...")` על מחרוזת מעורבת יזרוק `ValueError`.
3. טווחי מחיר (`$50 to $100`) לא מטופלים.
4. מפרידי אלפים (`1,299.99`) לא מנוקים.
5. התנאי `price < max_price` — לפי האפיון נדרש `<=` (שווה או נמוך).

### השלכות

- קריסת הבדיקה או סינון שגוי של פריטים.
- פריטים במחיר בדיוק `max_price` ייפלטו שלא לצורך.

### תיקון מוצע

```python
import re

def parse_price(raw: str) -> float | None:
    match = re.search(r"[\d,]+\.?\d*", raw.replace(",", ""))
    return float(match.group()) if match else None

price_el = item.locator(".s-item__price").first
price = parse_price(price_el.inner_text())
if price is not None and price <= max_price:
    ...
```

**עקרון:** לחלץ מחיר מאלמנט ייעודי, עם regex וטיפול ב-edge cases.

---

## בעיה 3: חוסר Pagination — לא עומד בדרישת `limit`

### מה הבעיה?

```python
for item in items:
    ...
    if len(urls) == limit:
        break
return urls
```

הלולאה רצה **רק על עמוד החיפוש הנוכחי**. לפי האפיון:

> אם יש פחות מ-5 פריטים בעמוד — יש לעבור לעמוד הבא ולהמשיך לאסוף עד `limit` או עד שנגמרים העמודים.

הקוד מחזיר פחות מ-`limit` גם כשיש מספיק פריטים בעמודים הבאים.

### תיקון מוצע

```python
collected: list[str] = []
while len(collected) < limit:
    for item in page.locator("li.s-item").all():
        # ... איסוף פריטים ...
        if len(collected) >= limit:
            break
    next_btn = page.locator('a.pagination__next, a[rel="next"]').first
    if not next_btn.is_visible():
        break
    next_btn.click()
    page.wait_for_load_state("domcontentloaded")
return collected[:limit]
```

---

## בעיה 4: `get_attribute("href")` ללא בדיקת null

### מה הבעיה?

```python
link = item.query_selector("a")
urls.append(link.get_attribute("href"))
```

- אם `query_selector` מחזיר `None` — `AttributeError`.
- אם `href` חסר — נוסף `None` לרשימה.
- אין סינון קישורי פרסומת ("Shop on eBay").

### תיקון מוצע

```python
link = item.locator("a.s-item__link").first
href = link.get_attribute("href")
title = item.locator(".s-item__title").inner_text()
if href and "shop on ebay" not in title.lower():
    urls.append(href)
```

---

## בעיה 5: אימות סכום סל — `<` במקום `<=` ו-selector לא אמין

### מה הבעיה?

```python
total_text = page.inner_text(".total")
total = float(total_text)
assert total < budget_per_item * items_count
```

1. `.total` — class גנרי שלא בהכרח קיים בעמוד הסל של eBay.
2. `inner_text` על selector שמחזיר מספר אלמנטים עלול להחזיר טקסט מורכב.
3. `total < threshold` — לפי האפיון: **"אינו עולה על"** → `<=`.
4. אין צילום מסך / trace כנדרש.

### תיקון מוצע

```python
total = parse_price(page.locator('[data-testid="TOTAL"], .subtotal').first.inner_text())
threshold = budget_per_item * items_count
assert total is not None and total <= threshold, (
    f"Cart total {total} exceeds {threshold}"
)
page.screenshot(path="reports/cart_assertion.png")
```

---

## בעיה 6: `add_items_to_cart` — ללא וריאנטים, ללא screenshot, `go_back` לא אמין

### מה הבעיה?

```python
def add_items_to_cart(page: Page, urls):
    for url in urls:
        page.goto(url)
        page.click("text=Add to cart")
        page.go_back()
```

- לא בוחר מידה/צבע/כמות כנדרש.
- `"text=Add to cart"` עלול להיכשל כשהכפתור מוסתר או שונה.
- `go_back()` לא מבטיח חזרה לעמוד החיפוש (טאבים, redirects).
- אין screenshot log לכל פריט.

### תיקון מוצע

ראו מימוש ב-`services/cart_service.py` ו-`pages/product_page.py` בפרויקט זה.

---

## בעיה 7: Login — URL ו-selectors לא תקינים

```python
page.goto("https://www.ebay.com/login")
page.fill("#username", username)
```

eBay משתמש ב-`signin.ebay.com` עם `#userid` ו-`#pass`, לא בנתיב `/login` עם `#username`.

---

## סיכום

| # | קטגוריה | חומרה |
|---|---------|--------|
| 1 | Locators שגויים | גבוהה |
| 2 | פרסור מחיר | גבוהה |
| 3 | חוסר Pagination | גבוהה |
| 4 | Null safety ב-href | בינונית |
| 5 | אימות סל שגוי | בינונית |
| 6 | addItemsToCart לא שלם | בינונית |
| 7 | Login שגוי | בינונית |

**מסקנה:** קוד שנוצר ע"י AI דורש review ידני — במיוחד סלקטורים, המתנות, pagination, ופרסור נתונים דינמיים מאתרי מסחר.
