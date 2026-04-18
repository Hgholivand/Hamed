# TOOLS.md — Market Intelligence Sources

## Free RSS Feeds (fetch these before using any search credits)

### Yahoo Finance News (per ticker)
https://feeds.finance.yahoo.com/rss/2.0/headline?s=TICKER&region=CA&lang=en-CA

### Canadian Market News
- TSX news: https://www.tsx.com/rss/news
- Globe & Mail markets: https://www.theglobeandmail.com/investing/rss/

### US Filings (SEC EDGAR — instant, free)
- Latest filings: https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&dateb=&owner=include&count=20&output=atom
- Company-specific: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TICKER&type=8-K&output=atom

### Canadian Filings (SEDAR+)
- https://www.sedarplus.ca/csa-party/party/search.html (search by company)

### Sentiment & Social
- Reddit r/canadianinvestor: https://www.reddit.com/r/canadianinvestor/.rss
- Reddit r/stocks: https://www.reddit.com/r/stocks/.rss
- Reddit r/investing: https://www.reddit.com/r/investing/.rss
- StockTwits (per ticker): https://api.stocktwits.com/api/2/streams/symbol/TICKER.json

### Earnings Calendar
- Earnings Whispers: https://www.earningswhispers.com/rss/earningstodayrss.asp

### Macro & Economic
- Bank of Canada (CAD/USD, rate decisions): https://www.bankofcanada.ca/rss/
- Bank of Canada exchange rates API: https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=5

## Free APIs (no cost)

### Price Data — yfinance (Python, no API key)
Run: /home/ubuntu/venv/bin/python3 /home/ubuntu/market_fetcher.py TICKER
Returns: current price, day change %, volume, 52w high/low, next earnings date

### Bank of Canada API
GET https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1
Returns: latest CAD/USD rate

### Finnhub (free tier — 60 calls/min)
Earnings calendar: https://finnhub.io/api/v1/calendar/earnings?from=DATE&to=DATE&token=API_KEY

## Search Credit Priority
1. Fetch RSS feeds first (zero credits)
2. Use Google search if RSS reveals something worth investigating
3. Use Tavily only for deep research on high-impact events
