"""Deliver only the public research report table; never read Gmail summaries."""
import argparse
import datetime as dt
import json
import os
from zoneinfo import ZoneInfo
from radar import Store, notify, digest

def message_for(db, today, days=1):
    row = db.q("SELECT report_text FROM radar_public_digests WHERE period_days=? AND report_date=?", (days,today)).fetchone()
    return row[0] if row else None

def due_periods(today):
    return [1] + ([7] if today.weekday()==0 else []) + ([30] if today.day==1 else [])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    args=parser.parse_args()
    url=os.getenv("DATABASE_URL")
    if not url: parser.error("DATABASE_URL eksik")
    db=Store(url)
    try:
        now=dt.datetime.now(ZoneInfo("Europe/Istanbul"))
        today=now.date()
        failed=False
        for days in ([1] if args.test else due_periods(today)):
            if args.test:
                key="notification-test:"+os.environ.get("GITHUB_RUN_ID","local")+":"+os.environ.get("GITHUB_RUN_ATTEMPT","1")
                msg="Global Trend Radar AI | Bağlantı testi. Özel veri içermez."
            else:
                key="public-digest:"+str(days)+":"+today.isoformat()
                msg=message_for(db,today,days)
                if msg is None:
                    print(json.dumps({"period_days":days,"status":"digest_not_ready"})); continue
            deliveries=notify(db,msg,key)
            existing=db.q("SELECT channel,status FROM radar_deliveries WHERE id IN (?,?)",(digest(key+"telegram"),digest(key+"ntfy"))).fetchall()
            print(json.dumps({"period_days":days,"deliveries":deliveries,"recorded":existing},ensure_ascii=False))
            if not any(x[1]=="sent" for x in existing): failed=True
        return int(failed)
    finally:
        db.close()

if __name__=="__main__":
    raise SystemExit(main())
