# TOOLS — Free intelligence sources

## Python data tools (run via venv)
All commands: `/home/ubuntu/venv/bin/python3 /home/ubuntu/market_fetcher.py`

| Command | Data returned | Limit |
|---------|--------------|-------|
| `TICKER [TICKER...]` | price, change%, RSI, MACD, SMA20/50, volume spike, 52w range, ta_signals, next earnings | Unlimited |
| `--fg` | Fear & Greed score + direction | Unlimited |
| `--insider TICKER` | Insider buys/sells last 30d (Finnhub) | 60 calls/min |
| `--alpha TICKER` | News sentiment score + headlines | 25 calls/day |
| `--fred` | Fed rate, CPI, unemployment, 10Y, GDP | Unlimited |

**Ticker format notes:**
- Yahoo Finance / yfinance: use `SHOP.TO`, `CNR.TO` for TSX
- Alpha Vantage `--alpha`: automatically strips `.TO` — use original format, e.g. `--alpha SHOP.TO`
- Finnhub `--insider`: US tickers only (AAPL, NVDA, etc.) — no TSX support

## RSS feeds (zero API credits)
- Yahoo Finance: `https://finance.yahoo.com/rss/topstories`
- TSX news: `https://www.tsx.com/rss/news`
- Reuters business: `https://feeds.reuters.com/reuters/businessNews`
- Globe & Mail markets: `https://www.theglobeandmail.com/investing/markets/?service=rss`
- Reddit r/stocks: `https://www.reddit.com/r/stocks/.rss`
- Reddit r/investing: `https://www.reddit.com/r/investing/.rss`
- SEC EDGAR Form 4 (insider): `https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&dateb=&owner=include&count=10&output=atom`

## Free APIs (no key)
- Fear & Greed: `https://api.alternative.me/fng/?limit=2&format=json`
- Bank of Canada FX: `https://www.bankofcanada.ca/valet/observations/FXCADUSD/json?recent=1`
- FRED macro: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS` (and other series)

## Search policy (use in order)
1. RSS feeds — always free, always first
2. `--alpha TICKER` — for confirmed signals needing news context
3. Google search — for breaking news not in RSS
4. Tavily — only for high-impact events (earnings, M&A, macro shock)

## Key series IDs for FRED
- `FEDFUNDS` — Fed funds rate
- `CPIAUCSL` — CPI (inflation)
- `UNRATE` — Unemployment rate
- `GS10` — 10-year Treasury yield
- `A191RL1Q225SBEA` — US real GDP growth
- `DEXCAUS` — CAD/USD exchange rate (daily)
