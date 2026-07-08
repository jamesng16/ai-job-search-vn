---
name: freehire-search
version: 1.0.0
description: >
  Search IT jobs globally via the freehire aggregator — one skill covering
  thousands of company boards (Greenhouse, Lever, Ashby, Workday, and more)
  across many countries. Use when the user wants to search for jobs across
  multiple sources at once, filter by region/country/category/seniority,
  or discover what skills are in demand. Trigger phrases: freehire, global
  job search, aggregator search, "find jobs worldwide", "search all boards",
  "what jobs match my skills", market-fit.
context: fork
allowed-tools: Bash(freehire:*)
---

# Freehire Search Skill

Search IT jobs across thousands of company boards through [freehire](https://freehire.dev) — an
open-source job aggregator (MIT license). One skill replaces many per-portal skills,
covering Greenhouse, Lever, Ashby, Workday-based boards, and more in a single
normalized schema.

> Uses the freehire CLI. Free API key required — create one at freehire.dev →
> Account → API Keys. The key is stored locally in `~/.freehire/creds.json`.

## Setup (one-time)

```bash
# Install the CLI (prebuilt binary, no Go needed)
curl -fsSL https://freehire.dev/install.sh | sh

# Authenticate with your free API key
freehire auth login --token <your-api-key>
# Or via env var (CI/ephemeral): export FREEHIRE_TOKEN=<key>
```

## When to use this skill

- Search jobs across ALL sources at once (not one portal at a time)
- Filter by region, country, city, remote, category, seniority, salary
- Discover what skills the market demands with `market-fit`
- Get a job's full description and apply link with `job`
- Track applications (save, apply, stage, note)

## Commands

### Search jobs

```bash
freehire search "<query>" [flags]
```

Key flags:
- `--remote` — remote-only jobs
- `--region <region>` — e.g. `asia`, `europe`, `north-america`
- `--country <code>` — ISO 3166-1 alpha-2, e.g. `vn`, `us`, `de`
- `--city <name>` — city name
- `--category <name>` — e.g. `backend`, `frontend`, `data`, `devops`
- `--seniority <level>` — e.g. `junior`, `mid`, `senior`, `staff`, `principal`
- `--employment-type <type>` — e.g. `full-time`, `contract`, `part-time`
- `--salary-min <amount>` — minimum salary
- `--skills <list>` — filter to jobs listing these skills (comma-sep)
- `--facet key=value` — any other API facet (repeatable)
- `--limit <n>` — max results (default 20)
- `--json` — machine-readable output (recommended for agents)

### Get job detail

```bash
freehire job <slug>
```

### Discover filters & skills

```bash
freehire facets [--category <name>] [--region <region>] ...
```

### Market fit — score your skills

```bash
freehire market-fit --skills "python,rag,langgraph,yolo,fastapi" [filters...]
```

### Track applications

```bash
freehire save <slug>
freehire apply <slug>
freehire my
```

## Usage examples

```bash
# AI Engineer jobs, remote, in Asia
freehire search "AI Engineer" --remote --region asia --limit 10 --json

# Backend Go jobs in Germany, senior level
freehire search "golang" --country de --seniority senior --json

# Discover what facets are available for data roles
freehire facets --category data

# Score your skills against the frontend market
freehire market-fit --skills "react,typescript,nextjs" --category frontend --remote

# Track a job through your pipeline
freehire save linear-senior-backend-engineer
freehire apply linear-senior-backend-engineer
freehire stage linear-senior-backend-engineer interview
```

## Output format

With `--json`: raw API JSON payload — ideal for piping to `jq` or agent consumption.
Without: human-readable table.

All errors go to **stderr** with non-zero exit code.

## Notes

- freehire aggregates from company ATS boards (Greenhouse, Lever, Ashby, etc.) — no recruiter spam
- One schema, deduplicated: the same role across boards collapses to one entry
- Liveness-swept: dead links are removed, what you open is still open
- Open source (MIT) — source at https://github.com/strelov1/freehire
- CLI source at https://github.com/strelov1/freehire-cli
- Free API key from freehire.dev → Account → API Keys
