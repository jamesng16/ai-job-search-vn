import { spawnSync } from "bun"

/** Run the CLI and return stdout, stderr, and exit code. */
export function runCLI(args: string[]): { stdout: string; stderr: string; exitCode: number } {
  const result = spawnSync({
    cmd: ["bun", "run", "src/cli.ts", ...args],
    stdout: "pipe",
    stderr: "pipe",
    env: { ...process.env },
  })
  return {
    stdout: result.stdout?.toString() || "",
    stderr: result.stderr?.toString() || "",
    exitCode: result.exitCode,
  }
}

/** Parse a CLI's JSON stdout output. */
export function parseJSON(text: string): any {
  return JSON.parse(text.trim())
}
