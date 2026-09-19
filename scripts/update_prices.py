#!/usr/bin/env python3
"""
Refreshes prices.json with real closing stock prices for the Paper Trader
game. Runs on a schedule via .github/workflows/update-prices.yml.

Design notes:
- No API key required. Tries Yahoo Finance's public chart endpoint first
  (the same one the popular `yfinance` library uses under the hood), and
  falls back to Stooq's free CSV endpoint per-ticker if Yahoo fails for
  that symbol.
- If BOTH sources fail for a ticker, that ticker is just left unchanged
  (its old price stays) rather than failing the whole run -- a stale price
  is much better than a broken site.
- Never raises on a single bad ticker; always writes back whatever it did
  manage to update, and prints a summary of what succeeded/failed so a
  failed run is easy to spot in the Actions log.
"""

import json
import sys
import time
import urllib.request
import urllib.error

PRICES_FILE = "prices.json"

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "META", "TSLA", "NVDA", "AMD",
    "DIS", "NFLX", "RBLX", "SPOT", "NTDOY", "TTWO", "WBD",
    "AMZN", "NKE", "MCD", "SBUX", "KO", "CMG", "PEP",
    "DUOL", "CAVA", "CELH", "ELF", "RDDT", "HOOD", "ONON", "SOFI", "PLTR",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch_yahoo(ticker):
    """Primary source: Yahoo Finance's public (unauthenticated) chart API."""
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + ticker + "?interval=1d&range=5d"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    result = payload.get("chart", {}).get("result")
    if not result:
        return None
    meta = result[0].get("meta", {})
    price = meta.get("regularMarketPrice")
    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None:
        return None
    return {"price": float(price), "prevClose": float(prev_close) if prev_close else None}


def fetch_stooq(ticker):
    """Fallback source: Stooq's free CSV quote endpoint."""
    url = "https://stooq.com/q/l/?s=" + ticker.lower() + ".us&f=sd2t2ohlcv&h&e=csv"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8")
    lines = text.strip().splitlines()
    if len(lines) < 2:
        return None
    parts = lines[1].split(",")
    # Symbol,Date,Time,Open,High,Low,Close,Volume
    try:
        close = float(parts[6])
    except (ValueError, IndexError):
        return None
    if close <= 0:
        return None
    return {"price": close, "prevClose": None}


def fetch_price(ticker):
    for fetcher in (fetch_yahoo, fetch_stooq):
        try:
            result = fetcher(ticker)
            if result and result.get("price"):
                return result
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
            continue
    return None


def main():
    try:
        with open(PRICES_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    today_date_label = time.strftime("%b %-d, %Y")
    today_full_label = today_date_label + " market close"

    updated, unchanged, failed = [], [], []

    for ticker in TICKERS:
        result = fetch_price(ticker)
        entry = data.get(ticker, {"history": []})
        old_price = entry.get("price")

        if result is None:
            # Both sources failed -- leave this ticker exactly as it was.
            failed.append(ticker)
            data[ticker] = entry
            continue

        new_price = round(result["price"], 2)
        # If the source gave us a previous close, use it; otherwise fall
        # back to "yesterday's price becomes today's prevClose", same
        # logic the original Claude-based scheduler used.
        prev_close = result.get("prevClose")
        prev_close = round(prev_close, 2) if prev_close else (old_price if old_price else new_price)

        if old_price is not None and abs(new_price - old_price) < 0.0001:
            unchanged.append(ticker)
        else:
            updated.append(ticker)

        entry["price"] = new_price
        entry["prevClose"] = prev_close
        history = entry.get("history", [])
        history.append({"d": today_date_label, "c": new_price})
        entry["history"] = history[-60:]
        entry["updatedAt"] = today_full_label
        data[ticker] = entry

        time.sleep(0.25)  # be polite to the free endpoints

    with open(PRICES_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print("Updated (" + str(len(updated)) + "): " + ", ".join(updated))
    print("Unchanged (" + str(len(unchanged)) + "): " + ", ".join(unchanged))
    if failed:
        print("FAILED, left as-is (" + str(len(failed)) + "): " + ", ".join(failed))

    if len(failed) == len(TICKERS):
        # Every single ticker failed -- almost certainly a network or
        # source-format problem worth surfacing as a failed Actions run,
        # rather than silently "succeeding" with a no-op.
        print("All tickers failed -- treating this as a failed run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
