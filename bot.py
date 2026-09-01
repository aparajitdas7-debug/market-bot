import datetime
import time
import pytz
import requests

# --- Configuration ---
TELEGRAM_TOKEN = "8978761813:AAHnREdrVRkGuOFRJmSEUo9TMf8xWmywQQ"
CHAT_ID = "6514656533"

# Yahoo Finance Active Valid Tickers
INDICES = {
    "US Tech 100 Fut": "NQ=F",
    "Dow Jones Fut": "YM=F",
    "DAX 40": "^GDAXI",
    "FTSE 100": "^FTSE",
    "CAC 40": "^FCHI",
    "Nifty 50 (GIFT Proxy)": "^NSEI",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "China Shanghai": "000001.SS",
    "Australia 200": "^AXJO",
    "Straits Times": "^STI",
    "KOSPI 200": "^KS11",
    "Taiwan Index": "^TWII",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_index_data(ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=15m"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None
        
        data = res.json()
        result = data.get("chart", {}).get("result")
        if not result:
            return None
        
        meta = result[0].get("meta", {})
        timestamps = result[0].get("timestamp", [])
        indicators = result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])

        ist = pytz.timezone("Asia/Kolkata")
        candles = []
        if timestamps and indicators:
            for ts, close in zip(timestamps, indicators):
                if close is not None:
                    dt = datetime.datetime.fromtimestamp(ts, tz=pytz.utc).astimezone(ist)
                    candles.append((dt, float(close)))

        if candles:
            candles.sort(key=lambda x: x[0])
            latest_date = candles[-1][0].date()

            t_0700 = ist.localize(datetime.datetime.combine(latest_date, datetime.time(7, 0)))
            t_0800 = ist.localize(datetime.datetime.combine(latest_date, datetime.time(8, 0)))
            t_0900 = ist.localize(datetime.datetime.combine(latest_date, datetime.time(9, 0)))

            def find_closest(target_dt):
                valid = [c for c in candles if abs((c[0] - target_dt).total_seconds()) <= 7200]
                return min(valid, key=lambda x: abs((x[0] - target_dt).total_seconds()))[1] if valid else None

            p_0700 = find_closest(t_0700)
            p_0800 = find_closest(t_0800)
            p_0900 = find_closest(t_0900)

            if p_0700 is not None or p_0800 is not None or p_0900 is not None:
                diff_1 = (p_0800 - p_0700) if (p_0700 and p_0800) else 0.0
                diff_2 = (p_0900 - p_0800) if (p_0800 and p_0900) else 0.0
                p_start = p_0700 if p_0700 else p_0800
                p_end = p_0900 if p_0900 else candles[-1][1]
                total_diff = (p_end - p_start) if (p_end and p_start) else (diff_1 + diff_2)
                return {"mode": "hourly", "diff_1": diff_1, "diff_2": diff_2, "total_diff": total_diff}

        current_price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

        if current_price is not None and prev_close is not None:
            diff = current_price - prev_close
            return {"mode": "summary", "diff": diff, "price": current_price}

        return None
    except Exception:
        return None

def generate_hourly_report():
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    if now.weekday() in [5, 6]:
        return "⚠️ Aj Shoni/Robi bar, Market bondho."

    today_date = now.strftime("%d %b %Y")
    msg = f"📊 **Global Market & Futures Breakdown** ({today_date})\n\n"

    for name, ticker in INDICES.items():
        data = fetch_index_data(ticker)
        time.sleep(0.3)

        if data:
            if data["mode"] == "hourly":
                emoji1 = "🟢" if data["diff_1"] >= 0 else "🔴"
                emoji2 = "🟢" if data["diff_2"] >= 0 else "🔴"
                emoji_tot = "🟢" if data["total_diff"] >= 0 else "🔴"

                msg += f"🔹 **{name}**\n"
                msg += f"  ├ 07:00 ➔ 08:00: {emoji1} {data['diff_1']:+.2f} pts\n"
                msg += f"  ├ 08:00 ➔ 09:00: {emoji2} {data['diff_2']:+.2f} pts\n"
                msg += f"  └ Total Change: {emoji_tot} {data['total_diff']:+.2f} pts\n\n"
            else:
                emoji = "🟢" if data["diff"] >= 0 else "🔴"
                msg += f"🔹 **{name}** (Live Overview)\n"
                msg += f"  └ Change: {emoji} {data['diff']:+.2f} pts (Price: {data['price']:.2f})\n\n"
        else:
            msg += f"⚠️ **{name}**: Data paowa jayni\n\n"

    return msg

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

if __name__ == "__main__":
    report_text = generate_hourly_report()
    send_telegram(report_text)
        
