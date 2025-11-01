import requests
from bs4 import BeautifulSoup
import os
import sys

# URL halaman BEI untuk aktivitas pencatatan (IPO, listing baru)
IDX_URL = "https://www.idx.co.id/id/perusahaan-tercatat/aktivitas-pencatatan"

SEEN_FILE = "seen_links.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in env.")
    sys.exit(2)

def fetch_idx():
    print("📡 Fetching IDX page...")
    r = requests.get(IDX_URL, timeout=20)
    r.raise_for_status()
    return r.text

def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href").strip()
        text = a.get_text(strip=True)
        if href.startswith("/"):
            href = "https://www.idx.co.id" + href
        if any(k in href.lower() for k in ["pencatatan", "listing", "ipo"]) or \
           any(k in text.lower() for k in ["pencatatan", "listing", "ipo"]):
            links.append((href, text))
    # Hilangkan duplikat
    seen = set()
    uniq = []
    for href, text in links:
        if href not in seen:
            seen.add(href)
            uniq.append((href, text))
    return uniq

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen(urls):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        for u in sorted(urls):
            f.write(u + "\n")

def send_telegram_messages(new_items):
    print(f"🚀 Sending {len(new_items)} new IPO links to Telegram...")
    base = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for href, text in new_items:
        message = f"📣 *IPO / Pencatatan Baru Ditemukan*\n{text}\n{href}"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        resp = requests.post(base, data=payload, timeout=10)
        if resp.status_code != 200:
            print("⚠️ Gagal kirim:", resp.text)
        else:
            print("✅ Dikirim:", href)

def main():
    html = fetch_idx()
    items = extract_links(html)
    found_urls = [href for href, _ in items]
    seen = load_seen()
    new = [item for item in items if item[0] not in seen]
    if not new:
        print("✅ Tidak ada link IPO baru.")
        return 0
    send_telegram_messages(new)
    save_seen(set(found_urls) | seen)
    print(f"🎉 Selesai kirim {len(new)} link baru.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
