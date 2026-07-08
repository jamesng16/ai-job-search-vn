// Data source: ITviec.com public job pages. Requires Vietnam IP address.
// Search returns server-rendered HTML with job cards; detail returns full job page.
// We parse both with regex. Cloudflare WAF blocks non-VN IPs.

export const SEARCH_URL = "https://itviec.com/it-jobs"
export const DETAIL_URL = "https://itviec.com/jobs"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

/** Fetch HTML with exponential backoff on 429/5xx. Returns "" on a 404. */
export async function htmlFetch(url: string): Promise<string> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      headers: {
        "User-Agent": UA,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
      },
      redirect: "follow",
    })
    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) {
        throw new Error(`Request failed: ${response.status} ${response.statusText}`)
      }
      const jitter = Math.floor(Math.random() * 500)
      await new Promise((r) => setTimeout(r, delay + jitter))
      delay = Math.min(delay * 2, 8000)
      continue
    }
    if (response.status === 404) return ""
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    return response.text()
  }
  throw new Error("Request failed after max retries")
}

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  url: string
  salary: string | null
  tags: string[]
}

export interface JobDetail extends JobCard {
  description: string | null
  requirements: string | null
  benefits: string | null
  applyUrl: string | null
}

function decodeHtmlEntities(text: string): string {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(parseInt(dec, 10)))
    .replace(/&#[xX]([0-9a-fA-F]+);/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/&nbsp;/g, " ")
}

function stripTags(html: string): string {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()
}

function clean(html: string): string {
  return decodeHtmlEntities(stripTags(html))
}

/**
 * Parse the search response HTML. ITviec renders job cards server-side
 * in the initial HTML payload. We extract from known markup patterns.
 *
 * Job cards in ITviec HTML are typically in blocks containing:
 * - A link with /jobs/<id> pattern
 * - Job title
 * - Company name
 * - Location
 * - Salary (optional)
 * - Tags (skills, level)
 */
export function parseJobCards(html: string): JobCard[] {
  const results: JobCard[] = []

  // Split on job detail links to isolate individual cards
  const chunks = html.split(/href="\/jobs\/(\d{4,})"/)
  // chunks[0] = before first job, chunks[1]=id1, chunks[2]=after id1,
  // chunks[3]=id2, chunks[4]=after id2, ...

  for (let i = 1; i < chunks.length; i += 2) {
    const id = chunks[i]
    const chunk = chunks[i + 1] || ""

    // Try to find title near the link
    let title: string | null = null
    const titlePatterns = [
      /<h\d[^>]*class="[^"]*job[^"]*title[^"]*"[^>]*>([\s\S]*?)<\/h\d>/i,
      /<h\d[^>]*>([\s\S]*?)<\/h\d>/i,
      /class="[^"]*title[^"]*"[^>]*>([\s\S]*?)<\//i,
    ]
    for (const pat of titlePatterns) {
      const m = chunk.match(pat)
      if (m) { title = clean(m[1]); break }
    }
    if (!title || title.length < 3) continue

    // Company name
    let company: string | null = null
    const companyPatterns = [
      /<[^>]*class="[^"]*company[^"]*"[^>]*>([\s\S]*?)<\//i,
      /company[^"]*"[^>]*>([\s\S]*?)<\//i,
      /<img[^>]*alt="([^"]*)"[^>]*>/i,
    ]
    for (const pat of companyPatterns) {
      const m = chunk.match(pat)
      if (m) { company = clean(m[1]) || null; break }
    }

    // Location
    let location: string | null = null
    const locMatch = chunk.match(/(?:Ho Chi Minh|Ha Noi|Da Nang|Remote|Hà Nội|Đà Nẵng)/i)
    if (locMatch) location = locMatch[0]

    // Salary
    let salary: string | null = null
    const salaryMatch = chunk.match(/(?:\$\d[\d,]*|\d[\d,]*\s?(?:USD|VND|triệu|M)|Up to \$[\d,]+)/i)
    if (salaryMatch) salary = salaryMatch[0]

    // Tags
    const tags: string[] = []
    const tagRe = /<[^>]*class="[^"]*tag[^"]*"[^>]*>([^<]+)<\/[^>]*>/gi
    let tagMatch: RegExpExecArray | null
    while ((tagMatch = tagRe.exec(chunk)) !== null) {
      const t = clean(tagMatch[1])
      if (t && !tags.includes(t)) tags.push(t)
    }

    results.push({
      id,
      title,
      company,
      location,
      date: null, // ITviec doesn't consistently show posting date
      url: `https://itviec.com/jobs/${id}`,
      salary,
      tags,
    })
  }

  return results
}

/** Parse the single-job detail page. */
export function parseJobDetail(html: string, id: string): JobDetail {
  // Title
  const titleMatch = html.match(/<title>([^<]*)<\/title>/i)
  const title = titleMatch ? clean(titleMatch[1].replace(/\s*\|\s*ITviec.*$/i, "")) : "(untitled)"

  // Company
  let company: string | null = null
  const companyMatch = html.match(/<[^>]*class="[^"]*company[^"]*"[^>]*>([\s\S]*?)<\//i)
  if (companyMatch) company = clean(companyMatch[1]) || null

  // Location
  let location: string | null = null
  const locMatch = html.match(/(?:Ho Chi Minh|Ha Noi|Da Nang|Remote|Hà Nội|Đà Nẵng)/i)
  if (locMatch) location = locMatch[0]

  // Description — extract from the main content area
  let description: string | null = null
  const descPatterns = [
    /class="[^"]*description[^"]*"[^>]*>([\s\S]*?)<\/div>/i,
    /id="[^"]*description[^"]*"[^>]*>([\s\S]*?)<\/div>/i,
  ]
  for (const pat of descPatterns) {
    const m = html.match(pat)
    if (m) {
      const withBreaks = m[1]
        .replace(/<\s*br\s*\/?>/gi, "\n")
        .replace(/<\/(p|li|ul|ol|div|h\d)>/gi, "\n")
      description = decodeHtmlEntities(stripTags(withBreaks))
        .replace(/\n{3,}/g, "\n\n").trim() || null
      break
    }
  }

  // Requirements section
  let requirements: string | null = null
  const reqMatch = html.match(/requirements?[^>]*>([\s\S]*?)(?:benefits|why you|\$)/i)
  if (reqMatch) requirements = clean(reqMatch[1]) || null

  // Benefits section
  let benefits: string | null = null
  const benMatch = html.match(/benefits?[^>]*>([\s\S]*?)(?:<\/div|apply)/i)
  if (benMatch) benefits = clean(benMatch[1]) || null

  // Apply link
  let applyUrl: string | null = null
  const applyMatch = html.match(/href="([^"]*\bapply[^"]*)"[^>]*>/i)
  if (applyMatch) applyUrl = decodeHtmlEntities(applyMatch[1])

  return {
    id,
    title,
    company,
    location,
    date: null,
    url: `https://itviec.com/jobs/${id}`,
    salary: null,
    tags: [],
    description,
    requirements,
    benefits,
    applyUrl,
  }
}
