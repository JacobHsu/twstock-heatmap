#!/usr/bin/env python3
"""
Taiwan Stock Market Heatmap AI Analysis
Uses GitHub Models API (GPT-4o Vision) to identify top losers from multiple heatmap screenshots
"""

import os
import sys
import json
import base64
import csv
import io
from datetime import datetime
from pathlib import Path
import argparse

# Fix Windows console encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")



def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value


def load_stock_mapping():
    """Load stock name to ticker mapping from StockMapping.csv"""
    mapping_path = Path(__file__).parent.parent.parent.parent / "data" / "StockMapping.csv"
    
    stock_mapping = {}
    
    if mapping_path.exists():
        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Map stock name to ticker
                    stock_mapping[row['name']] = row['ticker']
            print(f"✓ Loaded {len(stock_mapping)} stock mappings from {mapping_path.name}")
        except Exception as e:
            print(f"Warning: Failed to load stock mapping: {e}")
    else:
        print(f"Warning: Stock mapping file not found: {mapping_path}")
    
    return stock_mapping




def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_single_image(image_path, api_token, industry_name="all", stock_mapping=None):
    """
    Analyze a single heatmap image using GitHub Models API
    """
    import requests

    print(f"Analyzing {industry_name} from {image_path}...")

    # Encode image
    base64_image = encode_image(image_path)

    # GitHub Models API endpoint
    url = "https://models.inference.ai.azure.com/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}",
    }

    prompt = f"""分析這張台股市場熱力圖截圖 ({industry_name})。

這是一個台灣股票市場熱力圖：
- 紅色 = 上漲
- 綠色 = 下跌 (顏色越深綠，跌幅越大)
- 灰色 = 平盤
- 每個方塊包含：公司名稱、漲跌幅百分比

任務：找出「跌幅百分比最大」（數值最負）的 5 檔股票。

⚠️ 關鍵要求 (CRITICAL):
1. 【忽略方塊大小】：不要只看大方塊！跌幅大的股票通常在「小型方塊」中（例如 -5% 的小方塊比 -0.5% 的大方塊更重要）。
2. 【搜尋深綠色】：優先掃描顏色最深的綠色區塊，無論它多小。
3. 【精確排序】：必須嚴格按照百分比數值排序（例如 -5.42% 排在 -2.74% 前面）。
4. 【完整掃描】：請仔細檢查圖片右側和下方的邊緣區域，那裡常有跌幅重的小型股。

請返回 JSON 格式：
{{
  "top_losers": [
    {{"name": "公司名稱", "change": "跌幅百分比"}},
    ... (共5筆)
  ],
  "market": "taiwan",
  "industry": "{industry_name}"
}}"""

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.1,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        
        # Add ticker symbols to each stock if mapping is provided
        # Only include stocks with valid tickers (filter out AI misidentifications)
        if stock_mapping and "top_losers" in data:
            reordered_losers = []
            skipped_count = 0
            
            for stock in data["top_losers"]:
                stock_name = stock.get("name", "")
                # Look up ticker in mapping
                ticker = stock_mapping.get(stock_name, "")
                
                if not ticker:
                    print(f"  ⚠ No ticker found for: {stock_name} - SKIPPED (possible AI misidentification)")
                    skipped_count += 1
                    continue  # Skip this stock entirely
                
                # Create new ordered dict with ticker first
                reordered_stock = {
                    "ticker": ticker,
                    "name": stock_name,
                    "change": stock.get("change", "")
                }
                reordered_losers.append(reordered_stock)
            
            data["top_losers"] = reordered_losers
            
            if skipped_count > 0:
                print(f"  ℹ️ Filtered out {skipped_count} stock(s) without valid ticker")
        
        return data

    except Exception as e:
        print(f"Error analyzing {industry_name}: {e}")
        # Return empty structure on error
        return {
            "top_losers": [],
            "market": "taiwan",
            "industry": industry_name,
            "error": str(e),
        }


def save_json_api(data, output_path):
    """Save combined JSON API response file"""

    current_time = datetime.utcnow().isoformat() + "Z"

    # Add API metadata
    api_response = {
        "status": "success",
        "data": data,
        "version": "2.0",
        "market": "taiwan",
        "source": "nstock.tw",
        "last_updated": current_time,
        "generated_at": current_time,
    }

    # Save JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(api_response, f, indent=2, ensure_ascii=False)

    print(f"JSON API saved: {output_path}")


def main():
    # Load .env file if exists (for local development)
    load_env_file()
    
    # Load stock mapping from CSV
    stock_mapping = load_stock_mapping()
    
    parser = argparse.ArgumentParser(
        description="Analyze multiple Taiwan stock heatmaps using GitHub Models API"
    )
    # Allow multiple inputs in format "type:path"
    # Example: -i all:twstock.png otc-elec:twstock_otc_elec.png
    parser.add_argument(
        "-i",
        "--inputs",
        nargs="+",
        help="Input images in format 'type:path' (e.g. all:twstock.png)",
        required=True,
    )
    parser.add_argument(
        "-o", "--output", default="api/twstock_top_losers.json", help="Output JSON path"
    )
    parser.add_argument("--token", help="GitHub Models API token")

    args = parser.parse_args()

    # Get API token (priority: --token argument > environment variable)
    api_token = args.token or os.environ.get("GITHUB_TOKEN")
    if not api_token:
        print("Error: GitHub token required")
        sys.exit(1)

    script_dir = Path(__file__).parent.parent.parent.parent
    results = {}

    # Process each input image
    for input_arg in args.inputs:
        try:
            if ":" in input_arg:
                industry_type, filename = input_arg.split(":", 1)
            else:
                industry_type = "default"
                filename = input_arg

            image_path = script_dir / filename

            if not image_path.exists():
                print(f"Warning: Image not found: {image_path}")
                continue

            # Analyze image with stock mapping
            analysis = analyze_single_image(
                str(image_path), api_token, industry_type, stock_mapping
            )
            results[industry_type] = analysis["top_losers"]

        except Exception as e:
            print(f"Failed to process {input_arg}: {e}")

    # Save combined results
    output_path = script_dir / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_json_api(results, str(output_path))

    print("\nAnalysis complete!")
    print(f"Processed industries: {', '.join(results.keys())}")


if __name__ == "__main__":
    main()
