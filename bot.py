import datetime
import time
import pandas as pd
import pytz
import requests
import yfinance as yf

# --- Configuration ---
TELEGRAM_TOKEN = "8978761813:AAHnREdrVRkGuOFRJmSEUo9TMf8xWmywQQ"
CHAT_ID = "6514656533"

INDICES = {
    "US Tech 100 Fut": "NQ=F",
    "Dow Jones Fut": "YM=F",
    "DAX 40 Fut": "FDAX=F",
    "FTSE 100 Fut": "Z=F",
    "CAC 40 Fut": "FCE=F",
    "GIFT Nifty Fut": "^NSEI",
    "Nikkei 225 Fut": "NK=F",
    "Hang Seng Fut": "HSI=F",
    "China A50 Fut": "CN=F",
    "Australia 200 Fut": "AP=F",
    "Straits Times Fut": "ST=F",
    "KOSPI 200 Fut": "KM=F",
    "Taiwan Fut": "TW=F",
}


def get_nearest_price(df, target_hour, target_minute=0):
    if df is None or df.empty:
        return None
    try:
        ist = pytz.timezone("Asia/Kolkata")
        latest_date = df.index[-1].date()
        target_dt = ist.localize(
            datetime.datetime.combine(
                latest_date, datetime.time(target_hour, target_minute)
            )
        )

        start_window = target_dt - datetime.timedelta(minutes=30)
        end_window = target_dt + datetime.timedelta(minutes=30)

        sub = df[(df.index >= start_window) & (df.index <= end_window)]
        if sub.empty:
            return None

        closest_idx = (sub.index - target_dt).abs().argmin()
        price = sub["Close"].iloc[closest_idx]
        if isinstance(price, pd.Series):
            price = price.iloc[0]
        return float(price)
    except Exception:
        return None


def fetch_hourly_futures_data(ticker):
    try:
        # Yahoo Finance IP block এড়াতে রিকোয়েস্ট পাঠানো
        df = yf.download(
            ticker, period="2d", interval="2m", progress=False, timeout=10
        )
        if df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.ffill()

        ist = pytz.timezone("Asia/Kolkata")
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC").tz_convert(ist)
        else:
            df.index = df.index.tz_convert(ist)

        p_0700 = get_nearest_price(df, 7, 0)
        p_0800 = get_nearest_price(df, 8, 0)
        p_0900 = get_nearest_price(df, 9, 0)

        # অন্তত ২টি প্রাইস পেলেই ক্যালকুলেশন করবে
        diff_7_to_8 = (
            (p_0800 - p_0700)
            if (p_0700 is not None and p_0800 is not None)
            else 0.0
        )
        diff_8_to_9 = (
            (p_0900 - p_0800)
            if (p_0800 is not None and p_0900 is not None)
            else 0.0
        )
        total_diff = (
            (p_0900 - p_0700)
            if (p_0700 is not None and p_0900 is not None)
            else (diff_7_to_8 + diff_8_to_9)
        )

        if p_0900 is None:
            return None

        return {
            "diff_1": diff_7_to_8,
            "diff_2": diff_8_to_9,
            "total_diff": total_diff,
        }
    except Exception:
        return None


def generate_hourly_report():
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    if now.weekday() in [5, 6]:
        return "⚠️ Aj Shoni/Robi bar, Market bondho."

    today_date = now.strftime("%d %b %Y")
    msg = f"📊 **Futures Market 1-Hour Breakdown** ({today_date})\n"
    msg += f"📍 **Sokal 07:00 AM -> 09:00 AM Movement**\n\n"

    for name, ticker in INDICES.items():
        data = fetch_hourly_futures_data(ticker)
        time.sleep(1.2)  # Yahoo Finance Rate-limit প্রতিরোধ করতে ১.২ সেকেন্ড বিরতি

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
    
