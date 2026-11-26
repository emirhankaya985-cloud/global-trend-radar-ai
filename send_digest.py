"""Deliver private, generated Turkish digests without printing report content."""
import argparse
import datetime as dt
import json
import os
from zoneinfo import ZoneInfo
from radar import Store, notify, report, ROOT

def message_for(db, today):
    row = db.q("SELECT report_text FROM radar_turkish_digests WHERE report_date=?", (today,)).fetchone()
    if row:
        return row[0]
    sources = json.loads((ROOT / "sources.json").read_text())
    return "Türkçe AI özeti henüz hazır değil; aşağıdaki rapor özgün başlıklar içerebilir.\n" + report(db, 1, sources)

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
            key += ":test:" + os.environ.get("GITHUB_RUN_ID", "local")
        deliveries = notify(db, message_for(db, today), key)
        print(json.dumps({"deliveries": deliveries}, ensure_ascii=False))
        if args.test and not any(x["status"] == "sent" for x in deliveries):
            return 1
        return int(any(x["status"] != "sent" for x in deliveries))
    finally:
        db.close()

if __name__ == "__main__":
    raise SystemExit(main())
