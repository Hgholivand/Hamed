#!/usr/bin/env python3
"""
market_fetcher.py — Free-tier market data for Roxana's stock agent
Usage:
    python3 market_fetcher.py TICKER1 TICKER2 ...
    python3 market_fetcher.py --fg
    python3 market_fetcher.py --insider TICKER
    python3 market_fetcher.py --alpha TICKER
    python3 market_fetcher.py --macro
    python3 market_fetcher.py --size TICKER PORTFOLIO_VALUE [SIGNALS_COUNT]
"""

import sys
import json
import urllib.request


def _load_env():
    env = {}
    try:
        for line in open("/home/ubuntu/.market_env").read().strip().split("\n"):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    except Exception:
        pass
    return env


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
        env = _load_env()
        key = env.get("FINNHUB_API_KEY", "")
        if not key:
            return {"error": "FINNHUB_API_KEY not set in /home/ubuntu/.market_env"}
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
        env = _load_env()
        key = env.get("ALPHA_VANTAGE_KEY", "")
        if not key:
            return {"error": "ALPHA_VANTAGE_KEY not set in /home/ubuntu/.market_env"}
        av_ticker = ticker.split(".")[0] if "." in ticker else ticker
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={av_ticker}&limit=10&apikey={key}"
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
                (t for t in a.get("ticker_sentiment", []) if t["ticker"] == av_ticker), None
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
            "av_ticker_used": av_ticker,
            "avg_sentiment_score": avg,
            "sentiment_label": label,
            "articles": results
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_macro():
    """Market-traded macro indicators via yfinance (free, works from EC2)."""
    try:
        import yfinance as yf

        symbols = {
            "10y_treasury_yield": "^TNX",
            "vix": "^VIX",
            "sp500": "^GSPC",
            "nasdaq": "^IXIC",
            "tsx_composite": "^GSPTSE",
            "usd_index": "DX-Y.NYB",
            "cad_usd": "CADUSD=X",
            "gold": "GC=F",
            "crude_oil": "CL=F",
        }

        results = {}
        tickers = yf.download(
            list(symbols.values()), period="2d", interval="1d",
            progress=False, auto_adjust=True
        )
        close = tickers["Close"] if "Close" in tickers.columns else tickers

        for label, sym in symbols.items():
            try:
                vals = close[sym].dropna()
                if len(vals) >= 2:
                    today_val = round(float(vals.iloc[-1]), 4)
                    prev_val = round(float(vals.iloc[-2]), 4)
                    change = round((today_val - prev_val) / prev_val * 100, 2)
                    results[label] = {"value": today_val, "change_pct": change, "symbol": sym}
                elif len(vals) == 1:
                    results[label] = {"value": round(float(vals.iloc[-1]), 4), "symbol": sym}
            except Exception as e:
                results[label] = {"error": str(e)}

        risk_flags = []
        if "vix" in results and "value" in results["vix"]:
            vix = results["vix"]["value"]
            if vix > 30:
                risk_flags.append(f"HIGH_VOLATILITY (VIX={vix})")
            elif vix < 15:
                risk_flags.append(f"LOW_VOLATILITY (VIX={vix})")
        if "10y_treasury_yield" in results and "value" in results["10y_treasury_yield"]:
            y = results["10y_treasury_yield"]["value"]
            if y > 4.5:
                risk_flags.append(f"HIGH_RATES (10Y={y}%)")
        if "cad_usd" in results and "value" in results["cad_usd"]:
            fx = results["cad_usd"]["value"]
            if fx < 0.72:
                risk_flags.append(f"WEAK_CAD (FX={fx}) — FX headwind on USD stocks")
            elif fx > 0.76:
                risk_flags.append(f"STRONG_CAD (FX={fx}) — FX tailwind on USD stocks")

        results["risk_flags"] = risk_flags
        return results
    except Exception as e:
        return {"error": str(e)}


def fetch_position_size(ticker, portfolio_cad, signals_count=2):
    """
    Suggest position size for a TFSA buy.
    portfolio_cad: total portfolio value in CAD
    signals_count: number of buy signals triggering this (1, 2, or 3+)
    """
    try:
        import yfinance as yf

        # Get current price and currency
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")
        if hist.empty:
            return {"error": f"No price data for {ticker}"}

        price_native = info.get("currentPrice") or info.get("regularMarketPrice") or float(hist["Close"].iloc[-1])
        currency = info.get("currency", "USD")

        # Convert price to CAD if USD stock
        cad_usd = 0.73  # fallback
        try:
            fx_hist = yf.Ticker("CADUSD=X").history(period="2d")
            if not fx_hist.empty:
                cad_usd = float(fx_hist["Close"].iloc[-1])
        except Exception:
            pass

        if currency == "USD":
            price_cad = round(price_native / cad_usd, 2)
            fx_note = f"USD stock: ${price_native} USD = ${price_cad} CAD (rate: {round(cad_usd, 4)})"
        else:
            price_cad = round(price_native, 2)
            fx_note = "CAD stock: no FX conversion needed"

        # Get VIX for volatility adjustment
        vix = 20.0  # fallback
        try:
            vix_hist = yf.Ticker("^VIX").history(period="2d")
            if not vix_hist.empty:
                vix = float(vix_hist["Close"].iloc[-1])
        except Exception:
            pass

        # Base allocation: 5% of portfolio per position (TFSA conservative)
        base_pct = 0.05

        # Signal strength adjustment (never exceed 5%)
        if signals_count >= 3:
            signal_pct = 0.05   # full 5% — strong conviction
        elif signals_count == 2:
            signal_pct = 0.04   # 4% — moderate conviction
        else:
            signal_pct = 0.03   # 3% — single signal, cautious

        # VIX volatility adjustment
        if vix >= 40:
            vix_mult = 0.4
            vix_note = f"EXTREME FEAR (VIX={round(vix,1)}): position halved twice"
        elif vix >= 30:
            vix_mult = 0.6
            vix_note = f"HIGH VOLATILITY (VIX={round(vix,1)}): position reduced 40%"
        elif vix >= 25:
            vix_mult = 0.8
            vix_note = f"ELEVATED VOLATILITY (VIX={round(vix,1)}): position reduced 20%"
        else:
            vix_mult = 1.0
            vix_note = f"NORMAL VOLATILITY (VIX={round(vix,1)}): no reduction"

        final_pct = round(min(signal_pct * vix_mult, base_pct), 4)
        position_cad = round(portfolio_cad * final_pct, 2)
        shares = int(position_cad / price_cad)
        actual_cost_cad = round(shares * price_cad, 2)

        stop_loss_native = round(price_native * 0.93, 2)
        target_native = round(price_native * 1.12, 2)
        stop_loss_cad = round(stop_loss_native / cad_usd, 2) if currency == "USD" else stop_loss_native
        target_cad = round(target_native / cad_usd, 2) if currency == "USD" else target_native
        max_loss_cad = round(actual_cost_cad * 0.07, 2)
        potential_gain_cad = round(actual_cost_cad * 0.12, 2)

        return {
            "ticker": ticker,
            "price_native": price_native,
            "price_cad": price_cad,
            "currency": currency,
            "fx_note": fx_note,
            "portfolio_cad": portfolio_cad,
            "signals_count": signals_count,
            "vix": round(vix, 1),
            "vix_note": vix_note,
            "allocation_pct": round(final_pct * 100, 2),
            "position_value_cad": position_cad,
            "suggested_shares": shares,
            "actual_cost_cad": actual_cost_cad,
            "stop_loss": stop_loss_native,
            "target": target_native,
            "max_loss_cad": max_loss_cad,
            "potential_gain_cad": potential_gain_cad,
            "risk_reward": f"1 : {round(potential_gain_cad / max_loss_cad, 1) if max_loss_cad else 'N/A'}"
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "Usage: market_fetcher.py TICKER1 TICKER2 ... or --fg or --insider TICKER or --alpha TICKER or --macro or --size TICKER PORTFOLIO_CAD [SIGNALS]"})) 
        sys.exit(1)
    if args[0] == "--insider" and len(args) == 2:
        print(json.dumps(fetch_insider_trades(args[1]), indent=2))
    elif args[0] == "--alpha" and len(args) == 2:
        print(json.dumps(fetch_alpha_vantage_sentiment(args[1]), indent=2))
    elif args[0] == "--size" and len(args) >= 3:
        signals = int(args[3]) if len(args) >= 4 else 2
        print(json.dumps(fetch_position_size(args[1], float(args[2]), signals), indent=2))
    elif args == ["--fg"]:
        print(json.dumps({"fear_and_greed": fetch_fear_greed()}, indent=2))
    elif args == ["--macro"]:
        print(json.dumps({"macro": fetch_macro()}, indent=2))
    else:
        print(json.dumps({t: fetch(t) for t in args}, indent=2))
