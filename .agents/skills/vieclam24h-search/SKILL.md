---
name: vieclam24h-search
version: 1.0.0
description: >
  Tìm việc làm IT trên Vieclam24h.vn — cổng tuyển dụng đa ngành phổ biến
  tại Việt Nam. Dùng agent-browser để tương tác với trang SPA. Trigger phrases:
  vieclam24h, việc làm 24h, tìm việc 24h, "job trên vieclam24h".
context: fork
allowed-tools: Bash(agent-browser:*)
---

# Vieclam24h Search Skill

Tìm việc làm trên [Vieclam24h.vn](https://vieclam24h.vn) — một trong những cổng
tuyển dụng lớn nhất Việt Nam. Trang sử dụng SPA (Single Page Application) nên
cần **agent-browser** để tương tác và trích xuất dữ liệu.

> ⚠️ **Yêu cầu:** `agent-browser` đã cài đặt (`npm i -g agent-browser && agent-browser install`)

## Commands

### Search job listings

```bash
bash .agents/skills/vieclam24h-search/scripts/search.sh "AI Engineer" [--limit 5]
```

## How it works

1. Mở trang tìm kiếm bằng agent-browser (Chromium thật)
2. Điền từ khóa vào ô search
3. Submit form
4. Đợi kết quả load (SPA render)
5. Trích xuất job cards từ DOM

## Notes

- Vieclam24h là SPA — không scrape được bằng curl/fetch thông thường
- Cần agent-browser chạy Chromium thật để render JavaScript
- Kết quả trả về dạng text table
- Mỗi lần search mất ~5-10 giây do cần load browser + render
