#!/usr/bin/env python3
"""
完整測試腳本：測試所有四個產業的截圖和分析
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description):
    """執行命令並顯示結果"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"命令: {' '.join(cmd)}\n")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    elapsed = time.time() - start_time
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"⚠️ 錯誤輸出:\n{result.stderr}")
    
    print(f"\n⏱️ 執行時間: {elapsed:.2f} 秒")
    
    if result.returncode != 0:
        print(f"❌ 失敗 (返回碼: {result.returncode})")
        return False
    else:
        print(f"✅ 成功")
        return True

def main():
    print("🚀 台股熱力圖完整測試")
    print("=" * 60)
    
    # 檢查是否在正確的目錄
    if not Path("skills/twstock-heatmap/scripts/capture_twstock.py").exists():
        print("❌ 錯誤：請在專案根目錄執行此腳本")
        sys.exit(1)
    
    industries = [
        ("all", "上市總覽"),
        ("otc-elec", "櫃買電子"),
        ("otc-semi", "櫃買半導體"),
        ("otc-construction", "櫃買營建")
    ]
    
    # 步驟 1: 截圖所有產業
    print("\n📸 步驟 1/2: 截圖所有產業熱力圖")
    print("=" * 60)
    
    for industry_type, industry_name in industries:
        success = run_command(
            ["python", "skills/twstock-heatmap/scripts/capture_twstock.py", 
             "-t", industry_type, "--no-html"],
            f"截圖 {industry_name} ({industry_type})"
        )
        if not success:
            print(f"\n❌ {industry_name} 截圖失敗，停止測試")
            sys.exit(1)
        time.sleep(2)  # 避免請求過快
    
    # 檢查截圖檔案
    print("\n📁 檢查生成的截圖檔案:")
    print("=" * 60)
    expected_files = [
        "twstock.png",
        "twstock_otc-elec.png",
        "twstock_otc-semi.png",
        "twstock_otc-construction.png"
    ]
    
    all_files_exist = True
    for filename in expected_files:
        filepath = Path(filename)
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {filename} ({size:,} bytes)")
        else:
            print(f"❌ {filename} 不存在")
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ 部分截圖檔案不存在，停止測試")
        sys.exit(1)
    
    # 步驟 2: AI 分析
    print("\n🤖 步驟 2/2: AI 分析所有熱力圖")
    print("=" * 60)
    
    success = run_command(
        ["python", "skills/twstock-heatmap/scripts/analyze_twstock.py",
         "-i", 
         "all:twstock.png",
         "otc-elec:twstock_otc-elec.png",
         "otc-semi:twstock_otc-semi.png",
         "otc-construction:twstock_otc-construction.png",
         "-o", "api/twstock_top_losers.json"],
        "AI 分析所有產業"
    )
    
    if not success:
        print("\n❌ AI 分析失敗")
        sys.exit(1)
    
    # 檢查 API 檔案
    print("\n📄 檢查 API 輸出:")
    print("=" * 60)
    api_file = Path("api/twstock_top_losers.json")
    if api_file.exists():
        import json
        with open(api_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ API 檔案已生成")
        print(f"\n包含的產業:")
        for industry in data.get('data', {}).keys():
            count = len(data['data'][industry])
            print(f"  - {industry}: {count} 檔股票")
        
        # 顯示每個產業的前 3 名
        print(f"\n📊 各產業跌幅前 3 名:")
        industry_display = {
            'all': '📈 上市總覽',
            'otc-elec': '🔌 櫃買電子',
            'otc-semi': '💎 櫃買半導體',
            'otc-construction': '🏗️ 櫃買營建'
        }
        
        for key, name in industry_display.items():
            if key in data.get('data', {}):
                print(f"\n{name}:")
                for i, stock in enumerate(data['data'][key][:3], 1):
                    ticker = stock.get('ticker', 'N/A')
                    stock_name = stock.get('name', 'N/A')
                    change = stock.get('change', 'N/A')
                    print(f"  {i}. {ticker} {stock_name}: {change}")
    else:
        print("❌ API 檔案不存在")
        sys.exit(1)
    
    # 測試完成
    print("\n" + "=" * 60)
    print("🎉 所有測試完成！")
    print("=" * 60)
    print("\n生成的檔案:")
    for filename in expected_files:
        print(f"  ✅ {filename}")
    print(f"  ✅ api/twstock_top_losers.json")
    print("\n您可以查看 api/twstock_top_losers.json 來確認完整的 API 輸出")

if __name__ == "__main__":
    main()
