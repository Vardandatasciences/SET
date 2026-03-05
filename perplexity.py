"""
Person info via Perplexity (Sonar) — web + model
================================================
Given just a name (or description like "Satya Nadella Microsoft CEO"),
this script calls the Perplexity / Sonar API which can browse the web
and returns the maximum possible details in structured JSON.

This is similar to `openai_person_info.py` and `gemini_model.py`,
but uses Perplexity's search-augmented models instead of OpenAI/Gemini.

Requires:
  pip install openai python-dotenv

Env vars:
  PERPLEXITY_API_KEY=your_perplexity_api_key_here
  PERPLEXITY_MODEL=sonar-pro              # optional, default shown
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


# ── Config ────────────────────────────────────────────────────────────────────
PERPLEXITY_API_KEY = (os.getenv("PERPLEXITY_API_KEY") or "").strip()
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")
MAX_TOKENS = 2048


# ── Prompt for maximum possible details ───────────────────────────────────────
SYSTEM_FULL_DETAILS = (
    "You are Perplexity Sonar, an expert researcher that can browse the web. "
    "Given the name or short description of a person, you must use web search "
    "and any reliable sources you can access to gather the most complete and "
    "up-to-date profile of that person. "
    "Always answer ONLY as strict JSON. No markdown, no extra commentary."
)

KNOWLEDGE_WEB_PROMPT = """You are given a person to research:

  Query: "{query}"

Use your web search capabilities to find CURRENT, accurate information about this person.
Combine multiple sources where needed. Resolve conflicts if sources disagree.

Return ONLY this JSON object (use empty "" or [] when unknown):
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
    """Extract the first {...} block and parse it as JSON.

    Perplexity often wraps JSON in ```json fences or adds extra text.
    This helper ignores everything outside the outermost JSON object.
    """
    # Find outermost JSON object by braces
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return {}


def ask_perplexity_person_info(query: str) -> Dict[str, Any]:
    """
    Ask Perplexity (Sonar) to research a person and return structured info.

    Uses the OpenAI-compatible client pointing at https://api.perplexity.ai.
    """
    if not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY == "your_perplexity_api_key_here":
        raise ValueError("Set PERPLEXITY_API_KEY in .env")

    try:
        from openai import OpenAI
    except ImportError as e:
        raise ImportError("Install openai: pip install openai") from e

    client = OpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai",
    )

    user_prompt = KNOWLEDGE_WEB_PROMPT.format(query=query)

    log.info(f"Using Perplexity model {PERPLEXITY_MODEL} for query: {query}")

    resp = client.chat.completions.create(
        model=PERPLEXITY_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_FULL_DETAILS},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=MAX_TOKENS,
        temperature=0.1,
    )

    content = (resp.choices[0].message.content or "").strip()
    data = _parse_json_from_response(content)

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
    data["source_url"] = "Perplexity Sonar (web + model)"
    return data


def run(query: str, output_file: str = "profile_output_perplexity.json") -> Optional[Dict[str, Any]]:
    """CLI helper: call Perplexity Sonar and save the JSON profile."""
    print(f"\n{'='*60}")
    print(f"  Person info  |  Perplexity Sonar (web + model)")
    print(f"  Query: {query}")
    print(f"{'='*60}\n")

    try:
        result = ask_perplexity_person_info(query)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None

    print("\n── Extracted profile (Perplexity) ───────────────────────")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("─────────────────────────────────────────────────────────\n")

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

