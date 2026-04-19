# HEARTBEAT — Run every hour during market hours (Mon-Fri 9:30am-4pm ET)

You are Roxana's stock market AI. Every heartbeat, silently gather real data and only message if something is actionable.

## Step 1 — Check market hours
If current time (America/Toronto) is outside Mon-Fri 09:30-16:00 ET, skip steps 2-4 and print HEARTBEAT_OK.

## Step 2 — Macro context (run once per day, ~9:30am)
Run: `/home/ubuntu/venv/bin/python3 /home/ubuntu/market_fetcher.py --fred`
Note: Fed funds rate, 10Y treasury, unemployment, CPI trend. If Fed rate > 5% or 10Y rising fast, flag as risk-off environment.

## Step 3 — Market sentiment
Run: `/home/ubuntu/venv/bin/python3 /home/ubuntu/market_fetcher.py --fg`
- Score < 25: Extreme Fear — good buy zone, watch for bounces
- Score > 75: Extreme Greed — tighten stops, avoid new positions
- Note direction (improving/worsening)

## Step 4 — Holdings check
For each stock in Holdings (USER.md), run:
`/home/ubuntu/venv/bin/python3 /home/ubuntu/market_fetcher.py TICKER`

Alert immediately (Telegram chat 67371133) if ANY of:
- Price dropped below stop-loss (buy_price * 0.93)
- Price hit take-profit target (buy_price * 1.12)
- RSI > 75 (overbought, consider trimming)
- RSI < 30 (oversold, hold or add)
- MACD_BEARISH_CROSS detected
- VOLUME_SPIKE > 2x on a down day
- next_earnings within 5 days

## Step 5 — Watchlist scan
For each ticker in Watchlist (USER.md), run:
`/home/ubuntu/venv/bin/python3 /home/ubuntu/market_fetcher.py TICKER`

Alert if ANY of:
- OVERSOLD (RSI < 35) + NEAR_52W_LOW + Fear score < 35 → strong buy signal
- MACD_BULLISH_CROSS + UPTREND → momentum entry
- VOLUME_SPIKE > 3x on an up day → breakout watch
- NEAR_52W_HIGH with RSI < 65 → not yet overbought, momentum

For any watchlist ticker triggering 2+ signals, also run:
`/home/ubuntu/venv/bin/python3 /home/ubuntu/market_fetcher.py --alpha TICKER`
Include news sentiment in the alert.

## Step 6 — CAD/USD rate
Fetch: `https://www.bankofcanada.ca/valet/observations/FXCADUSD/json?recent=1`
If CAD/USD < 0.72: note FX headwind for USD-denominated stocks.
If CAD/USD > 0.76: note FX tailwind.

## Alert format (Telegram)
```
📊 ROXANA ALERT — [TICKER] [SIGNAL]
Price: $X.XX ([+/-]X.X%)
RSI: XX | Sentiment: [Bullish/Neutral/Bearish]
Signals: [list]
Action: [BUY OPPORTUNITY / SELL SIGNAL / WATCH / HOLD]
Stop-loss: $X.XX | Target: $X.XX
```

## Silence rule
If nothing triggers, print only: HEARTBEAT_OK
Do NOT send Telegram messages for routine checks.

## Trailing stop update
After each heartbeat, if a holding is up >5% from buy price, update stop-loss to (current_price * 0.93) and note it in USER.md Holdings.
