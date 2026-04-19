#!/usr/bin/env python3
"""
market_fetcher.py — Free-tier market data for Roxana's stock agent
Usage:
    python3 market_fetcher.py TICKER1 TICKER2 ...
    python3 market_fetcher.py --fg
    python3 market_fetcher.py --insider TICKER
    python3 market_fetcher.py --alpha TICKER
    python3 market_fetcher.py --fred
"""

import sys
import json
import urllib.request


def fetch(ticker):
    try:
        import yfinance as yf
        import pandas_ta as ta

        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")

        if hist.empty:
            return {"error": f"No data for {ticker}"}

        price = info.get("currentPrice") or info.get("regularMarketPrice") or float(hist["Close"].iloc[-1])
        prev_close = info.get("previousClose") or float(hist["Close"].iloc[-2])
        change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0

        volume = int(hist["Volume"].iloc[-1])
        avg_volume = int(hist["Volume"].mean())
        volume_spike = round(volume / avg_volume, 2) if avg_volume else 1.0

        close = hist["Close"]
        rsi_series = ta.rsi(close, length=14)
        rsi = round(float(rsi_series.iloc[-1]), 1) if rsi_series is not None and not rsi_series.empty else None

        sma20 = round(float(close.rolling(20).mean().iloc[-1]), 2)
        sma50 = round(float(close.rolling(50).mean().iloc[-1]), 2) if len(close) >= 50 else None

        high_52w = info.get("fiftyTwoWeekHigh")
        low_52w = info.get("fiftyTwoWeekLow")
        pct_from_high = round((price - high_52w) / high_52w * 100, 1) if high_52w else None
        pct_from_low = round((price - low_52w) / low_52w * 100, 1) if low_52w else None

        # MACD crossover detection
        macd_df = ta.macd(close)
        macd_signal = None
        if macd_df is not None and not macd_df.empty:
            macd_col = [c for c in macd_df.columns if "MACD_" in c and "MACDs" not in c and "MACDh" not in c]
            signal_col = [c for c in macd_df.columns if "MACDs_" in c]
            if macd_col and signal_col:
                m = float(macd_df[macd_col[0]].iloc[-1])
                s = float(macd_df[signal_col[0]].iloc[-1])
                m_prev = float(macd_df[macd_col[0]].iloc[-2])
                s_prev = float(macd_df[signal_col[0]].iloc[-2])
                if m_prev < s_prev and m > s:
                    macd_signal = "MACD_BULLISH_CROSS"
                elif m_prev > s_prev and m < s:
                    macd_signal = "MACD_BEARISH_CROSS"

        ta_signals = []
        if rsi is not None:
            if rsi < 35:
                ta_signals.append("OVERSOLD")
            elif rsi > 70:
                ta_signals.append("OVERBOUGHT")
        if macd_signal:
            ta_signals.append(macd_signal)
        if sma50 and price > sma20 > sma50:
            ta_signals.append("UPTREND")
        elif sma50 and price < sma20 < sma50:
            ta_signals.append("DOWNTREND")
        if volume_spike >= 2.0:
            ta_signals.append(f"VOLUME_SPIKE_{volume_spike}x")
        if high_52w and pct_from_high is not None and pct_from_high > -5:
            ta_signals.append("NEAR_52W_HIGH")
        if low_52w and pct_from_low is not None and pct_from_low < 10:
            ta_signals.append("NEAR_52W_LOW")

        # Next earnings date
        cal = stock.calendar
        next_earnings = None
        if cal is not None and not cal.empty:
            try:
                dates = cal.get("Earnings Date") or cal.iloc[0]
                if hasattr(dates, "iloc"):
                    next_earnings = str(dates.iloc[0].date())
                else:
                    next_earnings = str(dates)
            except Exception:
                pass

        currency = info.get("currency", "USD")

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "change_pct": change_pct,
            "currency": currency,
            "volume": volume,
            "volume_spike_x": volume_spike,
            "rsi": rsi,
            "sma20": sma20,
            "sma50": sma50,
            "52w_high": high_52w,
            "52w_low": low_52w,
            "pct_from_52w_high": pct_from_high,
            "pct_from_52w_low": pct_from_low,
            "ta_signals": ta_signals,
            "next_earnings": next_earnings,
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def fetch_fear_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=2&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        today = data["data"][0]
        yesterday = data["data"][1]
        score = int(today["value"])
        prev = int(yesterday["value"])
        return {
            "score": score,
            "rating": today["value_classification"],
            "previous_close": prev,
            "direction": "improving" if score > prev else "worsening",
            "note": "Crypto-correlated but reliable market sentiment proxy"
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_insider_trades(ticker):
    try:
        key = open("/home/ubuntu/.market_env").read().strip().split("=")[1]
        url = f"https://finnhub.io/api/v1/stock/insider-transactions?symbol={ticker}&token={key}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        txns = data.get("data", [])[:5]
        results = []
        for tx in txns:
            results.append({
                "name": tx.get("name"),
                "share": tx.get("share"),
                "change": tx.get("change"),
                "transaction_price": tx.get("transactionPrice"),
                "transaction_code": tx.get("transactionCode"),
                "date": tx.get("transactionDate")
            })
        buys = [t for t in results if t["change"] and t["change"] > 0]
        sells = [t for t in results if t["change"] and t["change"] < 0]
        return {
            "ticker": ticker,
            "recent_insider_buys": len(buys),
            "recent_insider_sells": len(sells),
            "signal": "INSIDER BUYING" if len(buys) > len(sells) else ("INSIDER SELLING" if len(sells) > len(buys) else "neutral"),
            "transactions": results
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_alpha_vantage_sentiment(ticker):
    """News sentiment via Alpha Vantage free tier (25 calls/day, no card needed)."""
    try:
        env = {}
        for line in open("/home/ubuntu/.market_env").read().strip().split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
        key = env.get("ALPHA_VANTAGE_KEY", "")
        if not key:
            return {"error": "ALPHA_VANTAGE_KEY not set in /home/ubuntu/.market_env"}
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&limit=10&apikey={key}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        if "feed" not in data:
            return {"error": data.get("Note", data.get("Information", "No feed returned"))}
        articles = data["feed"][:5]
        results = []
        overall_scores = []
        for a in articles:
            ticker_sentiment = next(
                (t for t in a.get("ticker_sentiment", []) if t["ticker"] == ticker), None
            )
            score = float(ticker_sentiment["ticker_sentiment_score"]) if ticker_sentiment else 0.0
            overall_scores.append(score)
            results.append({
                "title": a.get("title"),
                "source": a.get("source"),
                "time": a.get("time_published", "")[:8],
                "overall_sentiment": a.get("overall_sentiment_label"),
                "ticker_score": round(score, 3),
            })
        avg = round(sum(overall_scores) / len(overall_scores), 3) if overall_scores else 0
        label = "Bullish" if avg > 0.15 else ("Bearish" if avg < -0.15 else "Neutral")
        return {
            "ticker": ticker,
            "avg_sentiment_score": avg,
            "sentiment_label": label,
            "articles": results
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_fred_macro():
    """US macro indicators from FRED (free, no API key required)."""
    try:
        series = {
            "fed_funds_rate": "FEDFUNDS",
            "cpi_yoy": "CPIAUCSL",
            "unemployment": "UNRATE",
            "10y_treasury": "GS10",
            "us_gdp_growth": "A191RL1Q225SBEA",
        }
        results = {}
        for label, sid in series.items():
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                lines = r.read().decode().strip().split("\n")
            for line in reversed(lines[1:]):
                parts = line.split(",")
                if len(parts) == 2 and parts[1].strip() not in (".", ""):
                    results[label] = {"date": parts[0], "value": parts[1].strip()}
                    break
        return results
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "Usage: market_fetcher.py TICKER1 TICKER2 ... or --fg or --insider TICKER or --alpha TICKER or --fred"}))
        sys.exit(1)
    if args[0] == "--insider" and len(sys.argv) == 3:
        print(json.dumps(fetch_insider_trades(sys.argv[2]), indent=2))
    elif args[0] == "--alpha" and len(sys.argv) == 3:
        print(json.dumps(fetch_alpha_vantage_sentiment(sys.argv[2]), indent=2))
    elif args == ["--fg"]:
        print(json.dumps({"fear_and_greed": fetch_fear_greed()}, indent=2))
    elif args == ["--fred"]:
        print(json.dumps({"macro": fetch_fred_macro()}, indent=2))
    else:
        print(json.dumps({t: fetch(t) for t in args}, indent=2))
