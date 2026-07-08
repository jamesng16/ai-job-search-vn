import {
  DETAIL_URL,
  htmlFetch,
  parseJobDetail,
  writeError,
  type JobDetail,
} from "../helpers.js"

interface DetailArgs {
  id: string
  format: "json" | "plain"
}

export async function runDetail(args: DetailArgs): Promise<void> {
  // Extract ID from URL if a full URL is passed
  let id = args.id
  const urlMatch = id.match(/itviec\.com\/jobs\/(\d+)/)
  if (urlMatch) id = urlMatch[1]

  const url = `${DETAIL_URL}/${id}`
  let html: string
  try {
    html = await htmlFetch(url)
  } catch (e: any) {
    writeError(e.message || "Fetch failed", "FETCH_ERROR")
    process.exit(1)
  }

  if (!html) {
    writeError("Job not found", "NOT_FOUND")
    process.exit(1)
  }

  const detail: JobDetail = parseJobDetail(html, id)

  switch (args.format) {
    case "json":
      process.stdout.write(JSON.stringify(detail) + "\n")
      break
    case "plain":
      process.stdout.write(`${detail.title}\n`)
      process.stdout.write(`${detail.company || "?"} — ${detail.location || "?"}\n`)
      process.stdout.write(`${"-".repeat(60)}\n\n`)
      if (detail.description) {
        process.stdout.write(detail.description + "\n\n")
      }
      if (detail.requirements) {
        process.stdout.write("YÊU CẦU:\n" + detail.requirements + "\n\n")
      }
      if (detail.benefits) {
        process.stdout.write("PHÚC LỢI:\n" + detail.benefits + "\n\n")
      }
      if (detail.applyUrl) {
        process.stdout.write(`Apply: ${detail.applyUrl}\n`)
      }
      break
  }
}
