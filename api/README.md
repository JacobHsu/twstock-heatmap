# 台股市場資料 API

自動化的台灣股票市場資料 API，使用 GitHub Actions + GitHub Models 每日更新跌幅最大的五檔股票。

---

## 🚀 快速開始

### API 端點

**完整版本 (含元資料):**
```
https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers.json
```

**簡化版本 (僅資料):**
```
https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers_simple.json
```

### 回應格式

**完整版回應** (`twstock_top_losers.json`):
```json
{
  "status": "success",
  "data": {
    "top_losers": [
      {"name": "群聯", "change": "-3.25%"},
      {"name": "信驊", "change": "-2.80%"},
      {"name": "環球晶", "change": "-2.15%"},
      {"name": "旺矽", "change": "-1.92%"},
      {"name": "元太", "change": "-1.58%"}
    ],
    "generated_at": "2026-01-14T01:30:00Z",
    "source": "nstock",
    "market": "taiwan"
  },
  "version": "1.0",
  "market": "taiwan",
  "source": "nstock.tw",
  "last_updated": "2026-01-14T01:30:00Z"
}
```

**簡化版回應** (`twstock_top_losers_simple.json`):
```json
{
  "top_losers": [
    {"name": "群聯", "change": "-3.25%"},
    {"name": "信驊", "change": "-2.80%"},
    {"name": "環球晶", "change": "-2.15%"},
    {"name": "旺矽", "change": "-1.92%"},
    {"name": "元太", "change": "-1.58%"}
  ],
  "generated_at": "2026-01-14T01:30:00Z",
  "source": "nstock",
  "market": "taiwan"
}
```

---

## 📖 使用範例

### JavaScript (Fetch API)

```javascript
// 獲取跌幅最大的股票
fetch('https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers.json')
  .then(response => response.json())
  .then(data => {
    console.log('台股跌幅排行:', data.data.top_losers);
    data.data.top_losers.forEach((stock, i) => {
      console.log(`${i + 1}. ${stock.name}: ${stock.change}`);
    });
  })
  .catch(error => console.error('Error:', error));
```

### Python (requests)

```python
import requests

# 獲取資料
response = requests.get('https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers.json')
data = response.json()

# 列印結果
print("台股跌幅排行：")
for i, stock in enumerate(data['data']['top_losers'], 1):
    print(f"{i}. {stock['name']}: {stock['change']}")
```

### cURL

```bash
# 獲取完整資料
curl https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers.json

# 獲取簡化資料
curl https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers_simple.json

# 格式化輸出 (使用 jq)
curl -s https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers.json | jq '.data.top_losers'
```

### React 範例

```jsx
import React, { useState, useEffect } from 'react';

function TaiwanTopLosers() {
  const [losers, setLosers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('https://{username}.github.io/twstock-heatmap/api/twstock_top_losers.json')
      .then(res => res.json())
      .then(data => {
        setLosers(data.data.top_losers);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>載入中...</div>;

  return (
    <div>
      <h2>台股今日跌幅最大</h2>
      <ul>
        {losers.map((stock, i) => (
          <li key={i}>{stock.name}: {stock.change}</li>
        ))}
      </ul>
    </div>
  );
}

export default TaiwanTopLosers;
```

### Vue 3 範例

```vue
<template>
  <div>
    <h2>台股今日跌幅最大</h2>
    <ul v-if="!loading">
      <li v-for="(stock, i) in losers" :key="i">
        {{ stock.name }}: {{ stock.change }}
      </li>
    </ul>
    <p v-else>載入中...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const losers = ref([]);
const loading = ref(true);

onMounted(async () => {
  const res = await fetch('https://{username}.github.io/twstock-heatmap/api/twstock_top_losers.json');
  const data = await res.json();
  losers.value = data.data.top_losers;
  loading.value = false;
});
</script>
```

---

## ⚙️ 設定指南

### 步驟 1: 啟用 GitHub Pages

1. 進入你的 GitHub 儲存庫
2. 點擊 **Settings** → **Pages**
3. Source 選擇 `gh-pages` 分支
4. 點擊 **Save**

📍 你的 API 將部署到: `https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers.json`

### 步驟 2: 啟用 GitHub Actions

1. 進入 **Actions** 標籤
2. 點擊 **"I understand my workflows, go ahead and enable them"**
3. 確認工作流已啟用

### 步驟 3: 手動觸發首次運行

1. **Actions** → 選擇 **"Generate Taiwan Stock Heatmap"**
2. 點擊 **"Run workflow"**
3. 選擇 `main` 分支
4. 點擊綠色的 **"Run workflow"** 按鈕

⏱️ 等待約 2-3 分鐘，工作流會自動完成：
- ✅ 截取台股熱力圖
- ✅ AI 分析圖片
- ✅ 生成 JSON API
- ✅ 部署到 GitHub Pages

### 步驟 4: 驗證設定

訪問你的 API 端點：
```
https://{your-username}.github.io/twstock-heatmap/api/twstock_top_losers.json
```

你應該看到 JSON 回應。同時可以訪問線上範例：
```
https://{your-username}.github.io/twstock-heatmap/api/twstock_example.html
```

---

## 🔄 工作原理

### 自動化流程

```
每個交易日台灣時間 09:30 AM (開盤後 30 分鐘)
              ↓
      1. 截取 nStock 熱力圖
              ↓
        生成 twstock.png
              ↓
      2. AI 分析圖片
         (GitHub Models API - GPT-4o Vision)
              ↓
      3. 識別跌幅最大的 5 檔股票
              ↓
      4. 生成 JSON API 檔案
              ↓
      5. 部署到 GitHub Pages
              ↓
      公開 API 端點可訪問
```

### 技術架構

- **截圖**: Playwright + Chromium
- **AI 分析**: GitHub Models API (GPT-4o with Vision)
- **自動化**: GitHub Actions
- **託管**: GitHub Pages
- **更新頻率**: 每個交易日開盤後自動更新

---

## 📊 API 規格

### 欄位說明

| 欄位 | 類型 | 說明 |
|------|------|------|
| `name` | string | 公司名稱 (如 "台積電", "鴻海") |
| `ticker` | string | 股票代碼 (如 "2330")，若有顯示 |
| `change` | string | 漲跌幅百分比 (如 "-2.50%") |
| `generated_at` | string | 資料生成時間 (ISO 8601 格式) |
| `source` | string | 資料來源 ("nstock") |
| `market` | string | 市場 ("taiwan") |
| `status` | string | API 狀態 ("success" 或 "error") |
| `version` | string | API 版本號 |

### 更新時間

- **自動更新**: 每個交易日台灣時間 09:30 AM
- **手動觸發**: 可在 GitHub Actions 中手動觸發工作流
- **更新延遲**: 開盤後約 2-3 分鐘
- **交易日**: 僅在台股交易日更新 (週一至週五，排除國定假日)

### 台股交易時間

| 項目 | 時間 (UTC+8) |
|------|-------------|
| 開盤 | 09:00 AM |
| 收盤 | 13:30 PM |
| API 更新 | 09:30 AM |

### CORS 支援

GitHub Pages 預設支援 CORS，可直接從瀏覽器客戶端呼叫此 API。

### 限制說明

- 🔄 **資料時效**: 資料代表截圖時刻的市場狀態
- 🎯 **準確性**: AI 識別準確率約 95%+ (可能有個別誤差)
- 📡 **呼叫限制**: GitHub Pages 靜態檔案無呼叫次數限制
- 🎨 **顏色慣例**: 台股紅漲綠跌（與美股相反）

---

## 🛠️ 進階設定

### 修改更新頻率

編輯 `.github/workflows/generate-twstock-map.yml`:

```yaml
on:
  schedule:
    # 預設: 台灣時間 09:30 AM (UTC 01:30 AM)
    - cron: '30 1 * * 1-5'

    # 其他選項:
    # - cron: '0 5 * * 1-5'   # 台灣 13:00 (收盤前)
    # - cron: '30 5 * * 1-5'  # 台灣 13:30 (收盤後)
```

### 自訂分析內容

編輯 `skills/twstock-heatmap/scripts/analyze_twstock.py` 的提示詞：

**範例: 分析漲幅最大的股票**

```python
prompt = """分析這張台股市場熱力圖截圖。

請找出漲幅最大的五檔股票（紅色方塊中漲幅數字最大的）。

要求：
1. 只返回 JSON 格式
2. JSON 格式如下：
{
  "top_gainers": [
    {"name": "公司名稱", "change": "漲幅百分比"},
    ...
  ],
  "generated_at": "ISO 時間戳記",
  "source": "nstock",
  "market": "taiwan"
}
"""
```

同時修改輸出檔案名稱:
```python
parser.add_argument(
    "-o", "--output",
    default="api/twstock_top_gainers.json",  # 改為 top_gainers
    help="輸出 JSON 路徑"
)
```

---

## 🔧 故障排除

### API 返回 404

**原因**:
- GitHub Pages 未啟用
- 分支選擇錯誤
- 工作流未成功運行

**解決方法**:
1. 確認 Settings → Pages → Source 設為 `gh-pages`
2. 檢查 `gh-pages` 分支是否存在
3. 查看 Actions 是否成功完成

### 工作流失敗

**原因**:
- nStock.tw 網站無法存取
- Playwright 瀏覽器安裝失敗
- API 呼叫失敗

**解決方法**:
1. 查看 Actions 日誌找到具體錯誤
2. 手動重新運行工作流
3. 檢查 GitHub Models API 額度

### JSON 資料不準確

**原因**:
- AI 識別錯誤
- 圖片品質問題
- 提示詞不夠清晰

**解決方法**:
1. 查看 Actions 日誌中的 API 回應
2. 下載 `twstock.png` 檢查圖片品質
3. 最佳化提示詞

### GitHub Models API 限制

**免費額度**:
- 每分鐘 15 次請求
- 每天 150 次請求
- 每月 1500 次請求

**超出限制時**:
- 減少工作流運行頻率
- 等待配額重置

---

## 📱 應用範例

### Discord 機器人

```python
import requests
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.command()
async def twstock(ctx):
    url = "https://{username}.github.io/twstock-heatmap/api/twstock_top_losers.json"
    data = requests.get(url).json()
    
    message = "📉 **台股今日跌幅排行**\n"
    for i, stock in enumerate(data['data']['top_losers'], 1):
        message += f"{i}. {stock['name']}: {stock['change']}\n"
    
    await ctx.send(message)
```

### Line Notify

```python
import requests

def send_line_notify(token):
    url = "https://{username}.github.io/twstock-heatmap/api/twstock_top_losers_simple.json"
    data = requests.get(url).json()
    
    message = "\n📉 台股跌幅排行\n"
    for i, stock in enumerate(data['top_losers'], 1):
        message += f"{i}. {stock['name']}: {stock['change']}\n"
    
    headers = {"Authorization": f"Bearer {token}"}
    requests.post(
        "https://notify-api.line.me/api/notify",
        headers=headers,
        data={"message": message}
    )
```

### Telegram Bot

```python
import requests
import telegram

def send_telegram(bot_token, chat_id):
    url = "https://{username}.github.io/twstock-heatmap/api/twstock_top_losers.json"
    data = requests.get(url).json()
    
    message = "📉 *台股今日跌幅排行*\n\n"
    for i, stock in enumerate(data['data']['top_losers'], 1):
        message += f"{i}\\. {stock['name']}: {stock['change']}\n"
    
    bot = telegram.Bot(token=bot_token)
    bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
```

---

## 📚 相關資源

- [nStock 熱力圖](https://www.nstock.tw/market_index/heatmap)
- [GitHub Models 文件](https://docs.github.com/en/github-models)
- [GitHub Actions 文件](https://docs.github.com/en/actions)
- [GitHub Pages 文件](https://docs.github.com/en/pages)
- [Playwright 文件](https://playwright.dev/python/)

---

## ⚠️ 免責聲明

**重要提示**:
- 此 API 僅供教育和研究目的
- 資料可能存在延遲或誤差
- 不構成投資建議
- 使用此資料進行投資決策需自行承擔風險
- 請遵守 nStock.tw 的服務條款

---

## 📄 授權

資料來自 [nStock.tw](https://www.nstock.tw)，僅供個人使用。
