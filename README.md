# CT8 注册队列监控

监控 [CT8 注册队列](https://ct8.00666.xyz) 状态，有位置时自动注册并 Telegram 通知。

## 功能

- ⏱ 每 30 分钟自动检查队列状态
- 📧 有位置时自动注册配置的邮箱
- 🔔 通过 Telegram 发送通知
- ♻️ 自动追踪已注册邮箱，避免重复提交

## 配置 Secrets

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret | 说明 | 示例 |
|--------|------|------|
| `CT8_EMAILS` | 要注册的邮箱，逗号分隔 | `ohjustb@outlook.com,hubtpp@gmail.com` |
| `TG_BOT_TOKEN` | Telegram Bot Token | `123456:ABC-DEF...` |
| `TG_CHAT_ID` | Telegram Chat ID | `644320820` |

## 手动触发

Actions 页面 → 选择 `CT8 注册队列监控` → `Run workflow` → 可选 `force_notify`
