// Data source: ITviec.com public job pages (server-rendered HTML).
// Requires Vietnam IP. We parse the HTML directly — jobs are in SSR markup
// around "Sign in to view salary" anchor tags.

export const SEARCH_URL = "https://itviec.com/it-jobs"
export const DETAIL_URL = "https://itviec.com/it-jobs"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

export async function htmlFetch(url: string): Promise<string> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const resp = await fetch(url, {
      headers: { "User-Agent": UA, "Accept-Language": "en-US,en;q=0.9,vi;q=0.8" },
      redirect: "follow",
    })
    if (resp.status === 429 || resp.status >= 500) {
      if (attempt === maxRetries) throw new Error(`${resp.status}`)
      await new Promise((r) => setTimeout(r, delay + Math.random() * 500))
      delay = Math.min(delay * 2, 8000)
      continue
    }
    if (resp.status === 404) return ""
    if (!resp.ok) throw new Error(`${resp.status}`)
    return resp.text()
  }
  throw new Error("Max retries")
}

export interface JobCard {
  id: string; title: string; company: string | null
  location: string | null; date: string | null; url: string
  salary: string | null; tags: string[]
}

export interface JobDetail extends JobCard {
  description: string | null; requirements: string | null
  benefits: string | null; applyUrl: string | null
}

function decodeHtml(text: string): string {
  return text
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&#[xX]([0-9a-fA-F]+);/g, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim()
}

/**
 * Parse job cards from ITviec search HTML.
 * Jobs are server-rendered. Each card is anchored by a
 * "Sign in to view salary" link containing the job slug.
 * Title and company name appear as text nodes in the ~2000 chars
 * before the salary marker.
 */
export function parseJobCards(html: string): JobCard[] {
  const results: JobCard[] = []
  const seen = new Set<string>()

  // Find all salary sign-in markers
  const re = /href="\/sign_in\?job=([^"&]+)[^"]*view_salary_source=search_page/g
  let match: RegExpExecArray | null

  while ((match = re.exec(html)) !== null) {
    const slug = decodeHtml(match[1])
    if (seen.has(slug)) continue
    seen.add(slug)

    const pos = match.index
    const ctx = html.slice(Math.max(0, pos - 3500), pos + 200)

    // Title: extract from <h3> tag
    const h3Match = ctx.match(/<h3[^>]*>([\s\S]*?)<\/h3>/i)
    const title = h3Match ? decodeHtml(h3Match[1].replace(/\n/g, " ")).trim() : ""

    // Company: find a company link text
    const companyLinkMatch = ctx.match(/href="\/companies\/[^"]*"[^>]*>([^<]+)<\/a>/i)
    const company = companyLinkMatch ? decodeHtml(companyLinkMatch[1]) : null

    // Location
    const locMatch = ctx.match(/(Ho Chi Minh|Ha Noi|Da Nang|Hà Nội|Đà Nẵng|Remote)/i)

    // Skill tags from context
    const skillRe = /href="\/it-jobs\/([^"?]+)\?click_source=Skill\+tag"[^>]*>([^<]+)<\/a>/gi
    const tags: string[] = []
    let sm: RegExpExecArray | null
    while ((sm = skillRe.exec(ctx)) !== null) {
      const tag = decodeHtml(sm[2])
      if (!tags.includes(tag)) tags.push(tag)
    }

    // Salary indicator
    const salary = ctx.includes("Sign in to view salary") ? "Confidential" : null

    results.push({
      id: slug,
      title,
      company: company || null,
      location: locMatch ? locMatch[0] : null,
      date: null,
      url: `https://itviec.com/it-jobs/${slug}`,
      salary,
      tags,
    })
  }

  return results
}

export function parseJobDetail(html: string, id: string): JobDetail {
  const titleMatch = html.match(/<title>([^<]*)<\/title>/i)
  const title = titleMatch ? decodeHtml(titleMatch[1].replace(/\s*\|\s*ITviec.*/i, "")) : id

  const companyMatch = html.match(/>([^<]{3,60})<\/a>[^<]{0,50}<\/(h\d|span|div)>/i)
  const company = companyMatch ? decodeHtml(companyMatch[1]) : null

  // Description
  const descRe = /<div[^>]*class="[^"]*description[^"]*"[^>]*>([\s\S]*?)<\/div>/i
  const descMatch = html.match(descRe)
  let description: string | null = null
  if (descMatch) {
    description = decodeHtml(descMatch[1].replace(/<[^>]+>/g, " ")
      .replace(/\s+/g, " ")).trim() || null
  }

  return {
    id, title, company, location: null, date: null,
    url: `https://itviec.com/it-jobs/${id}`,
    salary: null, tags: [],
    description, requirements: null, benefits: null, applyUrl: null,
  }
}

/** Convert query to ITviec URL path slug (spaces → hyphens, lowercase) */
export function queryToPath(query: string): string {
  return encodeURIComponent(query.trim()).replace(/%20/g, "-")
}
