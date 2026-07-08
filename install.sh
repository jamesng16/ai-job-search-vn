#!/bin/bash
# ============================================================
#  AI Job Search VN — Cài đặt toàn bộ chỉ với 1 lệnh
#  Repo: https://github.com/jamesng16/ai-job-search-vn
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
BOLD='\033[1m'

banner() { echo -e "\n${BOLD}${GREEN}==>${NC} ${BOLD}$1${NC}"; }
skip()  { echo -e "   ${YELLOW}⊘${NC} $1 (đã có)"; }
err()   { echo -e "   ${RED}✗${NC} $1"; }

# ─── Kiểm tra OS ────────────────────────────────────────────
banner "🔍 Kiểm tra hệ thống"
case "$(uname -s)" in
  Linux)   OS="linux";;
  Darwin)  OS="macos";;
  *)       echo "Chưa hỗ trợ OS này. Cần Linux hoặc macOS."; exit 1;;
esac
echo "   OS: $OS | Arch: $(uname -m)"

# ─── 1. Bun (JS runtime cho ITviec + LinkedIn) ─────────────
banner "🥟 Bun — JavaScript runtime"
if command -v bun &>/dev/null; then
  skip "bun $(bun --version)"
else
  echo "   Đang cài..."
  curl -fsSL https://bun.sh/install | bash
  export PATH="$HOME/.bun/bin:$PATH"
  echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc
  echo -e "   ${GREEN}✓${NC} bun $(bun --version)"
fi

# ─── 2. Agent Browser (cho Vieclam24h + portal SPA) ────────
banner "🌐 Agent Browser — Chromium cho SPA"
if command -v agent-browser &>/dev/null; then
  skip "agent-browser đã có"
else
  echo "   Đang cài..."
  npm i -g agent-browser 2>/dev/null
  agent-browser install --with-deps 2>/dev/null || agent-browser install
  echo -e "   ${GREEN}✓${NC} agent-browser installed"
fi

# ─── 3. Freehire CLI (global job aggregator) ────────────────
banner "🌍 Freehire CLI — Global job search"
if command -v freehire &>/dev/null; then
  skip "freehire $(freehire --version 2>/dev/null || echo 'ok')"
else
  echo "   Đang cài..."
  mkdir -p ~/.local/bin
  case "$OS" in
    linux)
      curl -fsSL "https://github.com/strelov1/freehire-cli/releases/latest/download/freehire_linux_amd64" -o ~/.local/bin/freehire
      ;;
    macos)
      curl -fsSL "https://github.com/strelov1/freehire-cli/releases/latest/download/freehire_darwin_$(uname -m)" -o ~/.local/bin/freehire
      ;;
  esac
  chmod +x ~/.local/bin/freehire
  export PATH="$HOME/.local/bin:$PATH"
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  echo -e "   ${GREEN}✓${NC} freehire installed"

  echo ""
  echo -e "   ${YELLOW}⚠${NC}  Freehire cần API key (miễn phí):"
  echo "      1. Vào https://freehire.dev → Account → API Keys"
  echo "      2. Chạy: freehire auth login --token <key>"
  echo "      (hoặc export FREEHIRE_TOKEN=<key>)"
fi

# ─── 4. Cài đặt dependencies cho các skill ──────────────────
banner "📦 Cài đặt skill dependencies"

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "   Repo: $REPO_DIR"

# ITviec
if [ -f "$REPO_DIR/.agents/skills/itviec-search/cli/package.json" ]; then
  echo "   ITviec..."
  cd "$REPO_DIR/.agents/skills/itviec-search/cli" && bun install --silent 2>/dev/null || true
  cd "$REPO_DIR"
fi

# LinkedIn
if [ -f "$REPO_DIR/.agents/skills/linkedin-search/cli/package.json" ]; then
  echo "   LinkedIn..."
  cd "$REPO_DIR/.agents/skills/linkedin-search/cli" && bun install --silent 2>/dev/null || true
  cd "$REPO_DIR"
fi

# ─── 5. Kiểm tra tổng kết ───────────────────────────────────
banner "✅ Kiểm tra hoàn tất"

echo ""
echo -e "   ${BOLD}Portals sẵn sàng:${NC}"
echo "   ┌──────────────┬──────────────────────────────────────┐"
echo "   │ ITviec       │ bun run ... search -q \"AI Engineer\" │"
echo "   │ LinkedIn VN  │ bun run ... search -l \"Ho Chi Minh\" │"
echo "   │ Vieclam24h   │ bash scripts/search.sh \"query\"      │"
echo "   │ Freehire     │ freehire search \"query\" --country vn│"
echo "   └──────────────┴──────────────────────────────────────┘"

echo ""
echo -e "   ${BOLD}Tìm nhanh:${NC}"
echo "     cd $REPO_DIR && bash scripts/vn-laptop/search-all.sh \"AI Engineer\""
echo ""
echo -e "   ${GREEN}${BOLD}✓ Setup hoàn tất!${NC} Bắt đầu tìm việc thôi 🚀"
