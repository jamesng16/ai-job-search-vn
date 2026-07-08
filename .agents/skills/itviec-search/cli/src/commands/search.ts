import {
  SEARCH_URL,
  htmlFetch,
  parseJobCards,
  queryToPath,
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
  const idW = Math.max(5, ...results.map((r) => Math.min(r.id.length, 50)))
  const titleW = Math.max(8, ...results.map((r) => Math.min(r.title.length, 50)))
  const companyW = Math.max(8, ...results.map((r) => Math.min((r.company || "").length, 30)))
  const lines = [
    `ID${" ".repeat(idW - 2)}  TITLE${" ".repeat(titleW - 5)}  COMPANY${" ".repeat(companyW - 7)}  LOCATION`,
    `${"-".repeat(idW)}  ${"-".repeat(titleW)}  ${"-".repeat(companyW)}  ${"-".repeat(12)}`,
  ]
  for (const r of results) {
    lines.push(
      `${r.id.slice(0, idW).padEnd(idW)}  ${r.title.slice(0, titleW).padEnd(titleW)}  ${(r.company || "?").slice(0, companyW).padEnd(companyW)}  ${r.location || "?"}`,
    )
  }
  return lines.join("\n")
}

export async function runSearch(args: SearchArgs): Promise<void> {
  const path = queryToPath(args.query)
  const pageParam = args.page > 1 ? `?page=${args.page}` : ""
  const url = `${SEARCH_URL}/${path}${pageParam}`

  let html: string
  try { html = await htmlFetch(url) }
  catch (e: any) { writeError(e.message, "FETCH_ERROR"); process.exit(1) }

  if (!html) { writeError("No results", "NOT_FOUND"); process.exit(1) }

  let results = parseJobCards(html)

  if (args.location) {
    const loc = args.location.toLowerCase()
    results = results.filter((r) => (r.location || "").toLowerCase().includes(loc))
  }
  if (args.limit > 0) results = results.slice(0, args.limit)

  switch (args.format) {
    case "json":
      process.stdout.write(JSON.stringify({ meta: { count: results.length, page: args.page }, results }) + "\n")
      break
    case "table":
      process.stdout.write(formatTable(results) + "\n")
      break
    case "plain":
      for (const r of results) process.stdout.write(`${r.id} | ${r.title} | ${r.company || "?"} | ${r.location || "?"}\n`)
      break
  }
}
