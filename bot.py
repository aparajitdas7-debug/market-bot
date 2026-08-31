import datetime
import pandas as pd
import pytz
import requests
import yfinance as yf

# --- Configuration ---
TELEGRAM_TOKEN = "8978761813:AAHNrEdRRVrKGuOfRJmSEUo9TMf8xWmywQQ"  # Apnar Bot Token boshant
CHAT_ID = "6514656533"  # Apnar Telegram Chat ID boshant

# Sob kota international futures index-er ticker list
INDICES = {
    "US Tech 100 Fut": "NQ=F",
    "Dow Jones Fut": "YM=F",
    "DAX 40 Fut": "FDAX=F",
    "FTSE 100 Fut": "Z=F",
    "CAC 40 Fut": "FCE=F",
    "GIFT Nifty Fut": "NIFTY_F1.NS",
    "Nikkei 225 Fut": "NK=F",
    "Hang Seng Fut": "HSI=F",
    "China A50 Fut": "CN=F",
    "Australia 200 Fut": "AP=F",
    "Straits Times Fut": "ST=F",
    "KOSPI 200 Fut": "KM=F",
    "Taiwan Fut": "TWM=F",
}


def get_price_at_time(df, start_t, end_t):
    """Nirdisto somoyer madhye price filter kore out kore"""
    filtered = df.between_time(start_t, end_t)
    if filtered.empty:
        return None
    return float(filtered["Close"].iloc[-1])


def fetch_hourly_futures_data(ticker):
    try:
        # Timeout 5 sec rakha hoyeche jate code stuck na hoy
        df = yf.download(
            ticker, period="1d", interval="1m", progress=False, timeout=5
        )

        if df.empty:
            return None

        # MultiIndex columns handle kora
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.ffill()

        # IST Timezone setup
        ist = pytz.timezone("Asia/Kolkata")
        df.index = df.index.tz_convert(ist)

        # 07:00, 08:00 ebong 09:00 AM-er price ber kora
        p_0700 = get_price_at_time(df, "06:55", "07:05")
        p_0800 = get_price_at_time(df, "07:55", "08:05")
        p_0900 = get_price_at_time(df, "08:55", "09:05")

        if p_0700 is None or p_0800 is None or p_0900 is None:
            return None

        # Point differences calculation
        diff_7_to_8 = p_0800 - p_0700
        diff_8_to_9 = p_0900 - p_0800
        total_diff = p_0900 - p_0700

        return {
            "p07": p_0700,
            "p08": p_0800,
            "p09": p_0900,
            "diff_1": diff_7_to_8,
            "diff_2": diff_8_to_9,
            "total_diff": total_diff,
        }
    except Exception:
        return None


def generate_hourly_report():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.datetime.now(ist)

    # Saturday (5) ebong Sunday (6) market bondho thakay bot pause thakbe
    if now.weekday() in [5, 6]:
        return "⚠️ Aj Shoni/Robi bar, Market bondho."

    today_date = now.strftime("%d %b %Y")
    msg = f"📊 **Futures Market 1-Hour Breakdown** ({today_date})\n"
    msg += "⏰ **Sokal 07:00 AM ➔ 09:00 AM Movement**\n\n"

    for name, ticker in INDICES.items():
        data = fetch_hourly_futures_data(ticker)

        if data:
            sign1 = "+" if data["diff_1"] >= 0 else ""
            sign2 = "+" if data["diff_2"] >= 0 else ""
            sign_tot = "+" if data["total_diff"] >= 0 else ""

            emoji1 = "🟢" if data["diff_1"] >= 0 else "🔴"
            emoji2 = "🟢" if data["diff_2"] >= 0 else "🔴"
            emoji_tot = "🟢" if data["total_diff"] >= 0 else "🔴"

            msg += f"🔹 **{name}**\n"
            msg += f"   ├ 07:00 ➔ 08:00: {emoji1} `{sign1}{data['diff_1']:.2f}` pts\n"
            msg += f"   ├ 08:00 ➔ 09:00: {emoji2} `{sign2}{data['diff_2']:.2f}` pts\n"
            msg += f"   └ Total Change : {emoji_tot} `{sign_tot}{data['total_diff']:.2f}` pts\n\n"
        else:
            msg += f"⚠️ **{name}**: Data paowa jayni / Market bondho\n\n"

    return msg


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload, timeout=10)


if __name__ == "__main__":
    report_text = generate_hourly_report()
    send_telegram(report_text)
    
