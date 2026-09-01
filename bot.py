import datetime
import time
import pytz
import requests

# --- Configuration ---
TELEGRAM_TOKEN = "8978761813:AAHNrEdRRVrKGuOfRJmSEUo9TMf8xWmywQQ"
CHAT_ID = "6514656533"

INDICES = {
    "US Tech 100 Fut": "NQ=F",
    "Dow Jones Fut": "YM=F",
    "DAX 40 Fut": "FDAX=F",
    "FTSE 100 Fut": "Z=F",
    "CAC 40 Fut": "FCE=F",
    "GIFT Nifty Fut": "IN=F",
    "Nikkei 225 Fut": "NK=F",
    "Hang Seng Fut": "HSI=F",
    "China A50 Fut": "CN=F",
    "Australia 200 Fut": "AP=F",
    "Straits Times Fut": "ST=F",
    "KOSPI 200 Fut": "KM=F",
    "Taiwan Fut": "TW=F",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_index_data(ticker):
    # Yahoo Finance Direct Chart API call
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=15m"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None
        
        data = res.json()
        result = data.get("chart", {}).get("result")
        if not result:
            return None
        
        timestamps = result[0].get("timestamp", [])
        indicators = result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
        
        if not timestamps or not indicators:
            return None

        ist = pytz.timezone("Asia/Kolkata")
        
        candles = []
        for ts, close in zip(timestamps, indicators):
            if close is not None:
                dt = datetime.datetime.fromtimestamp(ts, tz=pytz.utc).astimezone(ist)
                candles.append((dt, close))
        
        if not candles:
            return None

        latest_date = candles[-1][0].date()

        t_0700 = ist.localize(datetime.datetime.combine(latest_date, datetime.time(7, 0)))
        t_0800 = ist.localize(datetime.datetime.combine(latest_date, datetime.time(8, 0)))
        t_0900 = ist.localize(datetime.datetime.combine(latest_date, datetime.time(9, 0)))

        def find_closest(target_dt):
            valid = [c for c in candles if abs((c[0] - target_dt).total_seconds()) <= 3600]
            if not valid:
                return None
            return min(valid, key=lambda x: abs((x[0] - target_dt).total_seconds()))[1]

        p_0700 = find_closest(t_0700)
        p_0800 = find_closest(t_0800)
        p_0900 = find_closest(t_0900)

        if p_0700 is None and p_0800 is None and p_0900 is None:
            return None

        diff_1 = (p_0800 - p_0700) if (p_0700 is not None and p_0800 is not None) else 0.0
        diff_2 = (p_0900 - p_0800) if (p_0800 is not None and p_0900 is not None) else 0.0
        
        p_start = p_0700 if p_0700 is not None else p_0800
        p_end = p_0900 if p_0900 is not None else candles[-1][1]
        
        total_diff = (p_end - p_start) if (p_end is not None and p_start is not None) else (diff_1 + diff_2)

        return {
            "diff_1": diff_1,
            "diff_2": diff_2,
            "total_diff": total_diff
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def generate_hourly_report():
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    if now.weekday() in [5, 6]:
        return "⚠️ Aj Shoni/Robi bar, Market bondho."

    today_date = now.strftime("%d %b %Y")
    msg = f"📊 **Futures Market 1-Hour Breakdown** ({today_date})\n"
    msg += f"📍 **Sokal 07:00 AM -> 09:00 AM Movement**\n\n"

    for name, ticker in INDICES.items():
        data = fetch_index_data(ticker)
        time.sleep(0.5)

        if data:
            emoji1 = "🟢" if data["diff_1"] >= 0 else "🔴"
            emoji2 = "🟢" if data["diff_2"] >= 0 else "🔴"
            emoji_tot = "🟢" if data["total_diff"] >= 0 else "🔴"

            msg += f"🔹 **{name}**\n"
            msg += f"  ├ 07:00 ➔ 08:00: {emoji1} {data['diff_1']:+.2f} pts\n"
            msg += f"  ├ 08:00 ➔ 09:00: {emoji2} {data['diff_2']:+.2f} pts\n"
            msg += f"  └ Total Change: {emoji_tot} {data['total_diff']:+.2f} pts\n\n"
        else:
            msg += f"⚠️ **{name}**: Data paowa jayni / Market bondho\n\n"

    return msg

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

if __name__ == "__main__":
    report_text = generate_hourly_report()
    send_telegram(report_text)
    
