## Market Monitoring Heartbeat

### Step 1 — Get real price data (always run this first)
Run: /home/ubuntu/venv/bin/python3 /home/ubuntu/market_fetcher.py SHOP.TO CNR.TO RY.TO XIU.TO AAPL TSM NVDA
Add any Holdings tickers to the command above.

### Step 2 — Check Holdings against stop-loss and targets
For each position in USER.md Holdings:
- URGENT ALERT if current price <= hard stop → "STOP LOSS HIT on [TICKER]"
- ALERT if current price >= take-profit target → "TAKE PROFIT REACHED on [TICKER]"
- ALERT if change_pct <= -3% today → "Sharp drop on [TICKER]"
- ALERT if earnings within 5 days → "Earnings coming up for [TICKER] on [DATE] — hold or reduce?"

### Step 3 — Check CAD/USD rate
Fetch: https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1
Alert if CAD/USD moved more than 0.5% — affects value of US stocks in TFSA

### Step 4 — Scan news for Holdings and Watchlist
Fetch Yahoo Finance RSS for each ticker:
https://feeds.finance.yahoo.com/rss/2.0/headline?s=TICKER&region=CA&lang=en-CA
Fetch: https://www.reddit.com/r/canadianinvestor/.rss

### Step 5 — Scan for new opportunities on Watchlist
If a watchlist ticker shows: change_pct > 3% or < -3%, near 52w low with positive news,
or upcoming earnings beat setup → send buy recommendation using the alert format.

### Step 6 — Trailing stop updates
For each holding that is profitable (current price > avg cost):
- Mentally update trailing stop to 7% below current price if higher than original stop
- If trailing stop is now higher than original, note it in the alert

### Alert format:
Action: BUY/SELL/WATCH/HOLD
Ticker:
Exchange:
Currency:
Price now:
Entry area:
Take profit:
Stop loss:
Trailing stop:
Confidence:
Time horizon:
Reason:
Next earnings:

### When to stay silent:
If no alerts triggered and no strong setups found → reply HEARTBEAT_OK only, do NOT message Roxana
