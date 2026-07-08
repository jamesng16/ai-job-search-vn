# ITviec URL Reference

## Search

**Endpoint:** `https://itviec.com/it-jobs`
**Method:** GET (HTML)
**Parameters:**

| Param   | Type   | Example        | Notes                                      |
|---------|--------|----------------|--------------------------------------------|
| query   | string | AI+Engineer    | URL-encoded search keyword                 |
| page    | int    | 1              | Page number                                |
| location| string | ho-chi-minh    | URL slug for city (optional)               |

**Response:** HTML page with job cards in `<div class="job-card">` blocks.
Server-side rendered — no JavaScript required for initial parse.

### Job Card HTML Structure (observed from web_extract)

```
<div class="job-card">
  <div class="job-title">...</div>         <!-- Title -->
  <div class="company-name">...</div>      <!-- Company -->
  <div class="location">...</div>          <!-- Location -->
  <a href="/jobs/<id>">...</a>            <!-- Detail link -->
  <div class="job-tags">...</div>          <!-- Tags: skills, level -->
  <div class="salary">...</div>            <!-- Salary (if available) -->
</div>
```

## Detail

**Endpoint:** `https://itviec.com/jobs/<id>`
**Method:** GET (HTML)
**Response:** Full job detail page with:
- Description (HTML with formatting)
- Requirements
- Benefits
- Company info
- Apply link

**Note:** ITviec uses a SPA (React). Detail page content is embedded in the
initial HTML but may also be loaded via API. The page title tag contains the
job title.

## API Endpoints (Require Authentication)

- `https://itviec.com/api/v1/jobs` — v1 API (returns `{"message":"Bad credentials!"}` without auth)
- `https://itviec.com/api/v2/jobs` — v2 API (returns empty `{}` without auth)

## Access Notes

- Cloudflare WAF protection — blocks non-VN IPs (403 or JS challenge)
- `robots.txt` returns empty `{}` (blocked by Cloudflare)
- User-Agent spoofing alone is insufficient; GeoIP filtering in place
- Test from a Vietnam-based IP address for development
