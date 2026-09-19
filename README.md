# X to Threads Bot

自動讀取指定 X 帳號的最新貼文，篩選財經／科技題材、翻成繁體中文，並發布到 Threads。

## 排程

GitHub Actions 會在每天台灣時間 06:00 與 17:00 執行；你也可在 Actions 頁面手動執行。每次最多發布一個新串文，成功後會將來源貼文 ID 存入 `seen_tweets.json`，避免重複發文。

## 第一次設定

在 GitHub 儲存庫的 **Settings → Secrets and variables → Actions** 新增以下 repository secrets：

| Secret | 用途 |
| --- | --- |
| `RAPIDAPI_KEY` | RapidAPI 的 X 資料 API 金鑰 |
| `RAPIDAPI_HOST` | API 主機名稱，預設 `twitter-api45.p.rapidapi.com` |
| `THREADS_ACCESS_TOKEN` | Threads API 的有效 access token |
| `THREADS_USER_ID` | Threads 的數字使用者 ID |
| `TARGET_TWITTER_USERNAME` | 要追蹤的 X 帳號，逗號分隔，例如 `jukan05,aleabitoreddit` |
| `GEMINI_API_KEY` | 選填，用於自然的繁中翻譯 |

設定後，從 **Actions → X to Threads Bot Scheduled Run → Run workflow** 手動跑一次。日誌出現 `✅ 發佈成功！Threads Post ID:` 才代表真的已發到 Threads。

## 維護提醒

- Threads token 到期時更新 `THREADS_ACCESS_TOKEN`。
- X 與 Threads 的 API 規範、速率限制與授權由各平台控制；請確認可轉載目標內容，並保留來源歸屬。
- GitHub 的排程可能延遲，因此不適合需要精確到分鐘的發文。
