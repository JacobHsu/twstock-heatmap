#!/usr/bin/env python3
"""
Scrape histock.tw top losers ranking page.
Outputs: api/histock_top_losers.json
Source: https://histock.tw/stock/rank.aspx?m=4&d=0&t=dt
"""

import csv
import json
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4"], check=True)
    import requests
    from bs4 import BeautifulSoup


def load_stock_mapping(csv_path):
    """Load industry and market mapping from StockMapping.csv."""
    mapping = {}
    if not csv_path.exists():
        return mapping
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row.get("ticker", "").strip()
            if ticker:
                mapping[ticker] = {
                    "industry": row.get("industry", "").strip(),
                    "market": row.get("market", "").strip(),
                }
    return mapping


def scrape_histock_top_losers():
    """Scrape top 50 losers from histock.tw."""
    url = "https://histock.tw/stock/rank.aspx?m=4&d=0&t=dt"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    print(f"Fetching: {url}")
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the GridView table (ASP.NET control ID: CPHB1_gv)
    table = soup.find("table", id=lambda x: x and "gv" in x.lower())
    if not table:
        # Fallback: find by structure
        tables = soup.find_all("table")
        for t in tables:
            if t.find("th") and "代號" in t.get_text():
                table = t
                break

    if not table:
        print("ERROR: Could not find ranking table on page")
        sys.exit(1)

    rows = table.find_all("tr")
    print(f"Found {len(rows) - 1} data rows (excluding header)")

    # Load industry mapping
    project_root = Path(__file__).parent.parent.parent.parent
    csv_path = project_root / "data" / "StockMapping.csv"
    stock_mapping = load_stock_mapping(csv_path)
    print(f"Loaded {len(stock_mapping)} stocks from StockMapping.csv")

    results = []
    for row in rows[1:51]:  # Skip header, take first 50
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        # Column 0: ticker (may be inside <a> tag)
        ticker_el = cells[0].find("a")
        ticker = ticker_el.get_text(strip=True) if ticker_el else cells[0].get_text(strip=True)

        # Column 1: name
        name_el = cells[1].find("a")
        name = name_el.get_text(strip=True) if name_el else cells[1].get_text(strip=True)

        # Column 2: price
        price = cells[2].get_text(strip=True)

        # Column 4: change % (漲跌幅)
        change = cells[4].get_text(strip=True)

        # Lookup from StockMapping.csv
        stock_info = stock_mapping.get(ticker, {})
        industry = stock_info.get("industry", "") if stock_info else ""
        market = stock_info.get("market", "") if stock_info else ""

        results.append({
            "ticker": ticker,
            "name": name,
            "price": price,
            "change": change,
            "industry": industry,
            "market": market,
        })

    return results


def main():
    results = scrape_histock_top_losers()
    print(f"Scraped {len(results)} stocks")

    # Output JSON
    project_root = Path(__file__).parent.parent.parent.parent
    output_path = project_root / "api" / "histock_top_losers.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "status": "success",
        "source": "https://histock.tw/stock/rank.aspx?m=4&d=0&t=dt",
        "count": len(results),
        "data": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Output: {output_path}")

    # Preview
    if results:
        print("\nTop 5 losers:")
        for s in results[:5]:
            print(f"  {s['ticker']} {s['name']:<6} {s['price']:>8} {s['change']:>8} {s['market']:<4} {s['industry']}")


if __name__ == "__main__":
    main()
