# Timeout Fixes for LinkedIn Scraping ⏱️

## Problem
LinkedIn scraping was timing out when extracting experiences, education, and accomplishments:
```
Error getting experiences: Page.wait_for_selector: Timeout 10000ms exceeded.
  - waiting for locator("main") to be visible
  25 × locator resolved to hidden <main>
```

The `<main>` element was present but hidden, causing 10-second timeouts to fail.

## Solution: Increased Timeouts + Changed Wait Strategy

### Changes Made in `person.py`:

#### 1. Initial Profile Load (Lines 50-64)
**Before:**
```python
await self.page.wait_for_selector("main", timeout=30000)
await self.page.wait_for_selector("section.artdeco-card", timeout=15000)
```

**After:**
```python
await self.page.wait_for_selector("main", timeout=60000, state='attached')
await self.page.wait_for_selector("section.artdeco-card", timeout=30000, state='attached')
```

**Changes:**
- Increased main timeout: 30s → 60s
- Changed state: `visible` → `attached` (doesn't require element to be visible)
- Increased profile section timeout: 15s → 30s
- Added try-except to continue even if timeout occurs

#### 2. Experience Section (Lines 286-293)
**Before:**
```python
await self.navigate_and_wait(exp_url)
await self.page.wait_for_selector("main", timeout=10000)
await self.wait_and_focus(1.5)
await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=5)
```

**After:**
```python
await self.navigate_and_wait(exp_url)
try:
    await self.page.wait_for_selector("main", timeout=60000, state='attached')
except Exception as e:
    logger.warning(f"Main element wait timed out, continuing anyway: {e}")
await self.wait_and_focus(2.5)
await self.scroll_page_to_bottom(pause_time=1.0, max_scrolls=5)
```

**Changes:**
- Increased timeout: 10s → 60s
- Added `state='attached'` to not require visibility
- Added try-except to continue on timeout
- Increased focus delay: 1.5s → 2.5s
- Increased scroll pause: 0.5s → 1.0s

#### 3. Education Section (Lines 658-666)
**Before:**
```python
await self.navigate_and_wait(edu_url)
await self.page.wait_for_selector("main", timeout=10000)
await self.wait_and_focus(2)
await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=5)
```

**After:**
```python
await self.navigate_and_wait(edu_url)
try:
    await self.page.wait_for_selector("main", timeout=60000, state='attached')
except Exception as e:
    logger.warning(f"Main element wait timed out for education, continuing anyway: {e}")
await self.wait_and_focus(2.5)
await self.scroll_page_to_bottom(pause_time=1.0, max_scrolls=5)
```

**Changes:**
- Increased timeout: 10s → 60s
- Added `state='attached'`
- Added try-except to continue on timeout
- Increased focus delay: 2s → 2.5s
- Increased scroll pause: 0.5s → 1.0s

#### 4. Accomplishments Section (Lines 1013-1021)
**Before:**
```python
await self.navigate_and_wait(section_url)
await self.page.wait_for_selector("main", timeout=10000)
await self.wait_and_focus(1)
```

**After:**
```python
await self.navigate_and_wait(section_url)
try:
    await self.page.wait_for_selector("main", timeout=60000, state='attached')
except Exception as e:
    logger.warning(f"Main element wait timed out for {category}, continuing anyway: {e}")
await self.wait_and_focus(1.5)
```

**Changes:**
- Increased timeout: 10s → 60s
- Added `state='attached'`
- Added try-except to continue on timeout
- Increased focus delay: 1s → 1.5s

## Key Improvements

### 1. **6x Longer Timeouts**
- All waits increased from 10-30s to 60s
- Gives LinkedIn's slow-loading dynamic content more time

### 2. **Changed Wait Strategy**
- `state='attached'` instead of default `state='visible'`
- Elements can be hidden but still attached to DOM
- More reliable for LinkedIn's hidden elements

### 3. **Graceful Degradation**
- All waits wrapped in try-except
- Continues scraping even if one section times out
- Better error logging for debugging

### 4. **Human-Like Delays**
- Increased focus/wait times between actions
- More natural scrolling (1s pause instead of 0.5s)
- Reduces risk of bot detection

## Expected Results

### Before Fixes ❌
```
[███░░░░░░░░░░░░░░░░░░░░░░░░░░░] 10% - Navigated to profile
[██████░░░░░░░░░░░░░░░░░░░░░░░░] 20% - Got name: Krushini Katakam
[█████████░░░░░░░░░░░░░░░░░░░░░] 30% - Got about section
Error getting experiences: Timeout 10000ms exceeded.
[██████████████████░░░░░░░░░░░░] 60% - Got 0 experiences
```

### After Fixes ✅
```
[███░░░░░░░░░░░░░░░░░░░░░░░░░░░] 10% - Navigated to profile
[██████░░░░░░░░░░░░░░░░░░░░░░░░] 20% - Got name: Krushini Katakam
[█████████░░░░░░░░░░░░░░░░░░░░░] 30% - Got about section
[██████████████████░░░░░░░░░░░░] 60% - Got 1-2 experiences
[█████████████████████░░░░░░░░░] 50% - Got 1 education
[████████████████████████░░░░░░] 85% - Got accomplishments
✅ Profile scraped successfully!
```

## Testing

### Via Frontend
1. Start backend: `cd SET/backend && python main.py`
2. Start frontend: `cd SET/frontend && npm run dev`
3. Go to http://localhost:5173
4. Select "Individual Research"
5. Enter: "Krushini Katakam"
6. Add LinkedIn URL: `https://www.linkedin.com/in/krushini-katakam-3544992a0/`
7. Click "Generate Intelligence Capsule"

### Expected Output
```
Name: Krushini Katakam
Location: Karimnagar, Telangana, India
Experiences: 1-2 (Developer at Vardaan Data Sciences)
Education: 1 (University/College)
```

## Files Modified
- `SET/linkedin_scraper/linkedin_scraper/scrapers/person.py`
  - Lines 50-67: Initial profile load
  - Lines 286-293: Experience section
  - Lines 658-666: Education section  
  - Lines 1013-1021: Accomplishments section

## Related Fixes
- `SET/linkedin_scraper/linkedin_scraper/core/browser.py`: Anti-bot detection
- `SET/linkedin_scraper/linkedin_scraper/scrapers/base.py`: Human-like navigation
- `SET/backend/services/linkedin_scraper_service.py`: Session management

## Notes
- LinkedIn's dynamic content can be very slow to load (10-30s is normal)
- Hidden elements are common on LinkedIn (use `state='attached'`)
- Always add try-except for graceful degradation
- Increase delays between actions to avoid bot detection
