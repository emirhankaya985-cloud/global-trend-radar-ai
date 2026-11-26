import datetime as dt
import sqlite3
import send_digest

class DB:
    def __init__(self, row):
        self.row = row
    def q(self, sql, args):
        assert "WHERE report_date=?" in sql
        assert args == (dt.date(2026, 11, 26),)
        return self
    def fetchone(self):
        return self.row

def test_private_digest():
    assert send_digest.message_for(DB(("Türkçe özet",)), dt.date(2026,11,26)) == "Türkçe özet"

def test_missing_digest(monkeypatch):
    monkeypatch.setattr(send_digest, "report", lambda *args: "Fallback")
    result = send_digest.message_for(DB(None), dt.date(2026,11,26))
    assert "henüz hazır değil" in result
    assert result.endswith("Fallback")
