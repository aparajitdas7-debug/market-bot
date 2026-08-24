import requests
from datetime import datetime, timezone, timedelta

TOKEN = "8978761813:AAHNrEdRRVrKGuOfRJmSEUo9TMf8xWmywQQ"
CHAT_ID = "6514656533"

# ৯টি ইনডেক্স ও ফিউচার্সের টিকার
symbols = {
    "Dow Jones Fut": "YM=F",
    "US Tech 100 Fut": "NQ=F",
    "DAX Fut": "FDX=F",
    "CAC 40 Fut": "FCE=F",
    "FTSE 100 Fut": "Z=F",
    "GIFT Nifty Fut": "IN=F",
    "Nikkei 225 Fut": "NK=F",
    "Hang Seng Fut": "HSI=F",
    "Shanghai Comp": "000001.SS"
}

headers = {'User-Agent': 'Mozilla/5.0'}
report = "📊 সকাল ০৭:৩০ - ০৯:০০ পয়েন্ট মুভমেন্ট\n\n"
ist = timezone(timedelta(hours=5, minutes=30))
today_date = datetime.now(ist).date()

for name, symbol in symbols.items():
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=2d"
        res = requests.get(url, headers=headers).json()
        
        result = res.get('chart', {}).get('result')
        if not result:
            report += f"⚠️ {name}: ডেটা পাওয়া যায়নি\n\n"
            continue
            
        timestamps = result[0].get('timestamp', [])
        quotes = result[0]['indicators']['quote'][0].get('close', [])
        
        prices_in_range = []
        
        for ts, price in zip(timestamps, quotes):
            if price is None:
                continue
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(ist)
            
            # শুধুমাত্র আজকের 07:30 (450 min) থেকে 09:00 (540 min) IST ফিল্টার
            if dt.date() == today_date:
                time_val = dt.hour * 60 + dt.minute
                if 450 <= time_val <= 540:
                    prices_in_range.append(price)
        
        if len(prices_in_range) >= 2:
            p_0730 = prices_in_range[0]   # ০৭:৩০-এর দাম
            p_0900 = prices_in_range[-1]  # ০৯:০০-এর দাম
            
            diff = p_0900 - p_0730
            status = "🟢" if diff >= 0 else "🔴"
            
            report += f"{status} {name}: {diff:+.2f} পয়েন্ট\n"
            report += f"  └ 07:30 -> {p_0730:.2f} | 09:00 -> {p_0900:.2f}\n\n"
        else:
            report += f"⚠️ {name}: এই সময়ের ডেটা বন্ধ\n\n"
            
    except Exception:
        report += f"⚠️ {name}: ডেটা আনা যায়নি\n\n"

# টেলিগ্রামে মেসেজ পাঠানো
telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
resp = requests.post(telegram_url, data={"chat_id": CHAT_ID, "text": report})

if resp.status_code == 200:
    print("মেসেজ সফলভাবে টেলিগ্রামে পাঠানো হয়েছে!")
else:
    print("টেলিগ্রাম এরর:", resp.text)
  
