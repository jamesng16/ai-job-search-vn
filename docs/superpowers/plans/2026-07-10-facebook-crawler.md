# Facebook Group Job Crawler — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Facebook group job crawling to search_adapter.py using crawl4ai + LLM extraction, following the existing ITviec portal pattern.

**Architecture:** Single Python function `search_facebook()` added to `search_adapter.py`. Uses crawl4ai AsyncWebCrawler with managed browser profile for FB session persistence. Three-pass extraction: crawl → keyword filter → LLM parse. Registered in `search_all()` and exposed via existing `/api/search/realtime` endpoint.

**Tech Stack:** Python 3.10+, crawl4ai v0.9.x (Playwright-backed), DeepSeek API (LLM extraction), SQLite (existing)

## Global Constraints

- Must use Facebook clone account (not real account) — ban risk isolated
- Browser session persisted via `~/.crawl4ai/profiles/fb-clone/`
- LLM extraction via DeepSeek (cheapest, already configured at `api.ai-box.vn/v1`)
- Follow existing portal pattern: function returns `list[dict]` with keys `job_title, company, portal, location, salary, job_url, description, posted_date, source_id`
- Dashboard HTML unchanged — portal auto-supported

---

### Task 1: Install crawl4ai and set up project config

**Files:**
- Create: `web/fb_groups.json`
- Create: `web/warmup_guide.md`

**Interfaces:**
- Produces: `fb_groups.json` — config file read by `search_facebook()`. Format: `{"groups": [{"name": str, "url": str}]}`
- Produces: `warmup_guide.md` — user-facing instructions, no code dependency

- [ ] **Step 1: Install crawl4ai**

```bash
pip install crawl4ai
crawl4ai-setup
```

- [ ] **Step 2: Create fb_groups.json**

Write `web/fb_groups.json`:

```json
{
  "groups": [
    {
      "name": "AI/ML Vietnam",
      "url": "https://facebook.com/groups/ai.ml.vietnam"
    },
    {
      "name": "Computer Vision Vietnam",
      "url": "https://facebook.com/groups/cv.vn"
    },
    {
      "name": "Data Science Vietnam",
      "url": "https://facebook.com/groups/datascience.vn"
    }
  ]
}
```

- [ ] **Step 3: Create warmup_guide.md**

Write `web/warmup_guide.md`:

```markdown
# Facebook Clone Account Warm-Up Guide

## 1. Create clone account
- Use a new email (not linked to your real FB)
- Use a realistic Vietnamese name
- Add a profile picture (AI-generated face works)
- Fill in basic info: school, city, job

## 2. Create browser profile
```bash
crwl profiles
# Select "Create new profile" → name it "fb-clone"
# Browser opens → login with clone account
# Press 'q' in terminal when done
```

## 3. Join target groups
- Search for groups listed in `fb_groups.json`
- Join each group (may need admin approval — wait 1-2 days)

## 4. Warm-up (3-5 days)
Each day, spend 5-10 minutes:
- Scroll the news feed naturally
- Like 3-5 posts
- Comment on 1-2 posts ("Quan tâm", "Cho mình xin thông tin với ạ")
- Join 1-2 more related groups
- Do NOT post any job listings or spam

## 5. Verify
```bash
crwl profiles
# Select "fb-clone" → "Test crawl"
# Verify you can see group content
```
```

- [ ] **Step 4: Commit**

```bash
git add web/fb_groups.json web/warmup_guide.md
git commit -m "feat: add Facebook crawler config and warm-up guide"
```

---

### Task 2: Add search_facebook() to search_adapter.py

**Files:**
- Modify: `web/search_adapter.py` — add `search_facebook()` function and imports

**Interfaces:**
- Consumes: `fb_groups.json` (from Task 1), existing `_normalize()` helper, DeepSeek API credentials from env
- Produces: `search_facebook(query: str, location: str = "", limit: int = 10) -> list[dict]`

- [ ] **Step 1: Add imports at top of search_adapter.py**

Patch `web/search_adapter.py` — add after existing imports (after `from typing import Optional`):

```python
import json as json_mod
import re
from openai import OpenAI
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
```

Add DeepSeek client (after BUN_DIR line):

```python
LLM_CLIENT = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
    base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.ai-box.vn/v1"),
)
LLM_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
```

- [ ] **Step 2: Add keyword filter helper**

Add after LLM_CLIENT block:

```python
HIRING_KEYWORDS = [
    "tuyển", "hiring", "looking for", "jd", "mô tả công việc",
    "lương", "salary", "ứng tuyển", "apply", "recruit",
    "full-time", "part-time", "remote", "hybrid", "on-site",
    "fresher", "senior", "junior", "intern", "middle",
    "engineer", "developer", "data scientist", "ai", "ml",
]


def _expand_keywords(query: str) -> list[str]:
    """Split query into words, add hiring keywords."""
    words = re.findall(r"[a-zA-ZÀ-ỹ]+", query.lower())
    # Add common variations
    expanded = set(words)
    for w in words:
        if len(w) > 3:
            expanded.add(w.rstrip("s"))
    expanded.update(HIRING_KEYWORDS)
    return list(expanded)


def _post_matches_keywords(text: str, keywords: list[str]) -> bool:
    """Check if post text contains any keyword (case-insensitive)."""
    text_lower = text.lower()
    return any(
        re.search(r"\b" + re.escape(kw) + r"\b", text_lower)
        for kw in keywords
    )
```

- [ ] **Step 3: Add LLM extraction function**

Add after keyword filter:

```python
def _llm_extract_job(post_text: str, post_url: str, author: str, date: str) -> dict | None:
    """Extract structured job info from a Facebook post using LLM."""
    prompt = f"""You are a job listing extractor. Given a Vietnamese Facebook post,
extract job information. Return ONLY valid JSON, no explanation, no markdown.

Post text:
{post_text[:2000]}

Return JSON with this exact schema:
{{
  "is_job": true/false,
  "title": "Job title or null",
  "company": "Company name or null",
  "salary": "Salary range or null",
  "location": "Work location or null",
  "contact": "Email/phone/telegram or null",
  "description": "Brief summary (max 200 chars, Vietnamese) or null"
}}

Rules:
- is_job=true ONLY if the post is clearly advertising a job opening
- NOT a job if: selling courses, looking for job (người tìm việc), sharing articles
- Extract ALL available fields, use null for missing
- Do NOT invent information not in the post"""

    try:
        resp = LLM_CLIENT.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        text = resp.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("\n", 1)[0]
        data = json_mod.loads(text)
        if not data.get("is_job"):
            return None
        return {
            "job_title": data.get("title") or "Unknown",
            "company": data.get("company") or author or "Unknown",
            "portal": "Facebook",
            "location": data.get("location") or "",
            "salary": data.get("salary") or "",
            "job_url": post_url,
            "description": data.get("description") or "",
            "posted_date": date or "",
            "source_id": f"fb_{hash(post_url) & 0x7FFFFFFF:08x}",
        }
    except Exception as e:
        print(f"[search_adapter] LLM extract error: {e}")
        return None
```

- [ ] **Step 4: Add search_facebook() main function**

Add after LLM extraction:

```python
async def _crawl_facebook_group(
    crawler: AsyncWebCrawler, group_url: str, keywords: list[str], limit: int
) -> list[dict]:
    """Crawl one Facebook group and extract job posts."""
    jobs = []
    try:
        result = await crawler.arun(
            url=group_url,
            config=CrawlerRunConfig(
                wait_for="div[role='feed']",
                page_timeout=30000,
                scan_full_page=True,
            ),
        )
        if not result or not result.success:
            print(f"[search_adapter] Failed to load group: {group_url}")
            return jobs

        markdown = result.markdown or ""
        # Split into individual posts by common FB post separators
        posts = re.split(r"\n---\n|\n####\n|\n\n\[", markdown)

        for post_text in posts[:limit * 2]:
            post_text = post_text.strip()
            if len(post_text) < 50 or not _post_matches_keywords(post_text, keywords):
                continue

            # Extract post URL if present
            url_match = re.search(r"https://facebook\.com/[^\s)\]]+", post_text)
            post_url = url_match.group(0) if url_match else group_url
            author_match = re.search(r"^\*?\*?([A-ZÀ-ỹ][a-zà-ỹ]+(?:\s[A-ZÀ-ỹ][a-zà-ỹ]+){1,4})\*?\*?", post_text)
            author = author_match.group(1) if author_match else ""

            job = _llm_extract_job(post_text, post_url, author, "")
            if job:
                jobs.append(job)
                if len(jobs) >= limit:
                    break

    except Exception as e:
        print(f"[search_adapter] Facebook crawl error for {group_url}: {e}")

    return jobs


def search_facebook(query: str, location: str = "", limit: int = 10) -> list[dict]:
    """Search Facebook groups for job posts matching query.

    Uses crawl4ai with managed browser profile for authenticated FB access.
    Requires: crwl profiles setup with 'fb-clone' profile logged into FB.
    """
    import asyncio

    # Load group config
    config_path = Path(__file__).parent / "fb_groups.json"
    if not config_path.exists():
        print("[search_adapter] fb_groups.json not found")
        return []

    with open(config_path) as f:
        config = json_mod.load(f)

    groups = config.get("groups", [])
    if not groups:
        return []

    keywords = _expand_keywords(query)
    profile_dir = os.path.expanduser("~/.crawl4ai/profiles/fb-clone")

    if not os.path.isdir(profile_dir):
        print(f"[search_adapter] FB profile not found at {profile_dir}. Run: crwl profiles")
        return []

    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        user_data_dir=profile_dir,
        browser_type="chromium",
    )

    async def _crawl():
        jobs = []
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for group in groups:
                group_jobs = await _crawl_facebook_group(
                    crawler, group["url"], keywords, max(limit // len(groups), 3)
                )
                jobs.extend(group_jobs)
                if len(jobs) >= limit:
                    break
        return jobs[:limit]

    try:
        return asyncio.run(_crawl())
    except Exception as e:
        print(f"[search_adapter] Facebook search error: {e}")
        return []
```

- [ ] **Step 5: Commit**

```bash
git add web/search_adapter.py
git commit -m "feat: add search_facebook() with crawl4ai + LLM extraction"
```

---

### Task 3: Register Facebook in search_all() and server.py

**Files:**
- Modify: `web/search_adapter.py` — update `search_all()` to support "Facebook"
- Modify: `web/server.py` — add "Facebook" to `/api/portals`

**Interfaces:**
- Consumes: `search_facebook()` (from Task 2)
- Produces: Facebook results flow through existing `search_all()` → API → DB pipeline

- [ ] **Step 1: Update search_all() in search_adapter.py**

Patch `search_all()` — find the `for portal in portals:` loop and add:

```python
            elif portal == "Facebook":
                jobs = search_facebook(query, location, limit)
```

Insert right after the `Freehire` elif block.

Change default portals to include Facebook:

```python
    if portals is None:
        portals = ["ITviec", "Facebook"]
```

- [ ] **Step 2: Update server.py /api/portals**

Patch `list_portals()` — change return line:

```python
    return {"portals": ["ITviec", "LinkedIn", "Freehire", "Facebook"]}
```

- [ ] **Step 3: Commit**

```bash
git add web/search_adapter.py web/server.py
git commit -m "feat: register Facebook portal in search_all() and API"
```

---

### Task 4: Test and verify

- [ ] **Step 1: Verify crawl4ai setup**

```bash
python3 -c "from crawl4ai import AsyncWebCrawler; print('crawl4ai OK')"
```
Expected: `crawl4ai OK`

- [ ] **Step 2: Start server and test Facebook portal listing**

```bash
cd /home/jamesnguyen106/Downloads/ai-job-search-vn/web
fuser -k 8765/tcp 2>/dev/null; sleep 1
python3 server.py &
sleep 2
curl -s http://localhost:8765/api/portals | python3 -m json.tool
```
Expected: `{"portals": ["ITviec", "LinkedIn", "Freehire", "Facebook"]}`

- [ ] **Step 3: Test search_facebook() directly (without LLM — just crawl)**

```bash
cd /home/jamesnguyen106/Downloads/ai-job-search-vn
python3 -c "
from web.search_adapter import search_facebook
# This will fail gracefully if fb-clone profile doesn't exist yet
results = search_facebook('AI Engineer', '', 3)
print(f'Results: {len(results)}')
# If profile not set up yet, expect 0 results + print message
"
```
Expected: Either 0 results with message "FB profile not found" (if setup not done), or real results (if profile exists).

- [ ] **Step 4: Test API endpoint**

```bash
curl -s -X POST http://localhost:8765/api/search/realtime \
  -H 'Content-Type: application/json' \
  -d '{"query":"python","limit":5,"portals":["Facebook"]}' | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'Found: {d[\"total_found\"]}, Stored: {d[\"stored\"]}')
"
```
Expected: Graceful handling — returns 0 without crashing even if FB profile not set up.

- [ ] **Step 5: Commit test verification**

```bash
git add -A
git diff --cached --stat
git commit -m "test: verify Facebook portal integration end-to-end"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ Section 2 (Architecture) → Task 2 (search_facebook) + Task 3 (registration)
- ✅ Section 3 (Data Flow) → Task 2 steps 2-4 (keyword filter, LLM extract, crawl)
- ✅ Section 4 (Implementation Files) → Tasks 1-3 cover all 5 files
- ✅ Section 5 (Setup & Dependencies) → Task 1 step 1, warmup_guide.md
- ✅ Section 6 (Error Handling) → All error cases handled with try/except + prints
- ✅ Section 7 (Testing) → Task 4

**2. Placeholder scan:** ✅ No TBD, TODO, or vague instructions. All code shown inline.

**3. Type consistency:** ✅ `search_facebook()` returns `list[dict]` (matching `search_itviec()`). Keys match `_normalize()` output. `search_all()` consumes same interface.
