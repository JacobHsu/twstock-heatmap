# 台股熱力圖 AI 分析工具

> 自動擷取台股熱力圖並使用 AI 分析跌幅排行，生成結構化 JSON API

[![GitHub Actions](https://img.shields.io/badge/automation-GitHub%20Actions-blue)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎯 專案簡介

本工具結合 **Playwright 網頁自動化** 與 **GPT-4o Vision AI**，自動擷取 [nStock.tw](https://www.nstock.tw/market_index/heatmap) 台股熱力圖，並智能識別跌幅最大的股票，輸出包含**股票代號**的結構化 API。

### 核心功能

- 🖼️ **自動截圖**：無頭瀏覽器擷取高解析度熱力圖
- 🤖 **AI 視覺分析**：GPT-4o 識別深綠色區塊（跌幅股）
- � **股票代號映射**：自動從 1,971 筆資料庫查找 ticker
- 📡 **JSON API**：輸出標準化資料供其他應用使用
- ⏰ **自動排程**：GitHub Actions 每日開盤後更新

---

## 🚀 快速開始

### 線上 API（無需安裝）

直接使用已部署的 API：

```bash
curl https://jacobhsu.github.io/twstock-heatmap/api/twstock_top_losers.json
```

**API 回應範例**：
```json
{
  "status": "success",
  "data": {
    "all": [
      {
        "ticker": "8086",
        "name": "宏捷科",
        "change": "-3.97%"
      }
    ]
  }
}
```

📌 [查看完整 API 文件](api/README.md) | [線上展示頁面](https://jacobhsu.github.io/twstock-heatmap/api/twstock_example.html)

---

## 💻 本地安裝

### 前置需求

- Python 3.8+
- Git

### 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/JacobHsu/twstock-heatmap.git
cd twstock-heatmap

# 2. 安裝依賴
pip install playwright Pillow requests
playwright install chromium

# 3. 設定環境變數
cp .env.example .env
# 編輯 .env，填入你的 GITHUB_TOKEN
```

> 💡 **取得 GitHub Token**：前往 [GitHub Settings → Tokens](https://github.com/settings/tokens)，勾選 `read:user` 權限

---

## 📖 使用方式

### 完整流程（本地端執行）

**步驟 1：擷取所有熱力圖**
```bash
python skills/twstock-heatmap/scripts/capture_twstock.py
```

這會自動擷取所有 8 個類別並儲存到 `heatmaps/` 資料夾：
- 📈 TSE Overview (上市總覽)
- 📊 OTC Overview (上櫃總覽)
- 🔌 OTC Electronic (櫃買電子)
- 💎 OTC Semiconductor (櫃買半導體)
- 🏗️ OTC Construction (櫃買營建)
- 🌱 TSE Green Energy (上市綠能環保)
- ✈️ OTC Tourism (上櫃觀光)
- ♻️ OTC Green Energy (上櫃綠能環保)

**執行結果**：
```
📊 Capturing all 8 heatmap categories...
Output directory: D:\15-stock\twstock-heatmap\heatmaps

============================================================
[1/8] Capturing: tse
============================================================
...
✅ Successfully captured tse

============================================================
📊 SUMMARY
============================================================
✅ Successful: 8/8
⏱️  Total time: 3m 25s

🎉 All heatmaps captured successfully!
```

**步驟 2：AI 分析生成 API**
```bash
python skills/twstock-heatmap/scripts/analyze_twstock.py --auto
```

使用 `--auto` 模式會自動掃描 `heatmaps/` 資料夾並分析所有 PNG：

```
🔍 Auto-scanning heatmaps directory...
Found 8 heatmap(s):
  - tse: twstock.png
  - otc: twstock_otc.png
  - otc-elec: twstock_otc-elec.png
  ...

Analyzing tse from heatmaps/twstock.png...
✓ Loaded 1,971 stock mappings from StockMapping.csv
...

JSON API saved: api/twstock_top_losers.json
Analysis complete!
```

**輸出檔案**：
- `heatmaps/*.png` - 8 個熱力圖截圖
- `api/twstock_top_losers.json` - 包含所有類別的 JSON API
- `index.html` - 本地檢視器

---

### 進階用法

**只擷取特定類別**：
```bash
# 只擷取上市總覽
python skills/twstock-heatmap/scripts/capture_twstock.py -t tse

# 只擷取上櫃總覽
python skills/twstock-heatmap/scripts/capture_twstock.py -t otc

# 只擷取特定產業
python skills/twstock-heatmap/scripts/capture_twstock.py -t tse-green
```

**手動指定要分析的檔案**：
```bash
python skills/twstock-heatmap/scripts/analyze_twstock.py \
  -i tse:heatmaps/twstock.png \
     otc:heatmaps/twstock_otc.png
```

**自訂輸出路徑**：
```bash
python skills/twstock-heatmap/scripts/analyze_twstock.py \
  --auto \
  -o custom/output.json
```

---

## 🏗️ 專案架構

```
twstock-heatmap/
├── skills/twstock-heatmap/scripts/
│   ├── capture_twstock.py      # 截圖腳本
│   └── analyze_twstock.py      # AI 分析腳本
├── data/
│   └── StockMapping.csv        # 股票代號資料庫 (1,971 筆)
├── api/
│   ├── twstock_top_losers.json # 生成的 API 檔案
│   └── twstock_example.html    # API 展示頁面
└── .github/workflows/
    └── generate-twstock-map.yml # 自動化排程
```

---

## 🔧 技術細節

### 截圖流程

1. Playwright 啟動 Chromium 無頭瀏覽器
2. 導航至 nStock.tw 熱力圖頁面
3. 等待 Nuxt.js 完全渲染（~20 秒）
4. 定位 Canvas 元素並擷取截圖

### AI 分析流程

1. 將圖片編碼為 Base64
2. 呼叫 GitHub Models API (GPT-4o Vision)
3. AI 識別深綠色方塊（跌幅股）並排序
4. 從 `StockMapping.csv` 查找股票代號
5. 輸出結構化 JSON（ticker 在第一位置）

### 股票代號映射

- **資料來源**：`data/StockMapping.csv`（1,971 筆上市櫃股票）
- **查找方式**：公司名稱 → 股票代號（O(1) 字典查找）
- **容錯機制**：找不到代號時顯示警告但不中斷執行

---

## 🤖 自動化部署

### GitHub Actions 設定

專案已配置自動化工作流程，每個交易日台灣時間 09:30 自動執行：

1. 擷取最新熱力圖
2. AI 分析生成 API
3. 部署到 GitHub Pages

**手動觸發**：前往 Actions 標籤 → Run workflow

---

## 📊 API 規格

### 端點

```
GET https://jacobhsu.github.io/twstock-heatmap/api/twstock_top_losers.json
```

### 回應格式

```json
{
  "status": "success",
  "data": {
    "all": [
      {
        "ticker": "8086",      // 股票代號（第一位置）
        "name": "宏捷科",       // 公司名稱
        "change": "-3.97%"     // 漲跌幅
      }
    ]
  },
  "version": "2.0",
  "market": "taiwan",
  "source": "nstock.tw",
  "last_updated": "2026-01-14T08:47:12Z"
}
```

### 整合範例

**JavaScript**
```javascript
fetch('https://jacobhsu.github.io/twstock-heatmap/api/twstock_top_losers.json')
  .then(res => res.json())
  .then(data => {
    data.data.all.forEach(stock => {
      console.log(`${stock.ticker} ${stock.name}: ${stock.change}`);
    });
  });
```

**Python**
```python
import requests

r = requests.get('https://jacobhsu.github.io/twstock-heatmap/api/twstock_top_losers.json')
for stock in r.json()['data']['all']:
    print(f"{stock['ticker']} {stock['name']}: {stock['change']}")
```

---

## 🛠️ 故障排除

### 截圖失敗

**問題**：`Failed to capture screenshot`

**解決**：
```bash
# 確認 Playwright 已安裝
playwright install chromium

# 使用可見模式除錯
python skills/twstock-heatmap/scripts/capture_twstock.py --no-headless
```

### AI 分析失敗

**問題**：`Error: GitHub token required`

**解決**：
1. 確認 `.env` 檔案存在且包含 `GITHUB_TOKEN`
2. 檢查 Token 權限（需要 `read:user`）
3. 確認 GitHub Models API 額度未超限

### 找不到股票代號

**問題**：`⚠ No ticker found for: 某公司`

**原因**：
- AI 識別的名稱與 CSV 不完全匹配
- 新上市股票尚未加入資料庫

**解決**：手動更新 `data/StockMapping.csv`

---

## 🌟 進階功能

### Claude Code 整合

本工具支援作為 MCP Skill 使用：

```bash
# 在 Claude Code 中載入
/skill add skills/twstock-heatmap/SKILL.md

# 自然語言操作
"幫我抓取現在的台股熱力圖並分析跌幅排行"
```

---

## 📝 授權與聲明

- **授權**：MIT License
- **資料來源**：[nStock.tw](https://www.nstock.tw)
- **用途**：僅供教育與個人使用，請遵守資料來源的服務條款

---

## 🔗 相關連結

- [GitHub Models API 文件](https://docs.github.com/en/github-models)
- [Playwright Python 文件](https://playwright.dev/python/)
- [nStock 台股熱力圖](https://www.nstock.tw/market_index/heatmap)

---

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！
