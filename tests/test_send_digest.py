import datetime as dt
import send_digest

class DB:
    def __init__(self,row,days=1): self.row=row; self.days=days
    def q(self,sql,args):
        assert "FROM radar_public_digests" in sql
        assert "radar_turkish_digests" not in sql
        assert args==(self.days,dt.date(2026,11,26))
        return self
    def fetchone(self): return self.row

def test_public_digest():
    assert send_digest.message_for(DB(("Türkçe özet",)),dt.date(2026,11,26))=="Türkçe özet"

def test_missing_digest():
    assert send_digest.message_for(DB(None),dt.date(2026,11,26)) is None

def test_weekly_digest():
    assert send_digest.message_for(DB(("Haftalık",),7),dt.date(2026,11,26),7)=="Haftalık"

def test_periods():
    assert send_digest.due_periods(dt.date(2026,11,26))==[1]
    assert send_digest.due_periods(dt.date(2026,11,30))==[1,7]
    assert send_digest.due_periods(dt.date(2026,12,1))==[1,30]
    assert send_digest.due_periods(dt.date(2027,2,1))==[1,7,30]
