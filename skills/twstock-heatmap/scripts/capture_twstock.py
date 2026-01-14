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
from pathlib import Path

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

    # nStock heatmap URL base
    # t1=1: listed stocks
    # t2=0: otc filter
    # t3=0: additional filter
    # t4=1: display mode
    # t5=0: additional option
    base_url = "https://www.nstock.tw/market_index/heatmap?t1=1&t2=0&t3=0&t4=1&t5=0&"

    # Industry map parameters
    industry_params = {
        "all": "iid&nh=0",  # 上市總覽 (Default)
        "otc-elec": "iid=28&nh=0",  # 櫃買電子組件
        "otc-semi": "iid=24&nh=0",  # 櫃買半導體
        "otc-construction": "iid=14&nh=0",  # 櫃買營建
    }

    # Construct full URL
    params = industry_params.get(map_type, industry_params["all"])
    url = f"{base_url}{params}"

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

            # Wait for Nuxt.js hydration and data loading
            print("Waiting for page to fully render (20 seconds)...")
            time.sleep(20)

            # Additional wait for any lazy-loaded content
            try:
                # Wait for any loading indicators to disappear
                page.wait_for_selector(".loading", state="hidden", timeout=5000)
            except Exception:
                pass  # No loading indicator found, continue

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
            time.sleep(1)

            # Move mouse away to clear any hover effects
            page.mouse.move(10, 10)
            time.sleep(1)

            # Take screenshot
            print("Capturing screenshot...")

            if treemap:
                # Element-specific screenshot
                treemap.scroll_into_view_if_needed()
                time.sleep(1)
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
        choices=["all", "otc-elec", "otc-semi", "otc-construction"],
        help="Industry type (all, otc-elec, otc-semi, otc-construction)",
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

    # Output paths - root directory
    script_dir = Path(__file__).parent.parent.parent.parent

    # Determine filename
    if args.output:
        png_filename = args.output
    else:
        png_filename = (
            f"twstock_{args.type}.png" if args.type != "all" else "twstock.png"
        )

    png_path = script_dir / png_filename
    html_path = (
        script_dir / f"twstock_{args.type}.html"
        if args.type != "all"
        else script_dir / "index.html"
    )

    print(f"Output directory: {script_dir}\n")

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
