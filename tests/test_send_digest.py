import datetime as dt
import send_digest

class DB:
    def __init__(self, row):
        self.row = row
    def q(self, sql, args):
        assert "newsletter_count" in sql
        assert "WHERE report_date=?" in sql
        assert args == (dt.date(2026, 11, 26),)
        return self
    def fetchone(self):
        return self.row

def test_public_digest():
    assert send_digest.message_for(DB(("Türkçe özet", 0)), dt.date(2026,11,26)) == ("Türkçe özet", "ready")

def test_missing_digest():
    assert send_digest.message_for(DB(None), dt.date(2026,11,26)) == (None, "digest_not_ready")

def test_private_newsletter_never_delivered():
    assert send_digest.message_for(DB(("Özel bülten", 1)), dt.date(2026,11,26)) == (None, "private_newsletter_digest")
