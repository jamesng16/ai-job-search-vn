# Running from your laptop in Vietnam

These scripts work from your laptop with a Vietnam IP address.

## Prerequisites

```bash
# Install bun (JS runtime)
curl -fsSL https://bun.sh/install | bash

# Install agent-browser (for TopCV/VietnamWorks)
npm i -g agent-browser && agent-browser install --with-deps
```

## Usage

```bash
# Search all portals at once
./scripts/vn-laptop/search-all.sh "AI Engineer" "Ho Chi Minh"

# Search specific portal
cd .agents/skills/itviec-search/cli
bun install
bun run src/cli.ts search -q "AI Engineer" -l "Ho Chi Minh" --format table

# LinkedIn VN
cd ../..
bun run .agents/skills/linkedin-search/cli/src/cli.ts search \
  -q "AI Engineer" -l "Ho Chi Minh City, Vietnam" --format table
```

## Portal Status (from VN IP)

| Portal | Method | Status |
|--------|--------|--------|
| ITviec | bun fetch | ✅ Works |
| LinkedIn VN | bun fetch | ✅ Works |
| TopCV | agent-browser | 🧪 Test from VN |
| VietnamWorks | agent-browser | 🧪 Test from VN |
