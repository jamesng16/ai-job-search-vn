"""Search adapter: calls real CLI tools for VN job portals."""
import subprocess
import json
import os
import time
import hashlib
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
import json as json_mod
import re
from openai import OpenAI
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

REPO = Path("/home/jamesnguyen106/Downloads/ai-job-search-vn")
SKILLS_DIR = REPO / ".agents/skills"
BUN = "/home/jamesnguyen106/.bun/bin/bun"
BUN_DIR = os.path.dirname(BUN)

LLM_CLIENT = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY")
            or os.environ.get("CUSTOM_PROVIDER_API_AI_BOX_VN_KEY")
            or os.environ.get("OPENAI_API_KEY", ""),
    base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.ai-box.vn/v1"),
)
LLM_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")


def _run(cmd: list[str], cwd: Path, timeout: int = 30) -> dict:
    """Run a command and return JSON output, or empty results on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(cwd), env={**os.environ, "PATH": f"{os.environ['PATH']}:{BUN_DIR}"}
        )
        if result.returncode != 0:
            print(f"[search_adapter] {cmd[0]} exited {result.returncode}: {result.stderr[:200]}")
            return {"results": [], "meta": {"count": 0, "error": result.stderr[:200]}}
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"results": [], "meta": {"count": 0, "error": "timeout"}}
    except json.JSONDecodeError as e:
        return {"results": [], "meta": {"count": 0, "error": str(e)}}
    except Exception as e:
        return {"results": [], "meta": {"count": 0, "error": str(e)}}


def _normalize(job: dict, portal: str) -> dict:
    """Normalize job fields to our DB schema."""
    return {
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "portal": portal,
        "location": job.get("location") or "Ho Chi Minh City",
        "salary": job.get("salary") or "",
        "job_url": job.get("url", ""),
        "description": "",
        "posted_date": job.get("date") or time.strftime("%Y-%m-%d"),
        "source_id": job.get("id", ""),
    }


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
    """Check if post text contains any keyword (case-insensitive, simple substring)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _extract_posted_date(text: str) -> str:
    """Extract a posted date from post text using regex patterns.
    
    Supports: ISO dates (2024-07-10), DD/MM/YYYY, 'hôm nay', 'hôm qua'.
    Returns YYYY-MM-DD string or empty string.
    """
    # ISO format: 2024-07-10 or 2024-07-10T12:00:00
    iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso_match:
        return f"{iso_match.group(1)}-{iso_match.group(2)}-{iso_match.group(3)}"

    # DD/MM/YYYY format: 10/07/2024
    slash_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", text)
    if slash_match:
        return f"{slash_match.group(3)}-{slash_match.group(2)}-{slash_match.group(1)}"

    # Vietnamese relative dates
    text_lower = text.lower()
    today = date.today()
    if "hôm nay" in text_lower:
        return today.isoformat()
    if "hôm qua" in text_lower:
        return (today - timedelta(days=1)).isoformat()

    return ""


def _llm_extract_job(post_text: str, post_url: str, author: str, date: str) -> dict | None:
    """Extract structured job info from a Facebook post using LLM."""
    prompt = f"""You are a job listing extractor for Vietnamese Facebook posts.
Extract job information from the post below. Posts may contain both Vietnamese text
and image descriptions (OCR-like text from job posters).

Return ONLY valid JSON, no explanation, no markdown.

Post:
{post_text[:3000]}

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
- If the post contains an image description with job titles (e.g. \"PHP DEVELOPER\", \"AI Engineer\"), extract ALL listed jobs
- For company name: use the author name if company not explicitly stated
- Extract ALL available fields, use null for missing
- Do NOT invent information not in the post"""

    try:
        max_retries = 3
        text = None
        for attempt in range(max_retries):
            try:
                resp = LLM_CLIENT.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500,
                )
                text = resp.choices[0].message.content.strip()
                break
            except Exception as retry_e:
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    print(f"[search_adapter] LLM retry {attempt + 1}/{max_retries} after {delay}s: {retry_e}")
                    time.sleep(delay)
                else:
                    raise
        if text is None:
            return None
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
            "source_id": f"fb_{hashlib.sha256(post_url.encode()).hexdigest()[:16]}",
        }
    except Exception as e:
        print(f"[search_adapter] LLM extract error: {e}")
        return None


def search_itviec(query: str, location: str = "", limit: int = 10) -> list[dict]:
    """Search ITviec via bun CLI. Location filter applied client-side (ITviec API doesn't support -l reliably)."""
    cli_dir = SKILLS_DIR / "itviec-search" / "cli"
    cmd = [str(BUN), "run", "src/cli.ts", "search",
           "-q", query, "-n", str(min(limit * 3, 50)), "--format", "json"]
    data = _run(cmd, cwd=cli_dir, timeout=30)
    jobs = [_normalize(j, "ITviec") for j in data.get("results", [])]
    # Client-side location filter
    if location:
        loc_lower = location.lower()
        jobs = [j for j in jobs if loc_lower in (j.get("location") or "").lower()]
    return jobs[:limit]


def search_linkedin(query: str, location: str = "", limit: int = 10) -> list[dict]:
    """Search LinkedIn VN via bun CLI."""
    cli_ts = SKILLS_DIR / "linkedin-search" / "cli" / "src" / "cli.ts"
    loc = f"{location} City, Vietnam" if location else "Ho Chi Minh City, Vietnam"
    cmd = [str(BUN), "run", str(cli_ts), "search",
           "-q", query, "-l", loc, "--limit", str(limit), "--format", "json"]
    data = _run(cmd, cwd=REPO, timeout=30)
    return [_normalize(j, "LinkedIn") for j in data.get("results", [])]


def search_freehire(query: str, location: str = "", limit: int = 10) -> list[dict]:
    """Search Freehire via CLI (Go binary or API)."""
    freehire_bin = os.path.expanduser("~/.local/bin/freehire")
    if not os.path.exists(freehire_bin):
        freehire_bin = "freehire"
    cmd = [freehire_bin, "search", query, "--country", "vn", "--limit", str(limit)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return []
        # freehire outputs line-delimited JSON or table; try JSON parse
        data = json.loads(result.stdout)
        if isinstance(data, list):
            return [_normalize(j, "Freehire") for j in data]
        if isinstance(data, dict) and "results" in data:
            return [_normalize(j, "Freehire") for j in data["results"]]
        return []
    except Exception:
        return []


async def _crawl_facebook_group(
    crawler: AsyncWebCrawler, group_url: str, keywords: list[str], location: str, limit: int
) -> list[dict]:
    """Crawl one Facebook group and extract job posts."""
    jobs = []
    try:
        result = await crawler.arun(
            url=group_url,
            config=CrawlerRunConfig(
                magic=True,
                page_timeout=20000,
            ),
        )
        if not result or not result.success:
            print(f"[search_adapter] Failed to load group: {group_url}")
            return jobs

        markdown = result.markdown or ""
        # Facebook mbasic: posts start with ## **AuthorName**
        # Also handle plain **Heading** (older format)
        raw_chunks = re.split(r"\n(?=##\s*\*\*|\*\*(?:\[)?[A-ZÀ-Ỹ])", markdown)
        if len(raw_chunks) <= 1:
            raw_chunks = re.split(r"\n\n+", markdown)
        # Remove nav/header chunk
        if raw_chunks and "**" not in raw_chunks[0][:200]:
            raw_chunks = raw_chunks[1:]
        # Merge small sub-chunks (like "**Yêu cầu:**") into previous chunk
        posts = []
        for chunk in raw_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            if posts and len(chunk) < 150 and not re.match(r"\*\*\[?[A-Z]", chunk):
                posts[-1] += "\n" + chunk  # merge sub-heading into parent post
            else:
                posts.append(chunk)

        for post_text in posts[:limit * 2]:
            post_text = post_text.strip()
            if len(post_text) < 50 or not _post_matches_keywords(post_text, keywords):
                continue

            # Extract post URL if present
            url_match = re.search(r"https://facebook\.com/[^\s)\]]+", post_text)
            post_url = url_match.group(0) if url_match else group_url
            author_match = re.search(r"^\*?\*?([A-ZÀ-ỹ][a-zà-ỹ]+(?:\s[A-ZÀ-ỹ][a-zà-ỹ]+){1,4})\*?\*?", post_text)
            author = author_match.group(1) if author_match else ""

            # Extract date from post text
            post_date = _extract_posted_date(post_text)

            job = _llm_extract_job(post_text, post_url, author, post_date)
            if job:
                # Filter by location if specified
                if location and location.lower() not in (job.get("location") or "").lower():
                    continue
                jobs.append(job)
                if len(jobs) >= limit:
                    break

    except Exception as e:
        print(f"[search_adapter] Facebook crawl error for {group_url}: {e}")

    return jobs


def search_facebook(query: str, location: str = "", limit: int = 10, max_groups: int = 8) -> list[dict]:
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

    keywords = _expand_keywords(f"{query} {location}")
    profile_dir = os.path.expanduser("~/.crawl4ai/profiles/fb")

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
            for group in groups[:max_groups]:
                group_jobs = await _crawl_facebook_group(
                    crawler, group["url"], keywords, location, max(limit // max_groups, 2)
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


def search_all(query: str, location: str = "", limit: int = 10,
               portals: Optional[list[str]] = None) -> list[dict]:
    """Search across specified portals (or all available)."""
    if portals is None:
        portals = ["ITviec"]  # default: only ITviec (fastest, always works)

    all_jobs = []
    for portal in portals:
        try:
            if portal == "ITviec":
                jobs = search_itviec(query, location, limit)
            elif portal == "LinkedIn":
                jobs = search_linkedin(query, location, limit)
            elif portal == "Freehire":
                jobs = search_freehire(query, location, limit)
            elif portal == "Facebook":
                jobs = search_facebook(query, location, limit)
            else:
                continue
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[search_adapter] {portal} error: {e}")

    return all_jobs
