---
name: itviec-search
version: 1.0.0
description: >
  Tìm kiếm việc làm IT tại Việt Nam trên ITviec.com — trang tuyển dụng IT
  hàng đầu Việt Nam. Dùng khi người dùng muốn tìm việc IT, lập trình,
  AI/ML, DevOps tại Việt Nam. Trigger phrases: tìm việc IT, itviec,
  việc làm IT Việt Nam, IT jobs Vietnam, tuyển dụng IT, tìm job IT,
  "có job nào ở", việc làm AI, việc làm lập trình.
context: fork
allowed-tools: Bash(bun run .agents/skills/itviec-search/cli/src/cli.ts *)
---

# ITviec Search Skill

Tìm kiếm việc làm IT trực tiếp từ [ITviec.com](https://itviec.com) — trang tuyển dụng
IT chuyên biệt lớn nhất Việt Nam với 28,000+ reviews công ty và báo cáo lương IT.

> ⚠️ **Yêu cầu IP Việt Nam.** ITviec dùng Cloudflare WAF chặn truy cập từ IP nước ngoài.
> Skill này chỉ hoạt động khi chạy từ máy có IP Việt Nam (hoặc qua VPN/proxy VN).

## ⚠️ Personal use only

Dữ liệu từ trang public của ITviec. Tự động truy cập có thể vi phạm điều khoản
sử dụng. **Giữ volume thấp, không dùng cho mục đích thương mại hoặc thu thập
dữ liệu hàng loạt.** Chạy với trách nhiệm của bạn.

## When to use this skill

- Tìm việc IT tại Việt Nam (HCMC, Hanoi, Da Nang...)
- Lọc theo level (Fresher, Junior, Middle, Senior)
- Lọc theo working model (Remote, Hybrid, On-site)
- Lọc theo mức lương
- Xem chi tiết một job posting cụ thể

## Commands

### Search job listings

```bash
bun run .agents/skills/itviec-search/cli/src/cli.ts search --query "AI Engineer" [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — từ khóa tìm kiếm (title, skill). **Required.**
- `--location <text>` / `-l <text>` — thành phố: "Ho Chi Minh", "Ha Noi", "Da Nang"
- `--page <n>` — số trang (1-indexed, ~20 results per page)
- `--limit <n>` / `-n <n>` — giới hạn tổng kết quả (client-side)
- `--format json|table|plain` — default `json`

### Fetch full job detail

```bash
bun run .agents/skills/itviec-search/cli/src/cli.ts detail <id|url> [--format json|plain]
```

## Usage examples

```bash
# AI Engineer jobs, Ho Chi Minh
bun run .agents/skills/itviec-search/cli/src/cli.ts search -q "AI Engineer" -l "Ho Chi Minh" --format table

# Python jobs nationwide
bun run .agents/skills/itviec-search/cli/src/cli.ts search -q "Python" --format table

# Full details for a specific job
bun run .agents/skills/itviec-search/cli/src/cli.ts detail 12345 --format plain
```

## Output formats

| Format | Best for |
|--------|----------|
| `json` | Default — programmatic use, passing IDs to `detail` |
| `table` | Quick human-readable scanning |
| `plain` | Reading a single job's full detail (`detail` command) |

All errors are written to **stderr** as `{ "error": "...", "code": "..." }` and the process exits with code `1`.

## Notes

- ITviec là SPA React — data được render server-side trong HTML gốc
- Mỗi trang ~20 kết quả
- API v1 (`api/v1/jobs`) cần authentication, skill này scrape HTML
- Job ID được extract từ URL chi tiết: `https://itviec.com/jobs/<id>`
- Cloudflare WAF — chỉ hoạt động từ IP Việt Nam
