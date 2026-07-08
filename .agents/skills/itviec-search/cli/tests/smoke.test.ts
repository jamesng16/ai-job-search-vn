import { describe, test, expect } from "bun:test"
import { runCLI, parseJSON } from "./helpers"

describe("itviec-search smoke test (VN IP required)", () => {
  test("search with --help shows usage", () => {
    const { stderr, exitCode } = runCLI(["--help"])
    expect(exitCode).toBe(0)
    expect(stderr).toContain("Usage:")
  })

  test("search without --query exits 1", () => {
    const { stderr, exitCode } = runCLI(["search"])
    expect(exitCode).toBe(1)
    expect(stderr).toContain("error")
  })

  test("search with bogus flag still runs (ignores unknown flags)", () => {
    const { exitCode } = runCLI(["search", "-q", "test", "--bogus"])
    // Unknown flags are silently ignored; the search still runs
    expect(exitCode).toBe(0)
  })

  test("detail without id exits 1", () => {
    const { stderr, exitCode } = runCLI(["detail"])
    expect(exitCode).toBe(1)
    expect(stderr).toContain("error")
  })

  // Live test — confirmed working from VN IP
  test("search returns real results (VN IP)", () => {
    const { stdout, exitCode } = runCLI([
      "search", "-q", "AI Engineer", "--limit", "3", "--format", "json",
    ])
    expect(exitCode).toBe(0)
    const data = parseJSON(stdout)
    expect(data.results.length).toBeGreaterThan(0)
    expect(data.results[0].id).toBeTruthy()
    expect(data.results[0].title).toBeTruthy()
    expect(data.results[0].url).toBeTruthy()
  })
})
