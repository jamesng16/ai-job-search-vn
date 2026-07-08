import {
  SEARCH_URL,
  htmlFetch,
  parseJobCards,
  writeError,
  type JobCard,
} from "../helpers.js"

interface SearchArgs {
  query: string
  location?: string
  page: number
  limit: number
  format: "json" | "table" | "plain"
}

function formatTable(results: JobCard[]): string {
  if (results.length === 0) return "(no results)"
  const lines: string[] = []
  // Header
  const idW = Math.max(6, ...results.map((r) => r.id.length))
  const titleW = Math.max(8, ...results.map((r) => r.title.length))
  const companyW = Math.max(8, ...results.map((r) => (r.company || "").length))
  const locW = Math.max(8, ...results.map((r) => (r.location || "").length))
  lines.push(
    `ID${" ".repeat(idW - 2)}  TITLE${" ".repeat(titleW - 5)}  COMPANY${" ".repeat(companyW - 7)}  LOCATION`,
  )
  lines.push(`${"-".repeat(idW)}  ${"-".repeat(titleW)}  ${"-".repeat(companyW)}  ${"-".repeat(locW)}`)
  for (const r of results) {
    lines.push(
      `${r.id.padEnd(idW)}  ${r.title.padEnd(titleW)}  ${(r.company || "?").padEnd(companyW)}  ${(r.location || "?").padEnd(locW)}`,
    )
  }
  return lines.join("\n")
}

export async function runSearch(args: SearchArgs): Promise<void> {
  const params = new URLSearchParams()
  params.set("query", args.query)
  if (args.page > 1) params.set("page", String(args.page))

  const url = `${SEARCH_URL}?${params.toString()}`
  let html: string
  try {
    html = await htmlFetch(url)
  } catch (e: any) {
    writeError(e.message || "Fetch failed", "FETCH_ERROR")
    process.exit(1)
  }

  if (!html) {
    writeError("No results or page not found", "NOT_FOUND")
    process.exit(1)
  }

  let results = parseJobCards(html)

  // Apply location filter client-side (ITviec search doesn't have clean location param)
  if (args.location) {
    const locLower = args.location.toLowerCase()
    results = results.filter((r) =>
      (r.location || "").toLowerCase().includes(locLower),
    )
  }

  // Apply limit
  if (args.limit > 0 && results.length > args.limit) {
    results = results.slice(0, args.limit)
  }

  switch (args.format) {
    case "json":
      process.stdout.write(
        JSON.stringify({ meta: { count: results.length, page: args.page }, results }) + "\n",
      )
      break
    case "table":
      process.stdout.write(formatTable(results) + "\n")
      break
    case "plain":
      for (const r of results) {
        process.stdout.write(`${r.id} | ${r.title} | ${r.company || "?"} | ${r.location || "?"}\n`)
      }
      break
  }
}
