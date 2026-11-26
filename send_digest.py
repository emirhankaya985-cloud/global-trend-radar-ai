"""Deliver Turkish public-source digests without logging private content."""
import argparse
import datetime as dt
import json
import os
from zoneinfo import ZoneInfo
from radar import Store, notify

def message_for(db, today):
    row = db.q("SELECT report_text, newsletter_count FROM radar_turkish_digests WHERE report_date=?", (today,)).fetchone()
    if not row:
        return None, "digest_not_ready"
    if row[1] != 0:
        return None, "private_newsletter_digest"
    return row[0], "ready"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    url = os.getenv("DATABASE_URL")
    if not url:
        parser.error("DATABASE_URL eksik")
    db = Store(url)
    try:
        today = dt.datetime.now(ZoneInfo("Europe/Istanbul")).date()
        key = "turkish-daily:" + today.isoformat()
        if args.test:
            key = "notification-test:" + os.environ.get("GITHUB_RUN_ID", "local")
            msg = "Global Trend Radar AI | Telegram/ntfy bağlantı testi. Özel veri içermez."
        else:
            msg, status = message_for(db, today)
            if msg is None:
                print(json.dumps({"status": status}))
                return 0
        deliveries = notify(db, msg, key)
        print(json.dumps({"deliveries": deliveries, "configured": {"telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")), "ntfy": bool(os.getenv("NTFY_TOPIC"))}}, ensure_ascii=False))
        if args.test and not any(x["status"] == "sent" for x in deliveries):
            return 1
        return int(any(x["status"] != "sent" for x in deliveries))
    finally:
        db.close()

if __name__ == "__main__":
    raise SystemExit(main())
