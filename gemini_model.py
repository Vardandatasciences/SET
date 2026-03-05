"""
Person info from Google Gemini knowledge only (no web scraping)
================================================================
Given just a name (or a short description like "Satya Nadella Microsoft CEO"),
this script asks the Gemini model what it already knows about that person and
returns the maximum possible details in structured JSON.

Requires:
  pip install google-generativeai python-dotenv

Env vars (set at least GEMINI_API_KEY or GOOGLE_API_KEY):
  GEMINI_API_KEY=your_gemini_api_key_here
  GEMINI_MODEL=gemini-1.5-flash   # optional, this is the default
"""

import os
import re
import json
import logging
from typing import Optional, Dict, Any

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_TOKENS = 2048


# ── Prompt for maximum possible details ───────────────────────────────────────
SYSTEM_FULL_DETAILS = (
    "You are an expert at extracting every possible detail about a person from your knowledge. "
    "Extract ALL available professional and personal information: name, job, company, location, bio, "
    "experience, education, skills, certifications, languages, volunteer work, projects, publications, "
    "awards, interests, social/contact links. "
    "ALWAYS return ONLY valid JSON. No markdown code fences, no explanation before or after."
)

KNOWLEDGE_PROMPT_FULL_DETAILS = """{system}

What do you know about this person? Query: "{query}"

Return every possible detail you are confident about. Use ONLY this JSON (empty "" or [] when unknown):
{{
  "name": "",
  "headline": "",
  "location": "",
  "about": "",
  "experience": [
    {{
      "title": "",
      "company": "",
      "duration": "",
      "years": "",
      "description": "",
      "location": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "years": "",
      "grade": "",
      "field": ""
    }}
  ],
  "skills": [],
  "certifications": [
    {{
      "name": "",
      "issuer": "",
      "date": ""
    }}
  ],
  "languages": [],
  "volunteer_work": [],
  "projects": [],
  "publications": [],
  "awards_honors": [],
  "interests": [],
  "social_links": {{
    "linkedin": "",
    "twitter": "",
    "github": "",
    "website": ""
  }},
  "contact_info": ""
}}"""


def _parse_json_from_response(text: str) -> Dict[str, Any]:
    """Strip markdown fences etc. and parse JSON."""
    text = re.sub(r"^```(?:json)?\\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\\s*```$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"\\{.*\\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


def ask_gemini_person_info(query: str) -> Dict[str, Any]:
    """
    Ask Gemini (knowledge only) what it knows about a person.

    Returns a dict with fields like:
      name, headline, location, about, experience, education, skills, etc.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("Set GEMINI_API_KEY or GOOGLE_API_KEY in .env")

    try:
        import google.generativeai as genai
    except ImportError as e:
        raise ImportError("Install google-generativeai: pip install google-generativeai") from e

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = KNOWLEDGE_PROMPT_FULL_DETAILS.format(system=SYSTEM_FULL_DETAILS, query=query)
    log.info(f"Using Gemini model {GEMINI_MODEL} for query: {query}")

    response = model.generate_content(
        prompt,
        generation_config={"max_output_tokens": MAX_TOKENS, "temperature": 0.1},
    )
    text = (response.text or "").strip()
    data = _parse_json_from_response(text)

    # Ensure basic shape and metadata
    if not isinstance(data, dict):
        data = {}
    data.setdefault("name", "")
    data.setdefault("headline", "")
    data.setdefault("location", "")
    data.setdefault("about", "")
    data.setdefault("experience", [])
    data.setdefault("education", [])
    data.setdefault("skills", [])
    data.setdefault("certifications", [])
    data.setdefault("languages", [])
    data.setdefault("volunteer_work", [])
    data.setdefault("projects", [])
    data.setdefault("publications", [])
    data.setdefault("awards_honors", [])
    data.setdefault("interests", [])
    data.setdefault("social_links", {"linkedin": "", "twitter": "", "github": "", "website": ""})
    data.setdefault("contact_info", "")

    data["query"] = query
    data["source_url"] = "Gemini knowledge only (no web search)"
    return data


def run(query: str, output_file: str = "profile_output_gemini.json") -> Optional[Dict[str, Any]]:
    """CLI helper: call Gemini and save the JSON profile."""
    print(f"\n{'='*60}")
    print(f"  Person info  |  Gemini (knowledge only)")
    print(f"  Query: {query}")
    print(f"{'='*60}\n")

    try:
        result = ask_gemini_person_info(query)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None

    print("\n── Extracted profile (Gemini knowledge) ───────────────")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("───────────────────────────────────────────────────────\n")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved → {output_file}")
    return result


name = "Satya Nadella Microsoft CEO"

if __name__ == "__main__":
    if not name:
        print(__doc__)
        print("Example:")
        print('  name = "Sundar Pichai Google CEO"')
        exit(1)

    run(name)
