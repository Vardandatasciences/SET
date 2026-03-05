"""
Person info from OpenAI / Gemini knowledge only (no web scraping)
=================================================================
Given just a name (or a short description like "Satya Nadella Microsoft CEO"),
this script asks the AI model what it already knows about that person and
returns the **maximum possible details** in structured JSON.

Important:
- **No Google search, no LinkedIn scraping, no google_scraper.py usage.**
- Only the model's internal knowledge is used.

You can use either provider (set exactly one in .env):
- `OPENAI_API_KEY=sk-...`       → use OpenAI (e.g. `gpt-4o-mini`)
- `GEMINI_API_KEY=...` or `GOOGLE_API_KEY=...` → use Google Gemini

The prompt is written to extract every possible detail: name, headline, location,
about, experience, education, skills, certifications, languages, volunteer work,
projects, publications, awards, interests, social links, contact info.

Usage:
  python openai_person_info.py   (edit the `name` variable at the bottom)

Requires:
  pip install openai python-dotenv
  # Optional if you want Gemini instead of OpenAI:
  # pip install google-generativeai
"""

import os
import re
import json
import logging
from typing import Optional, List

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MAX_TOKENS = 4096

# Keys we might merge if we ever combine multiple responses
LIST_KEYS = (
    "experience", "education", "skills", "certifications",
    "languages", "volunteer_work", "projects", "publications", "awards_honors",
    "interests", "social_links",
)
STRING_KEYS = ("name", "headline", "location", "about", "contact_info")


# ── Shared prompt: maximum possible details about the person ───────────────────
SYSTEM_FULL_DETAILS = (
    "You are an expert at extracting every possible detail about a person from text or from your knowledge. "
    "Extract ALL available professional and personal information: name, job, company, location, bio, "
    "experience, education, skills, certifications, languages, volunteer work, projects, publications, "
    "awards, interests, social/contact links. Even partial or minimal text — extract anything you find. "
    "ALWAYS return ONLY valid JSON. No markdown code fences, no explanation before or after."
)

PROMPT_FULL_DETAILS = """Extract every possible detail about this person from the raw text below.
Include every piece of information you can find, even if incomplete. Use empty string "" or [] when not found.

Return ONLY this JSON (no other text):
{{
  "name": "Full name",
  "headline": "Current job title and company",
  "location": "City, Region, Country",
  "about": "Full bio / summary / description",
  "experience": [
    {{ "title": "", "company": "", "duration": "", "years": "", "description": "", "location": "" }}
  ],
  "education": [
    {{ "degree": "", "institution": "", "years": "", "grade": "", "field": "" }}
  ],
  "skills": [],
  "certifications": [{{ "name": "", "issuer": "", "date": "" }}],
  "languages": [],
  "volunteer_work": [{{ "role": "", "organization": "", "duration": "", "description": "" }}],
  "projects": [{{ "name": "", "description": "", "url": "", "duration": "" }}],
  "publications": [{{ "title": "", "publisher": "", "date": "", "url": "" }}],
  "awards_honors": [],
  "interests": [],
  "social_links": {{ "linkedin": "", "twitter": "", "github": "", "website": "" }},
  "contact_info": ""
}}

Extract ANY information you can find. Raw text:

{text}"""

KNOWLEDGE_PROMPT_FULL_DETAILS = """What do you know about this person? Query: "{query}"

Return every possible detail you are confident about. Use ONLY this JSON (empty "" or [] when unknown):
{{
  "name": "", "headline": "", "location": "", "about": "",
  "experience": [{{ "title": "", "company": "", "duration": "", "years": "", "description": "", "location": "" }}],
  "education": [{{ "degree": "", "institution": "", "years": "", "grade": "", "field": "" }}],
  "skills": [], "certifications": [{{ "name": "", "issuer": "", "date": "" }}],
  "languages": [], "volunteer_work": [], "projects": [], "publications": [], "awards_honors": [], "interests": [],
  "social_links": {{ "linkedin": "", "twitter": "", "github": "", "website": "" }},
  "contact_info": ""
}}"""


def _parse_json_from_response(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


def _merge_extractions(results: List[dict]) -> dict:
    if not results:
        return {}
    if len(results) == 1:
        return results[0].copy()
    base = results[0].copy()
    for r in results[1:]:
        for k in STRING_KEYS:
            if k in r and len(str(r.get(k, ""))) > len(str(base.get(k, ""))):
                base[k] = r[k]
        for k in LIST_KEYS:
            if k not in base:
                base[k] = []
            existing = base[k]
            if not isinstance(existing, list):
                existing = [existing] if existing else []
            seen = {json.dumps(x, sort_keys=True) for x in existing if isinstance(x, dict)}
            for item in (r.get(k) or []):
                if isinstance(item, dict):
                    s = json.dumps(item, sort_keys=True)
                    if s not in seen:
                        existing.append(item)
                        seen.add(s)
                elif item and item not in existing:
                    existing.append(item)
            base[k] = existing
        if "social_links" in r and isinstance(r["social_links"], dict):
            for sk, sv in r["social_links"].items():
                if sv:
                    base.setdefault("social_links", {})[sk] = sv
    return base


# ── OpenAI extractor ────────────────────────────────────────────────────────────
class OpenAIExtractor:
    """Ask OpenAI what it already knows about a person (no web)."""

    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        except ImportError:
            raise ImportError("Install openai: pip install openai")
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            raise ValueError("Set OPENAI_API_KEY in .env")

    def extract_from_knowledge(self, query: str) -> dict:
        """Single call: model knowledge only, based on the person's name / description."""
        log.info(f"Asking OpenAI (knowledge only) about: {query}")
        return self._call(KNOWLEDGE_PROMPT_FULL_DETAILS.format(query=query)) or {}

    def _call(self, user_content: str) -> dict:
        try:
            resp = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_FULL_DETAILS},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=MAX_TOKENS,
                temperature=0.1,
            )
            content = (resp.choices[0].message.content or "").strip()
            return _parse_json_from_response(content)
        except Exception as e:
            log.error(f"OpenAI error: {e}")
            return {}


# ── Google Gemini extractor ─────────────────────────────────────────────────────
class GeminiExtractor:
    """Ask Gemini what it already knows about a person (no web)."""

    def __init__(self):
        try:
            import google.generativeai as genai
            self.genai = genai
            api_key = GEMINI_API_KEY
            if not api_key or api_key == "your_gemini_api_key_here":
                raise ValueError("Set GEMINI_API_KEY or GOOGLE_API_KEY in .env")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
        except ImportError:
            raise ImportError("Install Google Gemini: pip install google-generativeai")

    def extract(self, raw_text: str, query: str) -> dict:
        # Kept for API symmetry, but for knowledge-only mode we call extract_from_knowledge instead.
        log.info(f"(Gemini) raw_text extraction not used in knowledge-only mode")
        return {}

    def extract_from_knowledge(self, query: str) -> dict:
        log.info(f"Asking Gemini (knowledge only) about: {query}")
        return self._call(KNOWLEDGE_PROMPT_FULL_DETAILS.format(query=query)) or {}

    def _call(self, user_content: str) -> dict:
        try:
            full_prompt = f"{SYSTEM_FULL_DETAILS}\n\n{user_content}"
            response = self.model.generate_content(
                full_prompt,
                generation_config={"max_output_tokens": MAX_TOKENS, "temperature": 0.1},
            )
            text = (response.text or "").strip()
            return _parse_json_from_response(text)
        except Exception as e:
            log.error(f"Gemini error: {e}")
            return {}


# ── Auto-detect provider from API keys ─────────────────────────────────────────
def get_extractor():
    """Use OPENAI_API_KEY if set, else GEMINI_API_KEY or GOOGLE_API_KEY. One must be set."""
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        log.info("Using OpenAI for extraction")
        return OpenAIExtractor()
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        log.info("Using Google Gemini for extraction")
        return GeminiExtractor()
    raise ValueError(
        "Set either OPENAI_API_KEY or GEMINI_API_KEY (or GOOGLE_API_KEY) in .env"
    )


# ── Pipeline: knowledge-only (no scraping) ─────────────────────────────────────
def process_query_person(query: str, knowledge_only: Optional[bool] = None) -> dict:
    """
    Get maximum possible details about a person using ONLY model knowledge.
    No Google search, no LinkedIn scraping, no calls to google_scraper.py.
    """
    try:
        extractor = get_extractor()
    except ValueError as e:
        return {"query": query, "error": str(e)}

    try:
        # Always use knowledge-only extraction
        result = extractor.extract_from_knowledge(query)
        result["source_url"] = "AI knowledge only (no web search)"
        result["query"] = query
        return result
    except Exception as e:
        log.error(e)
        return {"query": query, "error": str(e)}


# Backward-compatible alias
def process_query_openai(query: str, knowledge_only: Optional[bool] = None) -> dict:
    return process_query_person(query, knowledge_only=knowledge_only)


def run(query: str, output_file: str = "profile_output_openai.json", knowledge_only: Optional[bool] = None):
    """CLI: run person-info pipeline (OpenAI or Gemini) and save JSON (knowledge-only)."""
    print(f"\n{'='*60}")
    print(f"  Person info  |  OpenAI or Gemini  |  Full details")
    print(f"  Query: {query}")
    print(f"  Mode: AI knowledge only (no web search)")
    print(f"{'='*60}\n")

    result = process_query_person(query, knowledge_only=knowledge_only)

    if not result or result.get("error"):
        print("\n✗ No data found. Tips:")
        print("  • Add context: \"John Smith Google Senior Engineer\"")
        print("  • Or paste a direct LinkedIn URL")
        print("  • Set OPENAI_USE_KNOWLEDGE_ONLY=1 for well-known people")
        if result and result.get("error"):
            print(f"\nDetails: {result['error']}")
        return None

    print(f"\n✓ Source: {result.get('source_url', '')}\n")
    print("\n── Extracted profile (all possible details) ───────────────")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("───────────────────────────────────────────────────────────\n")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved → {output_file}")
    return result


# ── Config ─────────────────────────────────────────────────────────────────────
name = "Muni syam putthuru"

if __name__ == "__main__":
    if not name:
        print(__doc__)
        print("Examples:")
        print('  name = "Satya Nadella Microsoft CEO"')
        print('  name = "https://www.linkedin.com/in/satyanadella"')
        print("  Set OPENAI_API_KEY or GEMINI_API_KEY in .env")
        exit(1)

    run(name)
