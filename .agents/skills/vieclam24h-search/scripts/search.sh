#!/bin/bash
# Vieclam24h Job Search — dùng agent-browser render SPA
QUERY="${1:-AI Engineer}"; LIMIT=10
[[ "$2" == "--limit" && -n "$3" ]] && LIMIT="$3"
SEARCH_URL="https://vieclam24h.vn/tim-kiem-viec-lam-nhanh?q=$(echo "$QUERY" | sed 's/ /+/g')"

echo "🔍 Vieclam24h: $QUERY"
echo ""

agent-browser close --all 2>/dev/null
agent-browser open "$SEARCH_URL" --timeout 20000 > /dev/null 2>&1
sleep 4
agent-browser wait --load networkidle --timeout 15000 > /dev/null 2>&1

# Job links có icon  (title|company separator) — lọc chính xác
agent-browser snapshot -i 2>/dev/null \
  | grep 'link "' | grep '' \
  | sed 's/^\s*- link "//;s/" \[ref=e[0-9]*\]//' \
  | sed 's/  / | /g; s/  / | /g; s/  / | /g; s/  / | /g' \
  | head -n "$LIMIT" \
  | awk -F' \\| ' '{printf "%-55s %-35s %s\n", $1, $2, $3}'

agent-browser close --all > /dev/null 2>&1