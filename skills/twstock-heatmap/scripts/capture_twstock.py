#!/usr/bin/env python3
"""
Taiwan Stock Market Heatmap Screenshot - Playwright Version
Capture nStock.tw heatmap as high-quality PNG screenshot
"""

import argparse
import sys
import subprocess
import time
import os
import io
import json
from pathlib import Path
import time

# Fix Windows console encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def check_dependencies():
    """Check if required packages are installed, install if not."""
    packages = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        packages.append("playwright")

    try:
        from PIL import Image
    except ImportError:
        packages.append("Pillow")

    if packages:
        print(f"Installing required packages: {', '.join(packages)}...")
        install_cmd = [sys.executable, "-m", "pip", "install"]
        if sys.platform != "win32":
            install_cmd.append("--break-system-packages")
        install_cmd.extend(packages)
        subprocess.run(install_cmd, check=True)

        # Install Playwright browsers
        if "playwright" in packages:
            print("Installing Playwright browsers...")
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"], check=True
            )


def find_treemap_element(page):
    """
    Auto-detect treemap element using multiple selectors.
    Returns element if found, None for full-page fallback.
    """
    selectors = [
        # nStock specific selectors
        ".treemap-container",
        "#treemap",
        '[class*="treemap"]',
        '[class*="heatmap"]',
        ".market-heatmap",
        # Generic chart selectors
        "canvas",
        'svg[class*="chart"]',
        ".chart-container",
        # Nuxt/Vue specific
        '[data-v-][class*="map"]',
    ]

    for selector in selectors:
        try:
            element = page.wait_for_selector(selector, timeout=3000)
            if element:
                # Verify element has reasonable dimensions
                box = element.bounding_box()
                if box and box["width"] > 200 and box["height"] > 200:
                    print(f"Found treemap with selector: {selector}")
                    return element
        except Exception:
            continue

    print("No specific treemap element found, will capture main content area")
    return None



# Mapping: JSON industry name -> (iid, capture_key_suffix)
INDUSTRY_MAP = {
    "半導體": ("24", "semi"),
    "電子組件": ("28", "elec"),
    "電機": ("5", "electrical"),
    "電子通路": ("29", "channel"),
    "電腦週邊": ("25", "computer"),
    "營建": ("14", "construction"),
    "其他": ("20", "other"),
    "光電": ("26", "opto"),
    "化學": ("21", "chem"),
    "生技": ("22", "bio"),
    "汽車": ("12", "auto"),
    "電器": ("6", "cable"),
    "其他電子": ("31", "otherele"),
    "網通": ("27", "network"),
    "塑膠": ("3", "plastic"),
    "航運": ("15", "shipping"),
    "綠能環保": ("35", "green"),
    "資訊服務": ("30", "info"),
    "觀光": ("16", "tourism"),
}

# nStock heatmap URL configuration
# t1: 0=TSE (上市), 1=OTC (上櫃)
# t2=0: otc filter
# t3=0: additional filter
# t4=1: display mode
# t5=0: additional option
# iid: industry ID

# Industry map parameters: (t1_value, iid_value)
INDUSTRY_PARAMS = {
    # === TSE (上市) Categories ===
    "tse": (0, ""),  # 上市總覽 (Default)
    "tse-semi": (0, "24"),  # 上市半導體
    "tse-network": (0, "27"),  # 上市網通
    "tse-elec": (0, "28"),  # 上市電子組件
    "tse-computer": (0, "25"),  # 上市電腦週邊
    "tse-channel": (0, "29"),  # 上市電子通路
    "tse-plastic": (0, "3"),  # 上市塑膠
    "tse-electrical": (0, "5"),  # 上市電機
    "tse-construction": (0, "14"),  # 上市營建
    "tse-shipping": (0, "15"),  # 上市航運
    "tse-green": (0, "35"),  # 上市綠能環保
    "tse-opto": (0, "26"),  # 上市光電
    "tse-chem": (0, "21"),  # 上市化學
    "tse-bio": (0, "22"),  # 上市生技
    "tse-auto": (0, "12"),  # 上市汽車
    "tse-cable": (0, "6"),  # 上市電器
    "tse-otherele": (0, "31"),  # 上市其他電子
    "tse-other": (0, "20"),  # 上市其他

    # === OTC (上櫃) Categories ===
    "otc": (1, ""),  # 上櫃總覽
    "otc-semi": (1, "24"),  # 上櫃半導體
    "otc-network": (1, "27"),  # 上櫃網通
    "otc-elec": (1, "28"),  # 上櫃電子組件
    "otc-computer": (1, "25"),  # 上櫃電腦週邊
    "otc-channel": (1, "29"),  # 上櫃電子通路
    "otc-electrical": (1, "5"),  # 上櫃電機
    "otc-construction": (1, "14"),  # 上櫃營建
    "otc-other": (1, "20"),  # 上櫃其他
    "otc-info": (1, "30"),  # 上櫃資訊服務
    "otc-tourism": (1, "16"),  # 上櫃觀光
    "otc-green": (1, "35"),  # 上櫃綠能環保
    "otc-opto": (1, "26"),  # 上櫃光電
    "otc-chem": (1, "21"),  # 上櫃化學
    "otc-bio": (1, "22"),  # 上櫃生技
    "otc-cable": (1, "6"),  # 上櫃電器
    "otc-otherele": (1, "31"),  # 上櫃其他電子
}


def capture_twstock_heatmap(map_type="all", output_path="twstock.png", headless=True):
    """
    Capture nStock.tw heatmap as screenshot using Playwright.

    Args:
        map_type: Industry type (all, otc-elec, otc-semi)
        output_path: Path to save the screenshot
        headless: Run in headless mode (default: True)

    Returns:
        True if successful, False otherwise
    """
    check_dependencies()

    from playwright.sync_api import sync_playwright
    from PIL import Image
    import io as iolib

    # Construct full URL
    t1_value, iid_value = INDUSTRY_PARAMS.get(map_type, INDUSTRY_PARAMS["tse"])
    iid_param = f"iid={iid_value}" if iid_value else "iid"
    url = f"https://www.nstock.tw/market_index/heatmap?t1={t1_value}&t2=0&t3=0&t4=1&t5=0&{iid_param}&nh=0"

    print(f"Taiwan Stock Heatmap Screenshot (Playwright)")
    print(f"Type: {map_type}")
    print(f"URL: {url}")
    print(f"Output: {output_path}")
    print(f"Headless: {headless}\n")

    try:
        with sync_playwright() as p:
            # Launch browser with settings optimized for SSR pages
            print("Launching Chromium browser...")
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )

            # Create context with realistic settings
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="zh-TW",
                timezone_id="Asia/Taipei",
                color_scheme="light",
            )

            # Anti-detection measures
            context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-TW', 'zh', 'en-US', 'en']
                });
            """)

            page = context.new_page()

            # Navigate to nStock heatmap
            print("Loading nStock.tw heatmap page...")
            page.goto(url, wait_until="networkidle", timeout=60000)

            # Smart wait: detect actual treemap rendering instead of hard 20s sleep
            print("Waiting for heatmap to render...")
            treemap_selectors = [
                '[class*="treemap"] rect',
                '[class*="treemap"] canvas',
                '[class*="heatmap"] rect',
                'canvas',
                'svg rect',
            ]
            rendered = False
            for sel in treemap_selectors:
                try:
                    page.wait_for_selector(sel, state="visible", timeout=15000)
                    print(f"  Detected rendered element: {sel}")
                    rendered = True
                    break
                except Exception:
                    continue

            if not rendered:
                # Fallback: wait for network idle as a sign the page is done
                print("  No treemap element detected, waiting for network idle...")
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass

            # Brief pause for animations/transitions to complete
            time.sleep(2)

            # Wait for any loading indicators to disappear
            try:
                page.wait_for_selector(".loading", state="hidden", timeout=3000)
            except Exception:
                pass

            # Check if page loaded successfully
            try:
                page_title = page.title()
                print(f"Page loaded: {page_title}")
            except Exception:
                print("Could not get page title")

            # Try to find specific treemap element
            print("Looking for heatmap element...")
            treemap = find_treemap_element(page)

            # Hide any floating elements that might interfere
            print("Cleaning up page for screenshot...")
            page.evaluate("""
                // Hide navigation, ads, and floating elements
                const selectorsToHide = [
                    'nav', 'header', '.navbar', '.nav-bar',
                    '.ad', '.ads', '[class*="advertisement"]',
                    '.popup', '.modal', '.overlay',
                    '[class*="cookie"]', '[class*="consent"]',
                    '.floating', '[style*="position: fixed"]'
                ];

                selectorsToHide.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        el.style.display = 'none';
                    });
                });

                // Also hide high z-index elements (tooltips, popups)
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    const zIndex = parseInt(style.zIndex) || 0;
                    if (zIndex > 1000 && !el.closest('[class*="treemap"], [class*="heatmap"], [class*="chart"]')) {
                        el.style.display = 'none';
                    }
                });
            """)

            # Move mouse away to clear any hover effects
            page.mouse.move(10, 10)
            time.sleep(0.5)

            # Take screenshot
            print("Capturing screenshot...")

            if treemap:
                # Element-specific screenshot
                treemap.scroll_into_view_if_needed()
                time.sleep(0.5)
                screenshot_bytes = treemap.screenshot(type="png")
            else:
                # Full page with smart clipping
                # First, get the main content area dimensions
                clip_area = page.evaluate("""
                    () => {
                        // Try to find the main content container
                        const selectors = [
                            '.treemap-wrapper', '.heatmap-wrapper',
                            '.market-map', '.chart-area',
                            'main', '.main-content', '#app'
                        ];
                        
                        for (const sel of selectors) {
                            const el = document.querySelector(sel);
                            if (el) {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 400 && rect.height > 300) {
                                    return {
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height
                                    };
                                }
                            }
                        }
                        
                        // Default: capture viewport area below header
                        return {
                            x: 0,
                            y: 80,
                            width: 1920,
                            height: 900
                        };
                    }
                """)

                screenshot_bytes = page.screenshot(type="png", clip=clip_area)

            # Save screenshot
            with open(output_path, "wb") as f:
                f.write(screenshot_bytes)

            file_size = os.path.getsize(output_path)
            print(f"Screenshot saved: {output_path}")
            print(f"File size: {file_size:,} bytes")

            # Clean up
            browser.close()
            return True

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return False


def create_html(html_path, png_filename="twstock.png"):
    """Create simple HTML to display the screenshot."""

    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taiwan Stock Market Heatmap</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background-color: #1a1a2e;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
            font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        h1 {{
            color: #fff;
            margin-bottom: 20px;
            font-size: 1.5em;
        }}
        .timestamp {{
            color: #888;
            margin-bottom: 20px;
            font-size: 0.9em;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }}
        .source {{
            color: #666;
            margin-top: 20px;
            font-size: 0.8em;
        }}
        a {{
            color: #4ecdc4;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>Taiwan Stock Market Heatmap</h1>
    <p class="timestamp">Generated: <span id="time"></span></p>
    <img src="{png_filename}" alt="Taiwan Stock Market Heatmap">
    <p class="source">Data source: <a href="https://www.nstock.tw" target="_blank">nStock.tw</a></p>
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString('zh-TW');
    </script>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML created: {html_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Capture nStock.tw Taiwan stock heatmap as screenshot using Playwright"
    )
    parser.add_argument(
        "-t",
        "--type",
        default="all",
        help="Industry type (default: all - dynamically from losers JSON)",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Don't create HTML file, only save screenshot",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run with visible browser (for debugging)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output PNG filename (default: based on type)",
    )

    args = parser.parse_args()

    # Output paths - heatmaps directory
    script_dir = Path(__file__).parent.parent.parent.parent
    heatmaps_dir = script_dir / "heatmaps"
    
    # Create heatmaps directory if it doesn't exist
    heatmaps_dir.mkdir(exist_ok=True)

    # If 'all' is specified, dynamically determine categories from losers JSON
    if args.type == "all":
        # Clean old heatmaps before capturing new ones
        old_pngs = list(heatmaps_dir.glob("*.png"))
        if old_pngs:
            print(f"🗑️ Removing {len(old_pngs)} old heatmap(s)...", flush=True)
            for png in old_pngs:
                png.unlink()

        json_path = script_dir / "api" / "histock_top_losers.json"
        if not json_path.exists():
            print(f"❌ Losers JSON not found: {json_path}", flush=True)
            sys.exit(1)

        with open(json_path, "r", encoding="utf-8") as f:
            losers_data = json.load(f)

        # Count stocks per (market, industry) pair
        from collections import Counter
        pair_counts = Counter()
        for stock in losers_data["data"]:
            pair = (stock["market"], stock["industry"])
            pair_counts[pair] += 1

        # Map to capture keys (only include industries with >= 2 stocks)
        MIN_STOCKS = 2
        all_categories = []
        for (market, industry), count in sorted(pair_counts.items()):
            if count < MIN_STOCKS:
                continue
            if industry in INDUSTRY_MAP:
                iid, suffix = INDUSTRY_MAP[industry]
                key = f"{market}-{suffix}"
                if key in INDUSTRY_PARAMS:
                    all_categories.append(key)
                    print(f"  ✓ {key} ({industry}: {count} stocks)", flush=True)
                else:
                    print(f"⚠️ No params for key: {key}, skipping", flush=True)
            else:
                print(f"⚠️ Unknown industry: {industry} ({count} stocks), skipping", flush=True)

        all_categories = sorted(set(all_categories))

        if not all_categories:
            print("❌ No valid categories found from losers JSON", flush=True)
            sys.exit(1)

        print(f"📊 Capturing {len(all_categories)} heatmap categories (from losers JSON)...", flush=True)
        print(f"Categories: {', '.join(all_categories)}", flush=True)
        print(f"Output directory: {heatmaps_dir}\n", flush=True)
        
        start_time = time.time()
        headless = not args.no_headless
        failed_categories = []
        
        for i, category in enumerate(all_categories, 1):
            print(f"\n{'='*60}", flush=True)
            print(f"[{i}/{len(all_categories)}] Capturing: {category}", flush=True)
            print(f"{'='*60}", flush=True)
            
            # Determine filename
            png_filename = f"twstock_{category}.png" if category not in ["tse"] else "twstock.png"
            png_path = heatmaps_dir / png_filename
            
            # Capture heatmap
            success = capture_twstock_heatmap(category, str(png_path), headless=headless)
            
            if not success:
                print(f"❌ Failed to capture {category}", flush=True)
                failed_categories.append(category)
            else:
                print(f"✅ Successfully captured {category}", flush=True)
        
        # Summary
        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        print(f"\n{'='*60}", flush=True)
        print(f"📊 SUMMARY", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"✅ Successful: {len(all_categories) - len(failed_categories)}/{len(all_categories)}", flush=True)
        if failed_categories:
            print(f"❌ Failed: {', '.join(failed_categories)}", flush=True)
        print(f"⏱️  Total time: {minutes}m {seconds}s", flush=True)
        
        # Create main HTML viewer if not disabled
        if not args.no_html:
            print(f"\n📄 Creating HTML viewer...", flush=True)
            html_path = script_dir / "index.html"
            create_html(str(html_path), "twstock.png")
            print(f"HTML: {html_path}", flush=True)
        
        if failed_categories:
            sys.exit(1)
        else:
            print(f"\n🎉 All heatmaps captured successfully!", flush=True)
            sys.exit(0)
    
    # Single category capture (original behavior)
    # Determine filename
    if args.output:
        png_filename = args.output
    else:
        png_filename = (
            f"twstock_{args.type}.png" if args.type not in ["tse", "all"] else "twstock.png"
        )

    png_path = heatmaps_dir / png_filename
    html_path = (
        script_dir / f"twstock_{args.type}.html"
        if args.type not in ["tse", "all"]
        else script_dir / "index.html"
    )

    print(f"Output directory: {heatmaps_dir}\n")

    # Capture heatmap screenshot
    headless = not args.no_headless
    success = capture_twstock_heatmap(args.type, str(png_path), headless=headless)

    if not success:
        print("\nFailed to capture screenshot")
        sys.exit(1)

    # Create HTML if requested
    if not args.no_html:
        print()
        create_html(str(html_path), png_filename)

    print(f"\nDone!")
    print(f"PNG: {png_path}")
    if not args.no_html:
        print(f"HTML: {html_path}")
        print(f"\nOpen {html_path} in your browser to view the heatmap.")

    sys.exit(0)



if __name__ == "__main__":
    main()
