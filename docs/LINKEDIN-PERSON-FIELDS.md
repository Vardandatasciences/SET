# What Details the LinkedIn Scraper Fetches for a Person

When you ask for a person (via the UI or `POST /api/profile`), the app can use **two pipelines**. The data you get depends on which one runs.

---

## 1. Playwright LinkedIn scraper (used for direct profile URLs)

Used when you pass a **direct LinkedIn profile URL** (e.g. `https://www.linkedin.com/in/satyanadella`) and the Playwright scraper is available. It logs into LinkedIn and scrapes the live profile page.

### Top-level fields

| Field | Description |
|-------|-------------|
| `linkedin_url` | Profile URL |
| `name` | Full name |
| `location` | Location (e.g. city, country) |
| `about` | About / summary / bio text |
| `open_to_work` | Boolean: profile has “Open to work” |

### Experiences (work history)

Each item can have:

| Field | Description |
|-------|-------------|
| `position_title` | Job title |
| `institution_name` | Company / organization name |
| `linkedin_url` | LinkedIn URL of the company/role if present |
| `from_date` | Start date (e.g. "Jan 2020") |
| `to_date` | End date or "Present" |
| `duration` | Duration string (e.g. "2 yrs 3 mos") |
| `location` | Job location |
| `description` | Role description |

### Educations

Each item can have:

| Field | Description |
|-------|-------------|
| `institution_name` | School / university name |
| `degree` | Degree (e.g. MBA, B.Tech) |
| `linkedin_url` | LinkedIn URL of school if present |
| `from_date` | Start date |
| `to_date` | End date |
| `description` | Description / activities |

### Accomplishments (includes certifications)

Each item can have:

| Field | Description |
|-------|-------------|
| `category` | e.g. "Certification", "Course", "Project" |
| `title` | Name of the accomplishment / certification |
| `issuer` | Issuing organization |
| `issued_date` | Date issued |
| `credential_id` | Credential ID if shown |
| `credential_url` | URL of credential if shown |
| `description` | Optional description |

### Skills

- `skills`: List of strings (skill names as shown on the profile).

### Interests

Each item can have:

| Field | Description |
|-------|-------------|
| `name` | Interest name (e.g. company, topic) |
| `category` | Category of interest |
| `linkedin_url` | LinkedIn URL if present |

### Contacts

Each item can have:

| Field | Description |
|-------|-------------|
| `type` | Type (e.g. email, phone, website) |
| `value` | The value (email, URL, etc.) |
| `label` | Optional label |

### Posts (recent activity)

Each item can have:

| Field | Description |
|-------|-------------|
| `content` | Post text |
| `timestamp` | When posted (if available) |
| `post_url` | URL to the post |
| `media_type` | e.g. "image", "video", "article" |

---

## 2. Selenium + Groq pipeline (fallback)

Used when you pass a **name** (not a URL) or when the Playwright scraper is not used/fails. It fetches the profile (or Google/Cache/DuckDuckGo content) with Selenium or requests, then sends the **raw text** to Groq (LLM) to extract structure.

### Top-level fields

| Field | Description |
|-------|-------------|
| `query` | Original search query (name or URL) |
| `name` | Full name |
| `headline` | Current job title and company (one line) |
| `location` | Location string |
| `about` | Bio / summary |
| `source_url` | URL the text was scraped from |
| `error` | Set only if something went wrong |

### Experience (LLM-extracted)

Each item can have:

| Field | Description |
|-------|-------------|
| `title` | Job title |
| `company` | Company name |
| `duration` | Time period (e.g. "2020 - 2022") |
| `years` | Years if mentioned |
| `description` | Job description / responsibilities |
| `location` | Job location |

### Education (LLM-extracted)

Each item can have:

| Field | Description |
|-------|-------------|
| `degree` | Degree (e.g. MBA, B.S.) |
| `institution` | School / university name |
| `years` | Years attended |
| `grade` | Grade if mentioned |

### Skills & certifications

- `skills`: List of strings.
- `certifications`: List of objects with `name`, `issuer`, `date`.

---

## Summary

| Detail | Playwright scraper | Selenium + Groq |
|--------|--------------------|------------------|
| Name, location, about | ✅ | ✅ |
| Headline (title + company) | ✅ (from experiences) | ✅ (single headline field) |
| Work experience | ✅ (full: dates, duration, description, URL) | ✅ (title, company, duration, description, location) |
| Education | ✅ (institution, degree, dates, description, URL) | ✅ (degree, institution, years, grade) |
| Skills | ✅ | ✅ |
| Certifications | ✅ (inside accomplishments) | ✅ (separate list) |
| Accomplishments / courses / projects | ✅ | Only via certifications |
| Interests | ✅ | ❌ |
| Contact info | ✅ | ❌ |
| Posts / activity | ✅ | ❌ |
| Open to work | ✅ | ❌ |

For **maximum detail** (interests, contacts, posts, open-to-work, exact dates/durations, LinkedIn URLs), use a **direct LinkedIn profile URL** so the **Playwright** scraper runs (with valid `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` in `.env`).  
For **name-only** searches or when Playwright isn’t used, you get the **Selenium + Groq** set of fields above.
