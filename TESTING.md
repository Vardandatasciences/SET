# How to Test SET (Flask app & APIs)

## 1. Run the Flask app

From the project root:

```bash
python flask_app.py
```

The app will start at **http://127.0.0.1:5000**. Open that URL in a browser.

---

## 2. Test in the browser

- **Home page**: Go to `http://127.0.0.1:5000`. Enter a name, choose a source (e.g. "Internet"), and submit to test the main form.
- **Person flow**: Use the UI that calls `/api/search` (type a name) then `/api/profile` (pick a candidate) to test person search and profile extraction.
- **Organization flow**: Use the org search and org profile actions to test company search and `scrape_organization`.

Watch the terminal where `flask_app.py` is running for logs (e.g. `[search_linkedin]`, `[api_search]`, Selenium fallback messages).

---

## 3. Test APIs with curl (PowerShell)

Start the app first, then in another terminal:

**Person search**
```powershell
curl -X POST http://127.0.0.1:5000/api/search -H "Content-Type: application/json" -d "{\"query\": \"Satya Nadella\"}"
```

**Organization search**
```powershell
curl -X POST http://127.0.0.1:5000/api/org/search -H "Content-Type: application/json" -d "{\"query\": \"Microsoft\"}"
```

**Get profile (name or LinkedIn URL)** — can trigger Selenium + Groq pipeline:
```powershell
curl -X POST http://127.0.0.1:5000/api/profile -H "Content-Type: application/json" -d "{\"query\": \"https://www.linkedin.com/in/satyanadella\"}"
```

**Get org profile**
```powershell
curl -X POST http://127.0.0.1:5000/api/org/profile -H "Content-Type: application/json" -d "{\"query\": \"Microsoft\"}"
```

---

## 4. Run the automated API test script

From the project root:

```bash
# Terminal 1: start the app
python flask_app.py

# Terminal 2: run tests
python tests/test_flask_apis.py
```

The script checks:

- `GET /` returns 200
- `POST /api/search` with a name returns `candidates`
- `POST /api/search` with a direct LinkedIn URL returns one candidate
- `POST /api/org/search` returns company candidates
- `POST /api/search` with no query returns 400

---

## 5. Test Selenium fallback

Selenium is used when **Google/DuckDuckGo HTML** returns no results:

- **Person search**: If you’re in a region or network where Google blocks or returns empty HTML for `site:linkedin.com/in`, the app will try Selenium (Google + Bing) automatically. Check the Flask terminal for lines like `[search_linkedin] no HTML candidates, trying Selenium _find_linkedin_url`.
- **Org search**: Same for `site:linkedin.com/company`; you’ll see `[search_linkedin_org] no HTML candidates, trying Selenium find_linkedin_company_urls`.

To force Selenium for search (for debugging):

- Use a query that’s unlikely to appear in the first HTML response, or
- Temporarily break the HTML path (e.g. wrong `HEADERS` or URL) so the code falls back to Selenium.

**Selenium requirements**: Chrome (or Chromium) and `selenium` installed. If Selenium isn’t available, the app still works using requests + BeautifulSoup; only the fallback is skipped.

---

## 6. Optional: pytest

If you use pytest:

```bash
pip install pytest
pytest tests/test_flask_apis.py -v
```

Make sure the Flask app is running on port 5000 before running the tests.
