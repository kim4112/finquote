import time, requests, traceback           # add traceback
from flask import Flask, request, jsonify, abort

YF_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; finquote/1.0)"}  # NEW
CACHE_TTL = 60

app = Flask(__name__)
_cache = {}                                # simplified type hint

@app.get("/quote")
def quote():
    ticker = request.args.get("ticker", "").upper()
    if not ticker.isalpha():
        abort(400, "Ticker must be alphabetic")

    if ticker in _cache and time.time() - _cache[ticker][1] < CACHE_TTL:
        price, _ = _cache[ticker]
        return jsonify({"price": price,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")})

    # ---------- NEW: surround Yahoo call with try/except -------------
    try:
        r = requests.get(YF_URL.format(ticker), headers=HEADERS, timeout=3)
        r.raise_for_status()                       # raise if 4xx / 5xx
        result = r.json()["quoteResponse"]["result"]
        if not result:
            abort(404, f"{ticker} not found")
        price = result[0]["regularMarketPrice"]
    except Exception as e:
        print("Yahoo fetch failed:", e)            # visible in Render logs
        print(traceback.format_exc())
        abort(502, "Upstream request failed")

    _cache[ticker] = (price, time.time())
    return jsonify({"price": price,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
