import json, sqlite3, datetime as dt
import pytest
import radar
S={'id':'example','category':'gündem','enabled':True,'interval_hours':1,'trust':'test'}
RSS=b'''<rss version="2.0"><channel><item><title>AI product launch</title><link>https://example.org/story?utm_source=a&amp;x=1</link><pubDate>Wed, 25 Nov 2026 12:00:00 GMT</pubDate></item></channel></rss>'''
ATOM=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Retail market</title><link rel="alternate" href="https://example.org/retail"/><updated>2026-11-25T12:00:00Z</updated></entry></feed>'''
@pytest.fixture
def db(monkeypatch,tmp_path):
    monkeypatch.setenv('RADAR_SQLITE',str(tmp_path/'test.sqlite3'));d=radar.Store();yield d;d.close()
@pytest.mark.parametrize('url,expected', [('https://Example.org/a?utm_source=x&k=1#x','https://example.org/a?k=1'),('javascript:alert(1)',None),('https://user:secret@example.org/a',None),('https://example.org','https://example.org/')])
def test_canonical(url,expected): assert radar.canonical(url)==expected
@pytest.mark.parametrize('text,category', [('AI launch','yapay zekâ'),('Etsy shirt','e-ticaret'),('Hiring now','kariyer'),('Inflation report','ekonomi'),('Other','gündem')])
def test_category(text,category): assert radar.categorize(text,'gündem')==category
def test_rss():
    r=radar.parse_feed(RSS,S)[0];assert r['category']=='yapay zekâ';assert r['published_at']=='2026-11-25T12:00:00+00:00';assert r['url']=='https://example.org/story?x=1'
def test_atom(): assert radar.parse_feed(ATOM,S)[0]['title']=='Retail market'
def test_xml_attack():
    with pytest.raises(Exception): radar.parse_feed(b'<!DOCTYPE a [<!ENTITY e SYSTEM "file:///etc/passwd">]><rss><item><title>&e;</title></item></rss>',S)
def test_invalid_feed():
    with pytest.raises(ValueError): radar.parse_feed(b'<html/>',S)
def test_missing_title(): assert radar.parse_feed(b'<rss><item><link>https://example.org</link></item></rss>',S)==[]
def test_dedupe(db):
    r=radar.parse_feed(RSS,S)[0];assert db.add(r)==1;assert db.add(r)==0
    assert db.q('SELECT count(*) FROM radar_items').fetchone()[0]==1
def test_clusters():
    rows=[('a','gündem','AI launches new model','https://x','a'),('b','gündem','New model launches AI','https://y','b'),('b','gündem','completely different story','https://z','c')];assert len(radar.clusters(rows))==2
def test_empty_report(db): assert 'Veri yok' in radar.report(db,1,[S])
def test_report_unknown_history(db):
    db.add(radar.parse_feed(RSS,S)[0]);assert 'yetersiz geçmiş' in radar.report(db,1,[S]);assert 'Özgün başlık' in radar.report(db,1,[S])
def test_collect_and_skip(db,monkeypatch):
    monkeypatch.setattr(radar,'fetch',lambda s,last:(radar.parse_feed(RSS,s),'abc',None,'ok'))
    assert radar.collect(db,[S])[0]['inserted']==1;assert radar.collect(db,[S])==[];assert radar.collect(db,[S],True)[0]['inserted']==0
    assert db.q('SELECT count(*) FROM radar_fetches').fetchone()[0]==2
def test_fetch_error(db,monkeypatch):
    def fail(*args): raise OSError('secret URL should not appear')
    monkeypatch.setattr(radar,'fetch',fail);r=radar.collect(db,[S])[0];assert r['status']=='error';assert r['error']=='OSError'
def test_disabled(db): assert radar.collect(db,[dict(S,enabled=False)])==[]
def test_github():
    s=dict(S,id='github_discovery');b=json.dumps({'items':[{'full_name':'x/y','html_url':'https://github.com/x/y','private':False,'created_at':'2026-11-25T12:00:00Z'},{'full_name':'private/x','html_url':'https://github.com/private/x','private':True}]}).encode();r=radar.parse_github(b,s);assert len(r)==1;assert r[0]['id']==radar.digest('github_discovery|https://github.com/x/y')
def test_github_incomplete():
    with pytest.raises(ValueError): radar.parse_github(b'{"incomplete_results":true,"items":[]}',S)
def test_notify_missing_config(db,monkeypatch):
    for k in ('NTFY_TOPIC','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID'):monkeypatch.delenv(k,raising=False)
    assert radar.notify(db,'test','key')==[];assert db.q('SELECT count(*) FROM radar_deliveries').fetchone()[0]==0
def test_no_alert_single_source(db,monkeypatch):
    db.add(radar.parse_feed(RSS,S)[0]);monkeypatch.setattr(radar,'notify',lambda *a:pytest.fail('unexpected alert'));radar.alerts(db,[S])
def test_dates(): assert radar.dateval('invalid') is None;assert radar.dateval('2026-11-25T12:00:00') is None
def test_source_failure_backoff(db,monkeypatch):
    def fail(*args): raise OSError()
    monkeypatch.setattr(radar,'fetch',fail)
    assert radar.collect(db,[S])[0]['status']=='error'; assert radar.collect(db,[S])==[]
def test_notification_receipt(db,monkeypatch):
    monkeypatch.setenv('NTFY_TOPIC','example_test_1234567890');monkeypatch.delenv('TELEGRAM_BOT_TOKEN',raising=False)
    class Response:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,n):return b'{"id":"receipt-1"}'
    monkeypatch.setattr(radar.OPENER,'open',lambda *a,**k:Response())
    assert radar.notify(db,'test','report-key')==[{'channel':'ntfy','status':'sent'}]
    assert radar.notify(db,'test','report-key')==[]
    assert db.q('SELECT receipt FROM radar_deliveries').fetchone()[0]=='receipt-1'
def test_notification_unverified(db,monkeypatch):
    monkeypatch.setenv('NTFY_TOPIC','example_test_1234567890');monkeypatch.delenv('TELEGRAM_BOT_TOKEN',raising=False)
    def fail(*a,**k):raise TimeoutError()
    monkeypatch.setattr(radar.OPENER,'open',fail)
    assert radar.notify(db,'test','report-key')[0]['status']=='unverified';assert radar.notify(db,'test','report-key')==[]
