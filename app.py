"""
Tiny Flask micro-service that returns the latest market price
for a US equity or ETF using Yahoo Finance’s public JSON endpoint.

Endpoint:
    GET /quote?ticker=MSFT
    → { "price": 225.37, "timestamp": "2025-07-09T15:12:04-04:00" }
"""

import time
import requests
from flask import Flask, request, jsonify, abort

# --------------------------------------------
# Config
# --------------------------------------------
YF_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={}"
CACHE_TTL = 60          # seconds to reuse last quote for same symbol

# --------------------------------------------
# Globals
# --------------------------------------------
app = Flask(__name__)
_cache: dict[str, tuple[float, float]] = {}   # { "AAPL": (price, unix_ts) }

# --------------------------------------------
# Routes
# --------------------------------------------
@app.get("/quote")
def quote() -> tuple[dict, int]:
    """Return latest price for ?ticker=XYZ in JSON."""
    ticker = request.args.get("ticker", "").upper()

    # basic validation
    if not ticker.isalpha():
        abort(400, "Ticker must be alphabetic characters only.")

    # serve from cache if < CACHE_TTL seconds old
    if ticker in _cache and time.time() - _cache[ticker][1] < CACHE_TTL:
        price, _ = _cache[ticker]
        return jsonify({
            "price": price,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }), 200

    # fetch from Yahoo Finance
    resp = requests.get(YF_URL.format(ticker), timeout=3)
    if resp.status_code != 200:
        abort(502, "Upstream request failed.")

    data = resp.json()["quoteResponse"]["result"]
    if not data:
        abort(404, f"Ticker {ticker} not found.")

    price = data[0]["regularMarketPrice"]

    # cache and return
    _cache[ticker] = (price, time.time())
    return jsonify({
        "price": price,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
    }), 200


# --------------------------------------------
# For local testing:  python app.py
# --------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

