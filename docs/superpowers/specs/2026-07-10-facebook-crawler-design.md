# Facebook Group Job Crawler — Design Spec

**Date:** 2026-07-10
**Status:** Draft
**Project:** AI Job Search VN (`jamesng16/ai-job-search-vn`)

---

## 1. Overview

Add Facebook group job crawling to the existing AI Job Search VN pipeline, using crawl4ai for browser automation and LLM for structured extraction. Follows the same portal-adapter pattern as ITviec (`search_adapter.py` → API → Dashboard).

### Target groups
- AI/ML Vietnam
- Computer Vision Vietnam
- Data Science VN
- (Configurable list, user adds more via config file)

### Constraints
- Must use Facebook clone account (not real account) to avoid ban risk
- Browser session persisted via crawl4ai Managed Browser profile
- LLM extraction via DeepSeek (cheapest option, already configured)

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│ SETUP (one-time)                                    │
│  pip install crawl4ai && crawl4ai-setup             │
│  crwl profiles → "fb-clone" → login FB → save       │
│  Stored: ~/.crawl4ai/profiles/fb-clone/             │
└─────────────────────────────────────────────────────┘
                         │ user_data_dir
┌────────────────────────▼────────────────────────────┐
│ CRAWL (search_adapter.py — new function)            │
│  search_facebook(query, groups, limit=20)            │
│    Pass 1:   crawl4ai → scroll feed → markdown      │
│    Pass 1.5: Keyword filter (regex, cheap)          │
│    Pass 2:   LLM extract → JSON per post            │
│    Return:   list[dict] (same shape as ITviec)       │
└─────────────────────────────────────────────────────┘
                         │ list[dict]
┌────────────────────────▼────────────────────────────┐
│ EXISTING PIPELINE (unchanged)                       │
│  POST /api/search/realtime {portals:["Facebook"]}    │
│    → search_adapter.search_all()                    │
│    → INSERT INTO job_listings (dedup by source_id)  │
│    → Dashboard displays results                     │
└─────────────────────────────────────────────────────┘
```

### Key decisions
- **crawl4ai over raw Playwright**: Built-in session persistence (`user_data_dir`), stealth mode, simpler API. Python-native, no need for a separate TypeScript CLI.
- **LLM over regex-only**: Facebook posts are unstructured free text. Regex catches obvious patterns but LLM handles the long tail.
- **Keyword pre-filter**: Reduces LLM calls from ~50 to ~5-15 per crawl. Saves cost.

---

## 3. Data Flow (3-pass extraction)

### Pass 1: Raw crawl (crawl4ai)
```
Input:  group_url (e.g. "https://facebook.com/groups/ai.ml.vietnam")
        limit = 50 posts

Process:
  1. AsyncWebCrawler(user_data_dir="fb-clone") → browser with FB session
  2. Navigate to group → wait for feed to load
  3. Scroll N times to load posts
  4. Extract each post as:
     - markdown text
     - post_url (permalink)
     - author_name
     - timestamp

Output: list of {text, url, author, date}
```

### Pass 1.5: Keyword pre-filter
```
Input:  list of posts, user_query (e.g. "AI Engineer")

Process:
  - Expand user_query into keywords: ["AI", "Engineer", "Machine Learning"]
  - Always include hiring keywords: ["tuyển", "hiring", "JD", "lương", "salary"]
  - Keep post if ANY keyword matches (case-insensitive, regex word boundary)

Output: filtered list (typically 5-15 posts)
```

### Pass 2: LLM structured extraction
```
Input:  post text + metadata

Prompt:
  "You are a job listing extractor. Given a Vietnamese Facebook post,
   extract job information. Return ONLY JSON, no explanation.

   Post: {text}

   Schema: {
     "is_job": true/false,
     "title": "Job title or null",
     "company": "Company name or null",
     "salary": "Salary range or null",
     "location": "Work location or null",
     "contact": "Email/phone/telegram or null",
     "description": "Brief summary (max 200 chars) or null"
   }"

Output: JSON per post → only keep is_job=true
```

### Normalization
Same shape as other portals:
```python
{
    "job_title": "...", "company": "...", "portal": "Facebook",
    "location": "...", "salary": "...", "job_url": "post_url",
    "description": "...", "posted_date": "...", "source_id": "fb_post_123"
}
```

---

## 4. Implementation Files

| File | Action | Purpose |
|------|--------|---------|
| `web/search_adapter.py` | **Modify** | Add `search_facebook()`, register in `search_all()` |
| `web/server.py` | **Modify** | Add "Facebook" to portal list in `/api/portals` |
| `web/static/index.html` | **No change** | Dashboard already supports any portal |
| `web/fb_groups.json` | **New** | Config file listing target group URLs |
| `web/warmup_guide.md` | **New** | Instructions for clone account warm-up |

### fb_groups.json
```json
{
  "groups": [
    {
      "name": "AI/ML Vietnam",
      "url": "https://facebook.com/groups/ai.ml.vietnam"
    },
    {
      "name": "Computer Vision Vietnam",
      "url": "https://facebook.com/groups/cv.vietnam"
    }
  ]
}
```

---

## 5. Setup & Dependencies

```bash
pip install crawl4ai
crawl4ai-setup          # installs Playwright browsers
crwl profiles           # interactive: create "fb-clone" profile
```

Then follow `warmup_guide.md`:
1. Login Facebook clone account in the profile browser
2. Join target groups
3. Use account naturally for 3-5 days (like, comment, scroll)
4. Ready for crawling

---

## 6. Error Handling

| Scenario | Handling |
|----------|----------|
| FB session expired / checkpoint | Return empty results + log warning. User re-logins via `crwl profiles` |
| Group not accessible (private) | Skip group, log warning |
| LLM API rate limit | Exponential backoff, max 3 retries |
| 0 posts match keyword | Return empty list (not an error) |
| Browser crash during crawl | Retry once, then return partial results |

---

## 7. Testing

- Unit test: `search_facebook()` with mock crawl4ai responses
- Integration test: `POST /api/search/realtime` with `portals:["Facebook"]`
- Manual test: Run against real FB clone account, verify output JSON
- Dashboard smoke test: Click "Facebook" in portal dropdown → Live Search → see job cards

---

## 8. Future (out of scope for v1)

- Schedule auto-crawl via cron
- Multi-group parallel crawl
- Post dedup across groups (same job posted in multiple groups)
- Direct "Apply" link detection (Google Forms, email)
- FB group discovery: auto-find new groups by keyword
