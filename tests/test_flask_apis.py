"""
Test the Flask app APIs (person search, org search, profile, org profile).

Usage:
  1. Start the app in another terminal:  python flask_app.py
  2. Run this script:                    python tests/test_flask_apis.py

Or with pytest (if installed):
  pytest tests/test_flask_apis.py -v

Requires: requests (already in requirements.txt)
"""

import json
import sys
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

# Change if you run Flask on another host/port
BASE_URL = "http://127.0.0.1:5000"


def test_get_index():
    """GET / should return 200 and HTML."""
    r = requests.get(BASE_URL, timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "html" in r.headers.get("Content-Type", "").lower() or "text/html" in r.text.lower()
    print("  GET /  -> 200 OK")


def test_api_search_person():
    """POST /api/search with a person name returns candidates."""
    r = requests.post(
        urljoin(BASE_URL, "/api/search"),
        json={"query": "Satya Nadella"},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code} - {r.text[:200]}"
    data = r.json()
    assert "candidates" in data, f"Response should have 'candidates': {list(data.keys())}"
    print(f"  POST /api/search (person) -> 200, candidates: {len(data['candidates'])}")


def test_api_search_direct_url():
    """POST /api/search with a direct LinkedIn URL returns single candidate."""
    r = requests.post(
        urljoin(BASE_URL, "/api/search"),
        json={"query": "https://www.linkedin.com/in/satyanadella"},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert "candidates" in data and len(data["candidates"]) >= 1
    assert "linkedin.com/in/" in data["candidates"][0].get("url", "")
    print("  POST /api/search (direct URL) -> 200, 1 candidate")


def test_api_org_search():
    """POST /api/org/search with company name returns company candidates."""
    r = requests.post(
        urljoin(BASE_URL, "/api/org/search"),
        json={"query": "Microsoft"},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert "candidates" in data
    print(f"  POST /api/org/search -> 200, candidates: {len(data['candidates'])}")


def test_api_search_missing_query():
    """POST /api/search without query returns 400."""
    r = requests.post(
        urljoin(BASE_URL, "/api/search"),
        json={},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code == 400
    print("  POST /api/search (no query) -> 400")


def run_all():
    print("Flask API tests (ensure flask_app.py is running on port 5000)\n")
    try:
        test_get_index()
        test_api_search_person()
        test_api_search_direct_url()
        test_api_org_search()
        test_api_search_missing_query()
        print("\nAll checks passed.")
        return 0
    except requests.exceptions.ConnectionError:
        print("\nCould not connect to Flask. Start the app first:")
        print("  python flask_app.py")
        return 1
    except AssertionError as e:
        print(f"\nAssertion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_all())
