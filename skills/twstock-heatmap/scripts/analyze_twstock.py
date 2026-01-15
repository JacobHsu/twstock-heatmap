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
        # AND filter stocks with decline > 3%
        if stock_mapping and "top_losers" in data:
            reordered_losers = []
            skipped_count = 0
            filtered_by_decline = 0
            
            for stock in data["top_losers"]:
                stock_name = stock.get("name", "")
                change_str = stock.get("change", "")
                
                # Look up ticker in mapping
                ticker = stock_mapping.get(stock_name, "")
                
                if not ticker:
                    print(f"  ⚠ No ticker found for: {stock_name} - SKIPPED (possible AI misidentification)")
                    skipped_count += 1
                    continue  # Skip this stock entirely
                
                # Filter by decline percentage (> 3%)
                try:
                    # Extract percentage value from string like "-5.23%" or "-2.5%"
                    decline_value = float(change_str.replace("%", "").replace("+", ""))
                    
                    # Only include if decline is greater than 3% (decline_value < -3)
                    if decline_value > -3.0:
                        filtered_by_decline += 1
                        continue
                except (ValueError, AttributeError):
                    # If we can't parse the percentage, skip this stock
                    print(f"  ⚠ Invalid change format for {stock_name}: {change_str} - SKIPPED")
                    skipped_count += 1
                    continue
                
                # Create new ordered dict with ticker first
                reordered_stock = {
                    "ticker": ticker,
                    "name": stock_name,
                    "change": change_str
                }
                reordered_losers.append(reordered_stock)
            
            data["top_losers"] = reordered_losers
            
            if skipped_count > 0:
                print(f"  ℹ️ Filtered out {skipped_count} stock(s) without valid ticker")
            if filtered_by_decline > 0:
                print(f"  ℹ️ Filtered out {filtered_by_decline} stock(s) with decline ≤ 3%")
        
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
    # Or use --auto to automatically scan heatmaps/ directory
    parser.add_argument(
        "-i",
        "--inputs",
        nargs="+",
        help="Input images in format 'type:path' (e.g. tse:heatmaps/twstock.png)",
        required=False,
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically scan and analyze all PNGs in heatmaps/ directory",
    )
    parser.add_argument(
        "--batch",
        choices=["tse", "otc"],
        help="Batch mode: analyze only TSE or OTC categories (useful to avoid API rate limits)",
    )
    parser.add_argument(
        "-o", "--output", default="api/twstock_top_losers.json", help="Output JSON path"
    )
    parser.add_argument("--token", help="GitHub Models API token")

    args = parser.parse_args()
    
    # Validate arguments
    if not args.inputs and not args.auto:
        print("Error: Either --inputs or --auto must be specified")
        print("Examples:")
        print("  Auto mode:   python analyze_twstock.py --auto")
        print("  Manual mode: python analyze_twstock.py -i tse:heatmaps/twstock.png")
        sys.exit(1)

    # Get API token (priority: --token argument > environment variable)
    api_token = args.token or os.environ.get("GITHUB_TOKEN")
    if not api_token:
        print("Error: GitHub token required")
        sys.exit(1)

    script_dir = Path(__file__).parent.parent.parent.parent
    heatmaps_dir = script_dir / "heatmaps"
    results = {}
    
    # Auto-scan mode: detect all PNGs in heatmaps/ directory
    if args.auto:
        print("🔍 Auto-scanning heatmaps directory...", flush=True)
        
        if not heatmaps_dir.exists():
            print(f"Error: Heatmaps directory not found: {heatmaps_dir}")
            sys.exit(1)
        
        # Find all PNG files
        png_files = list(heatmaps_dir.glob("*.png"))
        
        if not png_files:
            print(f"Error: No PNG files found in {heatmaps_dir}")
            sys.exit(1)
        
        # Category to market mapping
        category_market = {
            'tse': 'tse', 'otc': 'otc',
            'tse-semi': 'tse', 'tse-elec': 'tse', 'tse-computer': 'tse', 'tse-plastic': 'tse', 'tse-electrical': 'tse', 'tse-construction': 'tse', 'tse-channel': 'tse', 'tse-green': 'tse',
            'otc-elec': 'otc', 'otc-semi': 'otc', 'otc-computer': 'otc', 'otc-construction': 'otc', 'otc-other': 'otc', 'otc-info': 'otc', 'otc-tourism': 'otc', 'otc-green': 'otc'
        }
        
        print(f"Found {len(png_files)} heatmap(s):", flush=True)
        
        # Auto-detect category from filename
        inputs_list = []
        for png_file in sorted(png_files):
            filename = png_file.name
            
            # Detect category from filename
            if filename == "twstock.png":
                category = "tse"
            elif filename.startswith("twstock_"):
                # Extract category from filename (e.g., twstock_otc.png -> otc)
                category = filename.replace("twstock_", "").replace(".png", "")
            else:
                category = filename.replace(".png", "")
            
            # Filter by batch if specified
            if args.batch:
                market = category_market.get(category)
                if market != args.batch:
                    continue
            
            inputs_list.append(f"{category}:{png_file}")
            print(f"  - {category}: {png_file.name}", flush=True)
        
        # Use detected inputs
        args.inputs = inputs_list
        print()

    # Process each input image
    total_inputs = len(args.inputs)
    for idx, input_arg in enumerate(args.inputs, 1):
        try:
            if ":" in input_arg:
                industry_type, filename = input_arg.split(":", 1)
            else:
                industry_type = "default"
                filename = input_arg

            image_path = script_dir / filename
            
            # If path doesn't exist, try as absolute path
            if not image_path.exists():
                image_path = Path(filename)

            if not image_path.exists():
                print(f"Warning: Image not found: {filename}")
                continue

            print(f"Analyzing {industry_type} from {image_path.name}...", flush=True)
            
            # Analyze image with stock mapping
            analysis = analyze_single_image(
                str(image_path), api_token, industry_type, stock_mapping
            )
            results[industry_type] = analysis["top_losers"]
            
            # Add delay between API calls to avoid rate limits (except for last one)
            if idx < total_inputs:
                import time
                delay_seconds = 10
                print(f"⏳ Waiting {delay_seconds}s before next analysis to avoid API rate limits...", flush=True)
                time.sleep(delay_seconds)

        except Exception as e:
            print(f"Error analyzing {industry_type}: {e}", flush=True)
            results[industry_type] = []

    # Save combined results
    output_path = script_dir / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_json_api(results, str(output_path))

    print("\nAnalysis complete!")
    print(f"Processed industries: {', '.join(results.keys())}")


if __name__ == "__main__":
    main()
