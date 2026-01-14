---
name: twstock-heatmap
description: Capture Taiwan stock market heatmap screenshots from nStock.tw and analyze top losers. Use this skill when users ask for "Taiwan stock heatmap", "top losers in TW stock", or market visualization.
---

# Taiwan Stock Market Heatmap Skill

This skill allows you to capture real-time Taiwan stock market heatmaps and analyze them using AI.

## Capabilities

### 1. Capture Heatmap Screenshot
Use this command to capture the heatmap image.

**Command:**
```bash
# Capture default (Listed stocks)
python skills/twstock-heatmap/scripts/capture_twstock.py

# Capture OTC Electronic
python skills/twstock-heatmap/scripts/capture_twstock.py -t otc-elec

# Capture OTC Semiconductor
python skills/twstock-heatmap/scripts/capture_twstock.py -t otc-semi
```

### 2. Analyze Top Losers
Use this command to identify stocks with the biggest drop. (Requires `GITHUB_TOKEN`)

**Command:**
```bash
# Analyze captured image
python skills/twstock-heatmap/scripts/analyze_twstock.py -i all:twstock.png
```

## Usage Examples

**User:** "Show me the Taiwan stock heatmap."
**Agent:** Run `python skills/twstock-heatmap/scripts/capture_twstock.py`

**User:** "What are the top losers in OTC Electronic sector?"
**Agent:** 
1. Run `python skills/twstock-heatmap/scripts/capture_twstock.py -t otc-elec`
2. Run `python skills/twstock-heatmap/scripts/analyze_twstock.py -i otc-elec:twstock_otc-elec.png`

## Quick Start

The simplest way to capture the Taiwan stock heatmap:

```bash
python skills/twstock-heatmap/scripts/capture_twstock.py
```

This will:
1. Capture the current Taiwan stock market heatmap from nStock.tw
2. Save it as `twstock.png` in the project root directory
3. Create an `twstock_index.html` file to display the map

## Options

### Skip HTML Creation

Use `--no-html` to only save the PNG screenshot without creating an HTML file:

```bash
python skills/twstock-heatmap/scripts/capture_twstock.py --no-html
```

### Debug Mode (Visible Browser)

Use `--no-headless` to run with a visible browser window for debugging:

```bash
python skills/twstock-heatmap/scripts/capture_twstock.py --no-headless
```

## AI Analysis

After capturing the heatmap, you can analyze it to identify the top 5 losers:

```bash
python skills/twstock-heatmap/scripts/analyze_twstock.py
```

This requires a GitHub token (for GitHub Models API):
```bash
export GITHUB_TOKEN="your_github_token"
python skills/twstock-heatmap/scripts/analyze_twstock.py
```

Or pass it directly:
```bash
python skills/twstock-heatmap/scripts/analyze_twstock.py --token YOUR_TOKEN
```

## How It Works

### Screenshot Flow
1. Opens Chromium browser via Playwright
2. Navigates to nStock.tw heatmap page
3. Waits for the treemap to fully render (handles Nuxt.js SSR)
4. Locates and captures the heatmap section
5. Saves as high-resolution PNG

### AI Analysis Flow
1. Reads the captured heatmap screenshot (twstock.png)
2. Sends to GitHub Models API (GPT-4o with Vision)
3. AI identifies all stocks and their price changes
4. Extracts top 5 losers (biggest drops, most red)
5. Generates JSON API file

## Output Files

### PNG Screenshot
- **Location**: Project root directory
- **Filename**: `twstock.png`
- **Format**: High-resolution PNG
- **Color coding**: Green = gains, Red = losses

### HTML Viewer (optional)
- **File**: `twstock_index.html` in project root
- **Style**: Dark theme, responsive design
- **Content**: Displays the captured PNG

### JSON API (after analysis)
- **Location**: `api/` directory
- **Files**: 
  - `twstock_top_losers.json` (full version with metadata)
  - `twstock_top_losers_simple.json` (simplified version)

## API Response Format

### Full Version (`twstock_top_losers.json`)
```json
{
  "status": "success",
  "data": {
    "top_losers": [
      {"ticker": "2330", "name": "台積電", "change": "-2.50%"},
      {"ticker": "2317", "name": "鴻海", "change": "-1.80%"},
      {"ticker": "2454", "name": "聯發科", "change": "-1.50%"},
      {"ticker": "2308", "name": "台達電", "change": "-1.20%"},
      {"ticker": "2412", "name": "中華電", "change": "-0.90%"}
    ],
    "generated_at": "2026-01-14T06:00:00Z",
    "source": "nstock",
    "market": "taiwan"
  },
  "version": "1.0",
  "last_updated": "2026-01-14T06:00:00Z"
}
```

### Simple Version (`twstock_top_losers_simple.json`)
```json
{
  "top_losers": [
    {"ticker": "2330", "name": "台積電", "change": "-2.50%"},
    {"ticker": "2317", "name": "鴻海", "change": "-1.80%"}
  ],
  "generated_at": "2026-01-14T06:00:00Z",
  "source": "nstock",
  "market": "taiwan"
}
```

## Requirements

- **Playwright**: Automatically installed if not present
- **Pillow (PIL)**: Automatically installed if not present
- **requests**: For API calls (auto-installed)
- **Chrome/Chromium**: Required for browser automation

## Taiwan Stock Market Info

### Market Hours
- **Trading days**: Monday to Friday
- **Trading hours**: 9:00 AM - 1:30 PM (Taiwan Time, UTC+8)
- **Best capture time**: After 1:30 PM for final daily data

### Stock Code Format
- Taiwan stocks use 4-digit codes (e.g., 2330 for TSMC)
- Each stock displays: code, company name, and percentage change

### Heatmap Layout
- Stocks grouped by industry sector
- Size represents market capitalization
- Color intensity represents price change magnitude

## Source URL

Default heatmap URL:
```
https://www.nstock.tw/market_index/heatmap?t1=1&t2=0&t3=0&t4=1&t5=0&iid&nh=0
```

Parameters:
- `t1=1`: Show listed stocks (上市)
- `t2=0`: OTC stocks filter
- `t3=0`: Additional filter
- `t4=1`: Display mode
- `t5=0`: Additional option
- `nh=0`: No header mode

## Troubleshooting

### Page Load Issues
- The script waits for the treemap to render
- If capture fails, try `--no-headless` to see what's happening
- Network issues may require retry

### Empty or Partial Screenshot
- Increase wait time in the script
- Check if nStock.tw is accessible
- Verify the page loads correctly in a regular browser

### AI Analysis Fails
- Ensure GITHUB_TOKEN is set correctly
- Check GitHub Models API quota
- Verify the screenshot is valid and readable

### Browser Errors
- Ensure Playwright browsers are installed: `playwright install chromium`
- Update Playwright: `pip install --upgrade playwright`
- Close other browser instances

## Automation

This skill is designed to run via GitHub Actions for automated daily updates. See `.github/workflows/generate-twstock-map.yml` for the automation configuration.

## License

This project is for educational and personal use. Please respect nStock.tw's terms of service when using this tool.

## Data Source

Market data provided by [nStock.tw](https://www.nstock.tw)
