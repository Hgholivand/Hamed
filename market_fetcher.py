#!/usr/bin/env python3
import sys
import json
from datetime import datetime, timezone
import yfinance as yf

def fetch(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        hist = t.history(period="2d")

        if hist.empty:
            return {"error": f"No data for {ticker}"}

        prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else hist['Close'].iloc[-1]
        current = hist['Close'].iloc[-1]
        change_pct = ((current - prev_close) / prev_close) * 100
        volume = int(hist['Volume'].iloc[-1])

        try:
            cal = t.calendar
            next_earnings = str(cal.get('Earnings Date', ['N/A'])[0]) if cal else 'N/A'
        except:
            next_earnings = 'N/A'

        return {
            "ticker": ticker,
            "price": round(float(current), 2),
            "prev_close": round(float(prev_close), 2),
            "change_pct": round(float(change_pct), 2),
            "volume": volume,
            "52w_high": round(float(info.year_high), 2) if hasattr(info, 'year_high') else 'N/A',
            "52w_low": round(float(info.year_low), 2) if hasattr(info, 'year_low') else 'N/A',
            "next_earnings": next_earnings,
            "currency": info.currency if hasattr(info, 'currency') else 'N/A',
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}

if __name__ == "__main__":
    tickers = sys.argv[1:] if len(sys.argv) > 1 else []
    if not tickers:
        print(json.dumps({"error": "Usage: market_fetcher.py TICKER1 TICKER2 ..."}))
        sys.exit(1)
    results = {t: fetch(t) for t in tickers}
    print(json.dumps(results, indent=2))
