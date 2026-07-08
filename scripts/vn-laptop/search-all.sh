#!/bin/bash
# Search all VN job portals — run from your laptop in Vietnam
# Prerequisites: bun, agent-browser (npm i -g agent-browser && agent-browser install)

QUERY="${1:-AI Engineer}"
LOCATION="${2:-Ho Chi Minh}"
LIMIT="${3:-5}"
REPO="$HOME/Downloads/ai-job-search-vn"

echo "🔍 Searching: $QUERY in $LOCATION"
echo "========================================"

echo ""
echo "📌 ITVIEC"
cd "$REPO/.agents/skills/itviec-search/cli"
bun run src/cli.ts search -q "$QUERY" -l "$LOCATION" --limit "$LIMIT" --format table 2>/dev/null

echo ""
echo "📌 LINKEDIN VN"
cd "$REPO"
bun run .agents/skills/linkedin-search/cli/src/cli.ts search \
  -q "$QUERY" -l "$LOCATION City, Vietnam" --limit "$LIMIT" --format table 2>/dev/null

echo ""
echo "📌 TOPCV (browser — cần agent-browser)"
# agent-browser navigate "https://www.topcv.vn/tim-viec-lam-${QUERY// /-}" --timeout 20000
# agent-browser snapshot
echo "  (chạy thủ công: mở trình duyệt https://www.topcv.vn/tim-viec-lam)"
echo ""
echo "📌 VIETNAMWORKS (browser)"
# agent-browser navigate "https://www.vietnamworks.com/viec-lam?q=${QUERY// /+}" --timeout 20000
echo "  (chạy thủ công: mở trình duyệt https://www.vietnamworks.com/viec-lam)"
