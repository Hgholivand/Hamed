# GRADING — Self-evaluation protocol

Every time you generate a BUY OPPORTUNITY or SELL SIGNAL alert, you must also log it.
Every heartbeat, check if any logged recommendations are 30+ days old and grade them.

---

## Step 1 — Log every recommendation

When you send a BUY OPPORTUNITY or SELL SIGNAL Telegram alert, immediately append to
`/home/ubuntu/.openclaw/workspace/memory/recommendations.md` under **Active Recommendations**:

```
| YYYY-MM-DD | TICKER | BUY/SELL | $price | RSI=xx | sentiment=Bullish/Neutral/Bearish | key signals |
```

Example:
```
| 2026-04-19 | SHOP.TO | BUY | $112.40 | RSI=32 | sentiment=Bullish | OVERSOLD+MACD_BULLISH_CROSS+FG=27 |
```

---

## Step 2 — Grade old recommendations (30-day lookback)

During each heartbeat, scan **Active Recommendations** for entries older than 30 days.
For each one:
1. Run `market_fetcher.py TICKER` to get current price
2. Calculate return: `(current_price - entry_price) / entry_price * 100`
3. Grade:
   - BUY signal: return > +5% → WIN | -5% to +5% → NEUTRAL | < -5% → LOSS
   - SELL signal: return < -5% → WIN (avoided loss) | > +5% → LOSS (missed gain)
4. Move the row from Active to **Graded Recommendations** with outcome columns filled
5. Update **Performance Stats** totals

---

## Step 3 — Apply learnings

After grading, recalibrate your alert thresholds:

| Win rate | Action |
|----------|--------|
| < 40% | Require 3+ signals before alerting (raise bar) |
| 40–60% | Normal: require 2+ signals |
| > 60% | You can alert on strong single signals (lower bar) |

Also note which signal combinations have the best track record and prefer those.
Log a one-line insight in `memory/market-notes.md` after each grading batch.

---

## Step 4 — Monthly summary (first heartbeat of each month)

Send a Telegram message to Roxana (chat 67371133):

```
📊 MONTHLY PERFORMANCE REPORT
Recommendations graded: X
Wins: X | Losses: X | Neutral: X
Win rate: XX%
Best signal combo: [e.g. OVERSOLD+MACD_BULLISH_CROSS]
Worst performer: [ticker if any]
Threshold: [current alert threshold]
```
