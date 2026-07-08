<p align="center">
  <img src="claude_animation.gif" alt="AI Job Search Assistant" width="200">
</p>

# AI Job Search — Trợ lý tìm việc bằng AI 🇻🇳

[![CI](https://github.com/MadsLorentzen/ai-job-search/actions/workflows/ci.yml/badge.svg)](https://github.com/MadsLorentzen/ai-job-search/actions/workflows/ci.yml)
[![EN](https://img.shields.io/badge/📖_README-English-blue)](README.en.md)
[![PR](https://img.shields.io/badge/PR-Upstream_%2383-green)](https://github.com/MadsLorentzen/ai-job-search/pull/83)

Framework tìm việc tự động dùng AI, chạy trên [Claude Code](https://claude.com/claude-code).
Fork về, điền hồ sơ, để Claude đánh giá JD, chỉnh CV, viết cover letter, chuẩn bị phỏng vấn.

> Ghi chú: Dự án mã nguồn mở độc lập, không liên kết với Anthropic.
> Fork từ [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search).

---

## 🇻🇳 Portal tuyển dụng IT Việt Nam

| Portal | Trạng thái | Cách dùng |
|--------|-----------|----------|
| **ITviec** | ✅ Hoạt động | `bun run ... search -q "AI Engineer" --format table` |
| **LinkedIn VN** | ✅ Có sẵn | `--location "Ho Chi Minh City, Vietnam"` |
| **Vieclam24h** | ✅ Hoạt động | `bash scripts/search.sh "AI Engineer"` (cần agent-browser) |
| **Freehire** | ✅ Hoạt động | `freehire search "AI Engineer" --country vn` (cần API key miễn phí) |
| **TopCV** | ❌ Bị chặn | Cloudflare WAF |
| **VietnamWorks** | ❌ SPA | Cần browser automation |

### 🚀 Bắt đầu nhanh

```bash
# Clone fork
git clone https://github.com/jamesng16/ai-job-search-vn.git
cd ai-job-search-vn

# ITviec — cần bun
cd .agents/skills/itviec-search/cli && bun install && cd ../../..
bun run .agents/skills/itviec-search/cli/src/cli.ts search -q "AI Engineer" -l "Ho Chi Minh" --format table

# LinkedIn VN
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "AI Engineer" -l "Ho Chi Minh City, Vietnam" --format table

# Vieclam24h — cần agent-browser
bash .agents/skills/vieclam24h-search/scripts/search.sh "AI Engineer"

# Freehire — cần API key (miễn phí tại freehire.dev)
freehire search "AI Engineer" --country vn --json
```

---

## 🎯 Tính năng chính

1. **Đánh giá mức độ phù hợp** — So sánh JD với hồ sơ (kỹ năng, kinh nghiệm, behavioral)
2. **Tùy chỉnh CV** — Chỉnh sửa CV LaTeX cho từng vị trí
3. **Viết Cover Letter** — Tạo cover letter nhắm đúng vai trò
4. **Chuẩn bị phỏng vấn** — Câu hỏi, câu trả lời mẫu, talking points
5. **Chiến lược nghề nghiệp** — Tư vấn định vị bản thân

## 📁 Cấu trúc thư mục

```
├── cv/                    # CV LaTeX (moderncv)
├── cover_letters/         # Cover letter LaTeX (cover.cls)
├── .agents/skills/        # Job search CLI tools
│   ├── itviec-search/     # 🇻🇳 ITviec portal
│   ├── vieclam24h-search/ # 🇻🇳 Vieclam24h portal
│   ├── freehire-search/   # 🌍 Global aggregator
│   ├── linkedin-search/   # LinkedIn toàn cầu
│   └── ...
├── .claude/skills/        # AI skills cho workflow
├── scripts/vn-laptop/     # Script chạy từ laptop VN
└── CLAUDE.md              # Hồ sơ ứng viên của bạn
```

## 🔄 Workflow cho mỗi job

1. Gửi JD (link hoặc text)
2. Claude **đánh giá mức độ phù hợp**: skills, experience, culture match
3. Nếu OK → tạo CV (`cv/main_<cty>.tex`) + cover letter
4. **Kiểm tra** tài liệu (factual, targeting, consistency, quality)
5. Chuẩn bị talking points phỏng vấn

## 📋 Hồ sơ ứng viên

Điền thông tin vào `CLAUDE.md`: thông tin cá nhân, học vấn, kinh nghiệm, kỹ năng, chứng chỉ, giải thưởng, behavioral profile, mục tiêu nghề nghiệp. Sau đó chạy `/setup`.

---

<p align="center">
  <i>Tiết kiệm được một ngày Chủ nhật viết cover letter? Mời một ly cà phê.<br>
  Kiếm được job nhờ nó? Chắc là hai ly.</i> ☕
</p>

<p align="center">
  <a href="https://ko-fi.com/madslorentzen">
    <img src="https://storage.ko-fi.com/cdn/kofi3.png?v=6" alt="Buy me a coffee at ko-fi.com" height="40">
  </a>
</p>
