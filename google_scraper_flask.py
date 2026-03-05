"""
Small Flask UI + candidate selector for google_scraper.py
=========================================================

Flow:
  1) /api/search
       - Uses Google HTML results (no LinkedIn scraping)
       - Light Groq call to normalize just name + company for each candidate
       - Returns a list of candidates for user confirmation
  2) /api/profile
       - Runs the full pipeline (Selenium + Groq) ONLY for the selected candidate

Usage:
  set GROQ_API_KEY in your environment (.env is also supported by google_scraper)

  python google_scraper_flask.py

Then open: http://127.0.0.1:5000
"""

import re

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, Response
from groq import Groq

from google_scraper import GROQ_API_KEY, HEADERS, process_query


app = Flask(__name__)
groq_client = Groq(api_key=GROQ_API_KEY)


INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>LinkedIn Profile Extractor</title>
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #0f172a;
        color: #e5e7eb;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .app-shell {
        width: 100%;
        max-width: 960px;
        padding: 24px;
      }
      .card {
        background: radial-gradient(circle at top left, #1e293b, #020617);
        border-radius: 18px;
        padding: 24px 24px 20px;
        box-shadow:
          0 24px 60px rgba(15, 23, 42, 0.9),
          0 0 0 1px rgba(148, 163, 184, 0.15);
        border: 1px solid rgba(148, 163, 184, 0.35);
      }
      .title {
        font-size: 22px;
        font-weight: 650;
        letter-spacing: 0.02em;
        margin: 0 0 4px;
      }
      .subtitle {
        font-size: 13px;
        color: #9ca3af;
        margin: 0 0 18px;
      }
      .form-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 12px;
      }
      .form-row input {
        flex: 1 1 240px;
        padding: 10px 12px;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.5);
        background: rgba(15, 23, 42, 0.85);
        color: #e5e7eb;
        outline: none;
        font-size: 14px;
      }
      .form-row input:focus {
        border-color: #38bdf8;
        box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.5);
      }
      .btn {
        padding: 10px 16px;
        border-radius: 999px;
        border: none;
        background: linear-gradient(135deg, #38bdf8, #6366f1);
        color: #0b1120;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .btn:disabled {
        opacity: 0.55;
        cursor: default;
      }
      .status {
        font-size: 12px;
        color: #9ca3af;
        min-height: 18px;
        margin-bottom: 10px;
      }
      .status.error {
        color: #fecaca;
      }
      .status.success {
        color: #bbf7d0;
      }
      .results {
        margin-top: 8px;
        padding-top: 12px;
        border-top: 1px solid rgba(148, 163, 184, 0.4);
        display: grid;
        grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
        gap: 16px;
      }
      .candidate-list {
        margin: 10px 0 4px;
        padding: 10px 10px 4px;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.45);
      }
      .candidate-header {
        font-size: 12px;
        color: #9ca3af;
        margin-bottom: 6px;
      }
      .candidate-item {
        padding: 8px 10px;
        border-bottom: 1px dashed rgba(55, 65, 81, 0.7);
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
      }
      .candidate-item:last-child {
        border-bottom: none;
      }
      .candidate-main {
        flex: 1 1 auto;
      }
      .candidate-name {
        font-size: 14px;
        font-weight: 600;
      }
      .candidate-company {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 2px;
      }
      .candidate-sub {
        font-size: 11px;
        color: #64748b;
        margin-top: 2px;
      }
      .candidate-select-btn {
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.7);
        background: rgba(15, 23, 42, 0.9);
        color: #e5e7eb;
        cursor: pointer;
        white-space: nowrap;
      }
      @media (max-width: 768px) {
        .results {
          grid-template-columns: minmax(0, 1fr);
        }
      }
      .profile-main h2 {
        margin: 0 0 4px;
        font-size: 18px;
      }
      .muted {
        font-size: 13px;
        color: #9ca3af;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 2px 8px;
        font-size: 11px;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.5);
        color: #e5e7eb;
        margin-right: 6px;
        margin-bottom: 4px;
      }
      .section-title {
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        color: #9ca3af;
        margin-bottom: 6px;
      }
      .scroll-box {
        max-height: 260px;
        overflow: auto;
        padding-right: 6px;
      }
      .item {
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 1px dashed rgba(55, 65, 81, 0.7);
      }
      .item:last-child {
        border-bottom: none;
      }
      .confirm-bar {
        margin-top: 14px;
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.4);
        font-size: 13px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px;
      }
      .confirm-bar strong {
        margin-right: 4px;
      }
      .confirm-actions {
        display: inline-flex;
        gap: 6px;
      }
      .btn-secondary {
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.6);
        background: transparent;
        color: #e5e7eb;
        font-size: 12px;
        cursor: pointer;
      }
      code {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 12px;
      }
      a {
        color: #38bdf8;
        text-decoration: none;
      }
      a:hover {
        text-decoration: underline;
      }
    </style>
  </head>
  <body>
    <div class="app-shell">
      <div class="card">
        <h1 class="title">LinkedIn Profile Extractor</h1>
        <p class="subtitle">
          Type a person's name (optionally with company/city) or paste a direct LinkedIn URL.
          The backend will search, scrape and extract a structured profile using Groq.
        </p>

        <div class="form-row">
          <input
            id="queryInput"
            type="text"
            placeholder='e.g. "Satya Nadella Microsoft CEO" or profile URL'
          />
          <button id="runBtn" type="button" class="btn">
            <span id="btnLabel">Extract profile</span>
          </button>
        </div>

        <div id="status" class="status"></div>

        <div id="candidatesWrap" class="candidate-list" style="display:none;">
          <div class="candidate-header">
            Found profiles. Select the person whose details you want to extract:
          </div>
          <div id="candidates"></div>
        </div>

        <div id="results" style="display:none" class="results">
          <div class="profile-main">
            <h2 id="name"></h2>
            <div id="headline" class="muted"></div>
            <div id="location" class="muted" style="margin-top:4px;"></div>
            <div id="source" class="muted" style="margin-top:4px;"></div>
            <div id="about" style="margin-top:10px;font-size:13px;white-space:pre-line;"></div>

            <div style="margin-top:12px;">
              <span id="skills" class="muted"></span>
            </div>

            <div id="confirmBar" class="confirm-bar" style="display:none;">
              <span>
                <strong>Is this the correct person?</strong>
                <span id="confirmPersonLabel" style="margin-left:4px;font-weight:500;"></span>
                <br/>
                We found this profile based on your query (name + company / URL).
              </span>
              <div class="confirm-actions">
                <button id="confirmYes" class="btn-secondary">Yes, continue</button>
                <button id="confirmNo" class="btn-secondary">No, refine search</button>
              </div>
            </div>
          </div>

          <div id="detailColumn" class="profile-detail" style="display:none;">
            <div class="section">
              <div class="section-title">Experience</div>
              <div id="experience" class="scroll-box"></div>
            </div>
            <div class="section" style="margin-top:10px;">
              <div class="section-title">Education</div>
              <div id="education" class="scroll-box"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <script>
      const queryInput = document.getElementById("queryInput");
      const runBtn = document.getElementById("runBtn");
      const btnLabel = document.getElementById("btnLabel");
      const status = document.getElementById("status");
      const results = document.getElementById("results");
      const candidatesWrap = document.getElementById("candidatesWrap");
      const candidatesEl = document.getElementById("candidates");

      const nameEl = document.getElementById("name");
      const headlineEl = document.getElementById("headline");
      const locationEl = document.getElementById("location");
      const sourceEl = document.getElementById("source");
      const aboutEl = document.getElementById("about");
      const skillsEl = document.getElementById("skills");
      const expEl = document.getElementById("experience");
      const eduEl = document.getElementById("education");
      const confirmBar = document.getElementById("confirmBar");
      const confirmPersonLabel = document.getElementById("confirmPersonLabel");
      const detailColumn = document.getElementById("detailColumn");
      const confirmYes = document.getElementById("confirmYes");
      const confirmNo = document.getElementById("confirmNo");

      let lastQuery = "";
      let lastCandidates = [];

      function setLoading(isLoading) {
        runBtn.disabled = isLoading;
        btnLabel.textContent = isLoading ? "Working..." : "Extract profile";
      }

      async function runQuery() {
        const query = queryInput.value.trim();
        if (!query) {
          status.textContent = "Please enter a name or LinkedIn URL.";
          status.className = "status error";
          results.style.display = "none";
          return;
        }

        lastQuery = query;

        setLoading(true);
        status.textContent = "Searching LinkedIn profiles...";
        status.className = "status";
        results.style.display = "none";
        confirmBar.style.display = "none";
        detailColumn.style.display = "none";
        candidatesWrap.style.display = "none";
        candidatesEl.innerHTML = "";

        try {
          // First: search for candidate profiles
          const searchResp = await fetch("/api/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
          });

          const searchData = await searchResp.json();

          if (!searchResp.ok || searchData.error) {
            status.textContent =
              searchData.error ||
              "Something went wrong while searching for LinkedIn profiles.";
            status.className = "status error";
            return;
          }

          const candidates = Array.isArray(searchData.candidates)
            ? searchData.candidates
            : [];
          lastCandidates = candidates;

          // Always show the list first: username, company. User selects which one to extract.
          if (candidates.length >= 1) {
            status.textContent =
              "Select the correct person below, then we will extract full details.";
            status.className = "status";
            candidatesEl.innerHTML = "";

            candidates.forEach((c, idx) => {
              const div = document.createElement("div");
              div.className = "candidate-item";

              const main = document.createElement("div");
              main.className = "candidate-main";
              const name = document.createElement("div");
              name.className = "candidate-name";
              name.textContent = c.name || "(Person " + (idx + 1) + ")";
              const companyEl = document.createElement("div");
              companyEl.className = "candidate-company";
              companyEl.textContent = c.company || "-";
              const sub = document.createElement("div");
              sub.className = "candidate-sub";
              sub.textContent = c.snippet || "";

              main.appendChild(name);
              main.appendChild(companyEl);
              if (sub.textContent) {
                main.appendChild(sub);
              }

              const btn = document.createElement("button");
              btn.type = "button";
              btn.className = "candidate-select-btn";
              btn.textContent = "Select";
              btn.addEventListener("click", (e) => {
                e.preventDefault();
                 if (!c.url) return;
                 // Explicit permission before hitting LinkedIn / Selenium
                 const label =
                   (c.name || "this person") +
                   (c.company ? " - " + c.company : "");
                 const ok = window.confirm(
                   'We will open LinkedIn in the backend and extract details for:\n\n' + label + '\n\nDo you want to continue?'
                 );
                 if (!ok) return;
                 // Only after user confirmation do we hit LinkedIn + full pipeline
                 runProfileExtraction(c.url, c.name, c.company);
               });

              div.appendChild(main);
              div.appendChild(btn);
              candidatesEl.appendChild(div);
            });

            candidatesWrap.style.display = "block";
            return;
          }

          // If 0 candidates, fall back to direct extraction with original query
          await runProfileExtraction(query);
        } catch (err) {
          console.error(err);
          status.textContent = "Network error while calling the backend.";
          status.className = "status error";
          results.style.display = "none";
          confirmBar.style.display = "none";
          detailColumn.style.display = "none";
          candidatesWrap.style.display = "none";
        } finally {
          setLoading(false);
        }
      }

      async function runProfileExtraction(extractionQuery, displayName, displayCompany) {
        setLoading(true);
        status.textContent = "Extracting profile details...";
        status.className = "status";
        results.style.display = "none";
        confirmBar.style.display = "none";
        detailColumn.style.display = "none";

        try {
          const resp = await fetch("/api/profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: extractionQuery }),
          });

          const data = await resp.json();

          if (!resp.ok || data.error) {
            status.textContent = data.error || "Something went wrong while extracting the profile.";
            status.className = "status error";
            results.style.display = "none";
            return;
          }

          status.textContent = "Profile extracted successfully.";
          status.className = "status success";

          nameEl.textContent = data.name || "(no name found)";
          headlineEl.textContent = data.headline || "";
          locationEl.textContent = data.location || "";

          if (data.source_url) {
            if (data.source_url.startsWith("http")) {
              sourceEl.innerHTML =
                'Source: <a href="' +
                data.source_url +
                '" target="_blank" rel="noreferrer">open profile</a>';
            } else {
              sourceEl.textContent = "Source: " + data.source_url;
            }
          } else {
            sourceEl.textContent = "";
          }

          aboutEl.textContent = data.about || "";

          // Skills
          if (Array.isArray(data.skills) && data.skills.length) {
            skillsEl.innerHTML =
              '<span class="section-title" style="display:block;margin-bottom:4px;">Key skills</span>' +
              data.skills
                .slice(0, 20)
                .map((s) => '<span class="pill">' + String(s) + "</span>")
                .join("");
          } else {
            skillsEl.innerHTML = "";
          }

          // Experience
          expEl.innerHTML = "";
          if (Array.isArray(data.experience) && data.experience.length) {
            data.experience.slice(0, 12).forEach((job) => {
              const div = document.createElement("div");
              div.className = "item";
              div.innerHTML =
                "<strong>" +
                (job.title || "(role)") +
                "</strong><br/>" +
                (job.company || "") +
                (job.location ? " · " + job.location : "") +
                (job.duration ? " · " + job.duration : "") +
                (job.description
                  ? '<div style="margin-top:3px;font-size:12px;color:#9ca3af;white-space:pre-line;">' +
                    job.description +
                    "</div>"
                  : "");
              expEl.appendChild(div);
            });
          } else {
            expEl.innerHTML = '<span class="muted">No experience data found.</span>';
          }

          // Education
          eduEl.innerHTML = "";
          if (Array.isArray(data.education) && data.education.length) {
            data.education.slice(0, 12).forEach((ed) => {
              const div = document.createElement("div");
              div.className = "item";
              div.innerHTML =
                "<strong>" +
                (ed.institution || "(institution)") +
                "</strong><br/>" +
                (ed.degree || "") +
                (ed.years ? " · " + ed.years : "") +
                (ed.grade ? " · " + ed.grade : "");
              eduEl.appendChild(div);
            });
          } else {
            eduEl.innerHTML = '<span class="muted">No education data found.</span>';
          }

          // Show only the basic info first; ask user to confirm person
          const primaryExp =
            Array.isArray(data.experience) && data.experience.length
              ? data.experience[0]
              : null;
          const primaryCompany = primaryExp && primaryExp.company ? primaryExp.company : "";
          const personLabelBase =
            displayName || data.name || lastQuery || "(no name found)";
          const companyBase = displayCompany || primaryCompany;
          const personLabel = primaryCompany
            ? personLabelBase + " - " + companyBase
            : personLabelBase;
          confirmPersonLabel.textContent = personLabel;

          results.style.display = "grid";
          confirmBar.style.display = "flex";
          detailColumn.style.display = "none";
        } finally {
          setLoading(false);
        }
      }

      runBtn.addEventListener("click", (e) => {
        e.preventDefault();
        runQuery();
      });
      queryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          runQuery();
        }
      });

      // User confirms this is the correct person -> show full details
      confirmYes.addEventListener("click", () => {
        confirmBar.style.display = "none";
        detailColumn.style.display = "block";
      });

      // User says it's not the right person -> hide results and ask to refine
      confirmNo.addEventListener("click", () => {
        confirmBar.style.display = "none";
        detailColumn.style.display = "none";
        results.style.display = "none";
        status.textContent =
          "Not the right person. Please refine your query with more details (company, city) or paste the exact LinkedIn URL.";
        status.className = "status error";
        queryInput.focus();
      });
    </script>
  </body>
  </html>
"""


@app.route("/", methods=["GET"])
def index():
    # Serve raw HTML so Jinja2 does not alter script (e.g. {{ }} in JS)
    return Response(INDEX_HTML, mimetype="text/html; charset=utf-8")


def _search_linkedin_candidates(query: str) -> list[dict]:
    """
    Lightweight Google HTML search for site:linkedin.com/in results.
    Returns a list of candidates with (name, company guess, snippet, url).
    This is independent of the main scraping pipeline.
    """
    search_q = f"site:linkedin.com/in {query}"
    url = f"https://www.google.com/search?q={requests.utils.quote(search_q)}&num=6"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
    except Exception:
        return []

    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates: list[dict] = []

    # Google result blocks
    for g in soup.find_all("div", class_=re.compile(r"\bg\b")):
        a = g.find("a", href=True)
        h3 = g.find("h3")
        if not a or not h3:
            continue

        href = a["href"]
        if "linkedin.com/in/" not in href:
            continue

        # Clean LinkedIn profile URL
        m = re.search(r"(https?://(?:www\.)?linkedin\.com/in/[^\?&]+)", href)
        clean_url = m.group(1) if m else href

        title = h3.get_text(strip=True)
        snippet_el = g.find("div", class_=re.compile(r"VwiC3b|IsZvec"))
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        # Very rough guess: split title into "Name – Headline" or "Name | Headline"
        name = title
        company = ""
        for sep in [" - ", " – ", " | "]:
            if sep in title:
                parts = title.split(sep, 1)
                name = parts[0].strip()
                company = parts[1].strip()
                break

        candidates.append(
            {
                "name": name,
                "company": company,
                "snippet": snippet,
                "url": clean_url,
            }
        )

    return candidates


def _enrich_candidates_with_groq(candidates: list[dict]) -> list[dict]:
    """
    Use a very small Groq call to normalize just name + company
    from Google result titles/snippets (no LinkedIn scraping here).
    """
    if not candidates or not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        return candidates

    # Build compact text for the model
    lines = []
    for idx, c in enumerate(candidates):
        title = f"{c.get('name','')}".strip()
        company = c.get("company", "").strip()
        snippet = c.get("snippet", "").strip()
        line = f"[{idx}] title: {title}; company_guess: {company}; snippet: {snippet}"
        lines.append(line)
    joined = "\n".join(lines)

    system_msg = (
        "You are helping disambiguate LinkedIn search results. "
        "For each line, extract a clean person name and their main company "
        "(or best guess from the text). Always return STRICT JSON."
    )
    user_msg = f"""
Given these Google search result lines, return JSON with clean name and company for each index.

Lines:
{joined}

Return ONLY JSON like:
{{
  "candidates": [
    {{"index": 0, "name": "Full Name", "company": "Company Name"}},
    ...
  ]
}}
"""
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=512,
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
    except Exception:
        return candidates

    import json

    # Strip any accidental fences and parse JSON
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
    except Exception:
        return candidates

    mapping = {}
    for item in data.get("candidates", []):
        try:
            idx = int(item.get("index"))
        except Exception:
            continue
        mapping[idx] = {
            "name": item.get("name") or "",
            "company": item.get("company") or "",
        }

    # Apply normalized values where available
    for idx, c in enumerate(candidates):
        norm = mapping.get(idx)
        if not norm:
            continue
        if norm["name"]:
            c["name"] = norm["name"]
        if norm["company"]:
            c["company"] = norm["company"]

    return candidates


@app.post("/api/search")
def api_search():
    """
    POST /api/search
    JSON body: { "query": "name or LinkedIn URL" }

    Returns: { "candidates": [ { name, company, snippet, url }, ... ] }
    """
    print("[API] POST /api/search called", flush=True)
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    # If user already pasted a direct LinkedIn URL, no need to search
    if query.startswith("http") and "linkedin.com/in/" in query:
        return jsonify(
            {
                "candidates": [
                    {
                        "name": "",
                        "company": "",
                        "snippet": "Direct LinkedIn URL provided.",
                        "url": query,
                    }
                ]
            }
        )

    candidates = _search_linkedin_candidates(query)
    candidates = _enrich_candidates_with_groq(candidates)
    return jsonify({"candidates": candidates})


@app.post("/api/profile")
def api_profile():
    """
    POST /api/profile
    JSON body: { "query": "name or LinkedIn URL" }

    Returns structured profile JSON produced by process_query().
    """
    print("[API] POST /api/profile called", flush=True)
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    result = process_query(query)

    if not result:
        return jsonify({"error": "Unknown error during processing."}), 500

    if result.get("error"):
        # Pass through the error but keep 200 so UI can show the message
        return jsonify(result), 200

    return jsonify(result)


if __name__ == "__main__":
    # Bind to 0.0.0.0 so it also works inside containers / remote machines.
    app.run(host="0.0.0.0", port=5003, debug=True)


