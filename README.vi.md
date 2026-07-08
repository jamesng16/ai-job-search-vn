<p align="center">
  <img src="claude_animation.gif" alt="AI Job Search Assistant" width="200">
</p>

# AI Job Search — Trợ lý tìm việc bằng AI

[![CI](https://github.com/MadsLorentzen/ai-job-search/actions/workflows/ci.yml/badge.svg)](https://github.com/MadsLorentzen/ai-job-search/actions/workflows/ci.yml)
[![EN](https://img.shields.io/badge/README-English-blue)](README.md)
[![Fork VN](https://img.shields.io/badge/Fork-Vietnam-brightgreen)](https://github.com/jamesng16/ai-job-search-vn)

Framework tìm việc tự động dùng AI, chạy trên [Claude Code](https://claude.com/claude-code).
Fork về, điền hồ sơ của bạn, và để Claude đánh giá job posting, chỉnh sửa CV,
viết cover letter, và chuẩn bị phỏng vấn cho bạn.

> Ghi chú: Đây là dự án mã nguồn mở độc lập, không liên kết với Anthropic.

---

## 🇻🇳 Dành cho người Việt

Fork này được tùy chỉnh cho thị trường việc làm Việt Nam:

| Portal | Trạng thái | Ghi chú |
|--------|-----------|--------|
| **ITviec** | ✅ Hoạt động | `bun run ... search -q "AI Engineer"` |
| **LinkedIn VN** | ✅ Có sẵn | `--location "Ho Chi Minh City, Vietnam"` |
| **TopCV** | ❌ Bị chặn | Cloudflare WAF |
| **VietnamWorks** | ❌ SPA | Cần browser automation |

### 🚀 Bắt đầu nhanh (từ máy tính ở Việt Nam)

```bash
# Clone fork
git clone https://github.com/jamesng16/ai-job-search-vn.git
cd ai-job-search-vn

# Cài đặt
cd .agents/skills/itviec-search/cli && bun install && cd ../../..

# Tìm việc ITviec
bun run .agents/skills/itviec-search/cli/src/cli.ts search -q "AI Engineer" -l "Ho Chi Minh" --format table

# Tìm việc LinkedIn VN
bun run .agents/skills/linkedin-search/cli/src/cli.ts search \
  -q "AI Engineer" -l "Ho Chi Minh City, Vietnam" --format table
```

---

## 🎯 Tính năng chính

1. **Đánh giá mức độ phù hợp** — So sánh JD với hồ sơ của bạn (kỹ năng, kinh nghiệm, behavioral)
2. **Tùy chỉnh CV** — Chỉnh sửa CV LaTeX cho từng vị trí cụ thể
3. **Viết Cover Letter** — Tạo cover letter nhắm đúng vai trò
4. **Chuẩn bị phỏng vấn** — Câu hỏi, câu trả lời mẫu, talking points
5. **Chiến lược nghề nghiệp** — Tư vấn định vị bản thân

## 📁 Cấu trúc thư mục

```
├── cv/                    # CV LaTeX (moderncv)
├── cover_letters/         # Cover letter LaTeX (cover.cls)
├── .agents/skills/        # Job search CLI tools
│   ├── itviec-search/     # 🇻🇳 ITviec portal
│   ├── linkedin-search/   # LinkedIn toàn cầu
│   └── ...                # Các portal khác
├── .claude/skills/        # AI skills cho workflow
├── scripts/vn-laptop/     # Script chạy từ laptop VN
└── CLAUDE.md              # Hồ sơ ứng viên của bạn
```

## 🔄 Workflow cho mỗi job mới

1. Bạn gửi JD (link hoặc text)
2. Claude **đánh giá mức độ phù hợp**: skills match, experience match, culture match
3. Nếu phù hợp: tạo CV (`cv/main_<cty>.tex`) và cover letter (`cover_letters/cover_<cty>_<role>.tex`)
4. **Kiểm tra** cả 2 tài liệu (factual accuracy, targeting, consistency, quality)
5. Chuẩn bị talking points phỏng vấn

## 📋 Hồ sơ ứng viên

Điền thông tin của bạn vào `CLAUDE.md`:
- Thông tin cá nhân (tên, vị trí, location)
- Học vấn
- Kinh nghiệm làm việc
- Kỹ năng kỹ thuật
- Chứng chỉ, giải thưởng
- Behavioral profile
- Mục tiêu nghề nghiệp

Sau đó chạy `/setup` để Claude tự động populate hồ sơ.

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
