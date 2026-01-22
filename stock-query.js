// 股票多網站查詢功能

// 網站列表（來自 Chrome 擴展）
const websites = [
    'https://ifa.ai/tw-stock/{code}',
    'https://www.cnyes.com/twstock/{code}',
    'https://goodinfo.tw/tw/StockDividendSchedule.asp?STOCK_ID={code}',
    'https://statementdog.com/analysis/{code}/stock-health-check',
    'https://histock.tw/stock/{code}/每股淨值',
    'https://www.findbillion.com/twstock/{code}/financial_statement',
    'https://www.cmoney.tw/forum/stock/{code}?s=technical-analysis',
    'https://www.growin.tv/zh/my/analysis/{code}#analysis',
    'https://winvest.tw/Stock/Symbol/Comment/{code}',
    'https://www.fugle.tw/ai/{code}'
];

// 初始化功能
function initStockQuery() {
    const input = document.getElementById('stock-query-input');
    const btn = document.getElementById('stock-query-btn');
    const message = document.getElementById('stock-query-message');

    if (!input || !btn) {
        console.error('Stock query elements not found');
        return;
    }

    // 按鈕點擊事件
    btn.addEventListener('click', () => processStockCode(input, message));

    // Enter 鍵事件
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            processStockCode(input, message);
        }
    });
}

// 處理股票代碼
function processStockCode(input, message) {
    const stockCode = input.value.trim();

    // 驗證股票代碼
    if (!isValidStockCode(stockCode)) {
        showMessage(message, '格式錯誤 (4-6碼)', false);
        // Tailwind 錯誤樣式: 紅底紅框
        input.classList.add('bg-red-50', 'border-red-500');
        return;
    }

    // 移除錯誤樣式
    input.classList.remove('bg-red-50', 'border-red-500');
    showMessage(message, '開啟中...', true);

    // 開啟網站
    openWebsites(stockCode);

    // 清空輸入框
    input.value = '';

    // 2秒後清除訊息
    setTimeout(() => {
        showMessage(message, '', true);
    }, 2000);
}

// 驗證股票代碼（4-6 位數字）
function isValidStockCode(code) {
    return /^\d{4,6}$/.test(code);
}

// 開啟網站
function openWebsites(code) {
    console.log('開啟多個網站，股票代號:', code);

    // 開啟通用網站
    websites.forEach((url, index) => {
        setTimeout(() => {
            const finalUrl = url.replace('{code}', code);
            window.open(finalUrl, '_blank');
        }, index * 100); // 每個視窗間隔 100ms
    });

    // 特別處理 TradingView URL（區分上市上櫃）
    setTimeout(() => {
        const tradingViewUrl = getTradingViewUrl(code);
        window.open(tradingViewUrl, '_blank');
    }, websites.length * 100);

    // 特別處理 FastBull URL（區分上市上櫃）
    setTimeout(() => {
        const fastBullUrl = getFastBullUrl(code);
        window.open(fastBullUrl, '_blank');
    }, (websites.length + 1) * 100);
}

// 根據股票代碼判斷是上市還是上櫃，返回對應的 TradingView URL
function getTradingViewUrl(code) {
    // 確保 tpexStocks 變量存在 (定義在 tpex-stocks.js)
    if (typeof tpexStocks === 'undefined') {
        console.warn('tpexStocks data missing, defaulting to TWSE');
        return `https://tw.tradingview.com/symbols/TWSE-${code}/technicals/`;
    }

    return tpexStocks.has(code)
        ? `https://tw.tradingview.com/symbols/TPEX-${code}/technicals/`
        : `https://tw.tradingview.com/symbols/TWSE-${code}/technicals/`;
}

// 根據股票代碼判斷是上市還是上櫃，返回對應的 FastBull URL
function getFastBullUrl(code) {
    if (typeof tpexStocks === 'undefined') {
        return `https://www.fastbull.com/tw/quotation-detail/TWSE-${code}`;
    }

    return tpexStocks.has(code)
        ? `https://www.fastbull.com/tw/quotation-detail/TPEx-${code}`
        : `https://www.fastbull.com/tw/quotation-detail/TWSE-${code}`;
}

// 顯示訊息 (使用 Tailwind CSS)
function showMessage(messageElement, text, isSuccess) {
    if (!messageElement) return;

    // 如果 text 為空，則隱藏
    if (!text) {
        messageElement.classList.remove('opacity-100');
        messageElement.classList.add('opacity-0');
        return;
    }

    messageElement.textContent = text;

    // 重置顏色
    messageElement.classList.remove('bg-red-600', 'bg-green-600', 'bg-gray-800');

    // 根據狀態設置背景色
    if (!isSuccess) {
        messageElement.classList.add('bg-red-600');
    } else {
        messageElement.classList.add('bg-green-600');
    }

    // 顯示 (添加 opacity-100)
    messageElement.classList.remove('opacity-0');
    messageElement.classList.add('opacity-100');
}

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', initStockQuery);
