"""Private, metadata-only trend collector. No article scraping or paid API."""
import argparse, collections, datetime as dt, hashlib, html, json, os, re, sqlite3, sys, uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from email.utils import parsedate_to_datetime
from defusedxml import ElementTree as ET
ROOT=Path(__file__).resolve().parent
UTC=dt.timezone.utc
MAX_BYTES=2_000_000
STOP=set('the a an is are to of in on for and or with by from at as be this that it new how what why will after has have says more your you their its over about into up out'.split())
RULES={'yapay zekâ':r'\b(ai|artificial intelligence|llm|openai|anthropic|chatgpt|claude|machine learning)\b','e-ticaret':r'\b(etsy|shopify|ecommerce|e-commerce|retail|print.on.demand|t.shirt|marketplace)\b','kariyer':r'\b(hiring|jobs|employment|layoffs|career|recruitment)\b','ekonomi':r'\b(inflation|interest rates|gdp|central bank|tariffs|recession|stocks)\b'}
OPPS={'e-ticaret':'Etsy ve dijital ürün: talep, marka ve telif kontrolü yap.','yapay zekâ':'Video ve dijital ürün: kullanım koşulları ile müşteri ihtiyacını doğrula.','kariyer':'CareerHunter: ilan ve yetkinlik talebini araştır.','teknoloji':'Müşteri Avcısı: çözülmemiş işletme sorunlarını araştır.'}
def stamp(): return dt.datetime.now(UTC).isoformat(timespec='seconds')
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def clean(s): return ' '.join(html.unescape(re.sub(r'<[^>]*>',' ',s or '')).split())[:300]
def canonical(s):
    try:
        p=urlsplit(s.strip())
        if p.scheme not in ('http','https') or not p.hostname or p.username or p.password: return None
        return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',urlencode([(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid'}]),''))
    except ValueError: return None
def tokens(s): return {x for x in re.findall(r'[^\W_]+',s.casefold()) if (len(x)>2 or x in {"ai","us","uk","eu"}) and x not in STOP}
def topic(s):
    t=sorted(tokens(s)); return ' '.join(t)[:240] or s.casefold()[:240]
def categorize(title,default):
    return next((k for k,v in RULES.items() if re.search(v,title,re.I)),default)
def dateval(s):
    if not s: return None
    try:
        d=parsedate_to_datetime(s)
    except (ValueError,TypeError):
        try: d=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
        except ValueError: return None
    if d.tzinfo is None: return None
    return d.astimezone(UTC).isoformat(timespec='seconds')
def parse_feed(body,source):
    root=ET.fromstring(body)
    local=lambda t:t.rsplit('}',1)[-1]
    if local(root.tag) not in ('rss','feed','RDF'): raise ValueError('RSS/Atom değil')
    rows=[]
    for e in root.iter():
        if local(e.tag) not in ('item','entry'): continue
        fields={}; links=[]
        for c in e:
            k=local(c.tag); v=''.join(c.itertext())
            if k=='link' and c.get('rel','alternate')=='alternate': links.append(c.get('href') or v)
            elif k not in fields: fields[k]=v
        title=clean(fields.get('title')); url=next((x for l in links if (x:=canonical(l))),None)
        if not title or not url: continue
        rows.append({'id':digest(source['id']+'\0'+url),'source':source['id'],'category':categorize(title,source['category']),'title':title,'url':url,'published_at':dateval(fields.get('pubDate') or fields.get('published') or fields.get('updated')),'first_seen':stamp(),'topic':topic(title),'signal':clean(fields.get('approx_traffic')) or None})
        if len(rows)>=50: break
    return rows
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*a,**k): return None
OPENER=build_opener(NoRedirect())
def parse_github(body,source):
    data=json.loads(body)
    if data.get('incomplete_results'): raise ValueError('GitHub araması eksik sonuç döndürdü')
    if not isinstance(data.get('items'),list): raise ValueError('GitHub yanıtı geçersiz')
    rows=[]
    for item in data['items'][:20]:
        if item.get('private') or item.get('archived'): continue
        title=clean(item.get('full_name')); url=canonical(item.get('html_url') or '')
        if not title or not url or urlsplit(url).hostname!='github.com': continue
        rows.append({'id':digest(source['id']+'|'+url),'source':source['id'],'category':'teknoloji','title':title,'url':url,'published_at':dateval(item.get('created_at')),'first_seen':stamp(),'topic':title.casefold(),'signal':None})
    return rows

def fetch(s,last):
    headers={'User-Agent':'GlobalTrendRadarAI/0.1 (private RSS reader)','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'}
    if last and last[0]: headers['If-None-Match']=last[0]
    if last and last[1]: headers['If-Modified-Since']=last[1]
    url=s['url']; parser=parse_feed
    if s.get('kind')=='github_search':
        date=(dt.datetime.now(UTC).date()-dt.timedelta(days=6)).isoformat()
        url+='?'+urlencode({'q':f'is:public archived:false created:>={date} stars:>=10','per_page':20})
        headers['Accept']='application/vnd.github+json'; parser=parse_github
        if os.getenv('GITHUB_TOKEN'): headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
    try:
        with OPENER.open(Request(url,headers=headers),timeout=12) as r:
            b=r.read(MAX_BYTES+1)
            if len(b)>MAX_BYTES: raise ValueError('Yanıt boyut sınırı')
            return parser(b,s),r.headers.get('ETag'),r.headers.get('Last-Modified'),'ok'
    except HTTPError as e:
        if e.code==304: return [],last[0],last[1],'not_modified'
        raise ValueError('HTTP '+str(e.code)) from None
class Store:
    def __init__(self,url=None):
        self.pg=bool(url)
        if self.pg:
            if urlsplit(url).scheme not in ('postgres','postgresql'): raise ValueError('Postgres bağlantısı gerekli')
            import psycopg
            self.c=psycopg.connect(url,connect_timeout=10,sslmode='require')
        else: self.c=sqlite3.connect(os.getenv('RADAR_SQLITE','radar.sqlite3'))
        if self.pg:
            # Production schema is migrated by the separate owner, never by the app role.
            for table in ('radar_items','radar_fetches','radar_deliveries'):
                self.q('SELECT 1 FROM '+table+' LIMIT 0')
        else:
            for sql in (ROOT/'schema.sql').read_text().split(';'):
                if sql.strip(): self.q(sql)
        self.c.commit()
    def q(self,s,args=()): return self.c.execute(s.replace('?', '%s') if self.pg else s,args)
    def add(self,r):
        keys=list(r); return self.q('INSERT INTO radar_items ('+','.join(keys)+') VALUES ('+','.join('?' for _ in keys)+') ON CONFLICT DO NOTHING',tuple(r[k] for k in keys)).rowcount
    def close(self): self.c.close()
def collect(db,sources,force=False):
    results=[]
    if db.pg and db.q('SELECT pg_database_size(current_database())').fetchone()[0]>=700*1024*1024:
        raise RuntimeError('700 MiB koruma sınırı; veri silinmedi')
    if db.q('SELECT COUNT(*) FROM radar_items').fetchone()[0]>=150_000 or db.q('SELECT COUNT(*) FROM radar_fetches').fetchone()[0]>=100_000:
        raise RuntimeError('Koruma sınırı: arşivleme/kota kontrolü gerekli; veri silinmedi')
    for s in sources:
        if not s['enabled']: continue
        last=db.q('SELECT etag,modified,fetched_at FROM radar_fetches WHERE source=? AND status IN (?,?) ORDER BY fetched_at DESC LIMIT 1',(s['id'],'ok','not_modified')).fetchone()
        attempt=db.q('SELECT MAX(fetched_at) FROM radar_fetches WHERE source=?',(s['id'],)).fetchone()[0]
        if attempt and not force and dt.datetime.fromisoformat(attempt)>dt.datetime.now(UTC)-dt.timedelta(hours=s['interval_hours'],minutes=-5): continue
        n=added=0; etag=modified=err=None
        try:
            rows,etag,modified,status=fetch(s,last); n=len(rows)
            added=sum(db.add(r) for r in rows)
            db.c.commit()
        except Exception as e:
            db.c.rollback(); status='error'; added=0; err=type(e).__name__+(': '+str(e) if isinstance(e,ValueError) else '')
        db.q('INSERT INTO radar_fetches VALUES (?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),s['id'],stamp(),status,n,added,err,etag,modified));db.c.commit()
        results.append({'source':s['id'],'status':status,'fetched':n,'inserted':added,'error':err})
    return results
def clusters(rows):
    groups=[]; bases=[]; by_url={}; inverted=collections.defaultdict(set)
    for r in rows:
        t=tokens(r[2]); match=by_url.get(r[3])
        if match is None:
            candidates=collections.Counter(i for word in t for i in inverted[word])
            for i,overlap in candidates.most_common(100):
                if overlap<3: break
                if overlap/max(1,len(t|bases[i]))>=.72: match=i;break
        if match is None:
            match=len(groups);groups.append([]);bases.append(t)
            for word in t: inverted[word].add(match)
        groups[match].append(r);by_url[r[3]]=match
    return groups
def report(db,days,sources,translate=False):
    now=dt.datetime.now(UTC); cutoff=(now-dt.timedelta(days=days)).isoformat(timespec='seconds'); prev=(now-dt.timedelta(days=2*days)).isoformat(timespec='seconds')
    total=db.q('SELECT COUNT(*) FROM radar_items WHERE first_seen>=?',(cutoff,)).fetchone()[0]
    rows=db.q('SELECT source,category,title,url,topic,first_seen FROM radar_items WHERE first_seen>=? ORDER BY first_seen DESC LIMIT 5000',(cutoff,)).fetchall()
    previous=db.q('SELECT category,COUNT(*) FROM radar_items WHERE first_seen>=? AND first_seen<? GROUP BY category',(prev,cutoff)).fetchall()
    history=db.q('SELECT MIN(fetched_at) FROM radar_fetches WHERE status IN (?,?)',('ok','not_modified')).fetchone()[0]
    coverage=bool(history and history<=prev);  old=dict(previous); grouped=clusters(rows); counts=collections.Counter(g[0][1] for g in grouped); raw=dict(db.q('SELECT category,COUNT(*) FROM radar_items WHERE first_seen>=? GROUP BY category',(cutoff,)).fetchall()); registry={s['id']:s for s in sources}
    tr=None
    if translate:
        try:
            from argostranslate.translate import translate as tr
        except ImportError:
            tr=None
            lines_warning='Çeviri modülü kurulu değil; özgün başlıklar kullanıldı.'
    else: lines_warning=None
    lines=[f'Global Trend Radar AI | {days} günlük rapor',f'Gözlenen kayıt: {total} | Analiz örneklemi: {len(rows)} | Örneklemde yaklaşık benzersiz konu: {len(grouped)}','Sayılar gözlem hacmidir; pazar talebi veya gerçek arama sayısı değildir.']
    if total>len(rows): lines.append('Konu analizi son 5000 kayıtla sınırlı; toplam kayıt sayısı tamdır.')
    if translate and not tr: lines.append(lines_warning)
    for cat,count in counts.most_common():
        delta=f'{raw[cat]-old.get(cat,0):+d}' if coverage else 'yetersiz geçmiş'; lines.append(f'{cat}: {count} konu | önceki döneme göre ham kayıt değişimi: {delta}')
    if not rows: lines.append('Veri yok; fırsat veya trend çıkarılamadı.')
    for g in sorted(grouped,key=lambda x:len({r[0] for r in x}),reverse=True)[:12]:
        r=g[0]; name=registry.get(r[0],{}); n=len({x[0] for x in g}); title=r[2]
        if tr:
            try: title=tr(title,'en','tr')
            except Exception: title='[Çeviri başarısız] '+title
        else: title='[Özgün başlık] '+title
        lines.append(f'• {title} | {r[0]} ({name.get("trust","bilinmiyor")}) | {n} kaynak | {r[3]}')
        if n>=2 and r[1] in OPPS: lines.append('Araştırma hipotezi (doğrulanmadı): '+OPPS[r[1]])
    return '\n'.join(lines)
def notify(db,message,key):
    import urllib.parse
    targets=[]; nt=os.getenv('NTFY_TOPIC'); tg=os.getenv('TELEGRAM_BOT_TOKEN'); chat=os.getenv('TELEGRAM_CHAT_ID')
    if nt and re.fullmatch(r'[A-Za-z0-9_-]{16,128}',nt):
        headers={'Content-Type':'text/plain; charset=utf-8'}
        if os.getenv('NTFY_TOKEN'): headers['Authorization']='Bearer '+os.environ['NTFY_TOKEN']
        targets.append(('ntfy',Request('https://ntfy.sh/'+nt,data=message.encode()[:3500].decode('utf-8','ignore').encode(),headers=headers,method='POST')))
    if tg and chat and re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+',tg):
        targets.append(('telegram',Request('https://api.telegram.org/bot'+tg+'/sendMessage',data=json.dumps({'chat_id':chat,'text':message[:3900]}).encode(),headers={'Content-Type':'application/json'},method='POST')))
    results=[]
    for channel,req in targets:
        k=digest(key+channel); existing=db.q('SELECT status FROM radar_deliveries WHERE id=?',(k,)).fetchone()
        if existing: continue # no automatic retries after ambiguous delivery
        db.q('INSERT INTO radar_deliveries VALUES (?,?,?,?,?)',(k,channel,stamp(),'pending',None)); db.c.commit()
        status='error'; receipt=None
        try:
            with OPENER.open(req,timeout=12) as r:
                data=json.loads(r.read(65536)); receipt=data.get('id') if channel=='ntfy' else data.get('result',{}).get('message_id') if data.get('ok') else None
                status='sent' if receipt is not None else 'unverified'
        except Exception: status='unverified'
        db.q('UPDATE radar_deliveries SET status=?,receipt=? WHERE id=?',(status,str(receipt) if receipt is not None else None,k));db.c.commit(); results.append({'channel':channel,'status':status})
    return results
def alerts(db,sources):
    cutoff=(dt.datetime.now(UTC)-dt.timedelta(hours=3)).isoformat(timespec='seconds')
    rows=db.q('SELECT source,category,title,url,topic,first_seen FROM radar_items WHERE first_seen>=? ORDER BY first_seen DESC LIMIT 1000',(cutoff,)).fetchall()
    sent=0
    for group in clusters(rows):
        if sent>=3: break
        # Independent publishers cannot be inferred from domain alone; signal only.
        publishers={r[0].split('_')[0] for r in group}
        if len(publishers)<2: continue
        r=group[0]; key='alert:'+digest(r[4]); message=f'Çok kaynaklı konu sinyali (önem/doğruluk teyidi değil) | {r[1]} | {len(publishers)} kaynak\n'+ '\n'.join(f'{x[0]}: {x[2]} {x[3]}' for x in group[:4])
        if notify(db,message,key): sent+=1

def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['collect','report','health','export','alerts']);p.add_argument('--days',type=int,choices=[1,7,30],default=1);p.add_argument('--force',action='store_true');p.add_argument('--send',action='store_true');p.add_argument('--translate',action='store_true');p.add_argument('--require-db',action='store_true');args=p.parse_args()
    sources=json.loads((ROOT/'sources.json').read_text()); url=os.getenv('DATABASE_URL')
    if args.require_db and not url: p.error('DATABASE_URL eksik; üretim çalıştırması durduruldu')
    db=Store(url)
    try:
        if args.command=='collect':
            result=collect(db,sources,args.force); print(json.dumps(result,ensure_ascii=False)); return int(bool(result) and all(x['status']=='error' for x in result))
        if args.command=='report':
            msg=report(db,args.days,sources,args.translate); print(msg)
            if args.send:
                today=dt.datetime.now(UTC).date(); key=str(today if args.days==1 else today.isocalendar()[:2] if args.days==7 else today.strftime('%Y-%m'))+str(args.days); print(json.dumps(notify(db,msg,key)))
        elif args.command=='alerts':
            if args.send: alerts(db,sources)
        elif args.command=='export':
            cutoff=(dt.datetime.now(UTC)-dt.timedelta(days=args.days)).isoformat(timespec='seconds')
            rows=db.q('SELECT source,category,title,url,published_at,first_seen,signal FROM radar_items WHERE first_seen>=? ORDER BY first_seen DESC LIMIT 1000',(cutoff,)).fetchall()
            print(json.dumps({'schema_version':1,'items':[dict(zip(('source','category','title','url','published_at','first_seen','signal'),row)) for row in rows]},ensure_ascii=False))
        else:
            print(json.dumps({'items':db.q('SELECT COUNT(*) FROM radar_items').fetchone()[0],'fetches':db.q('SELECT source,status,COUNT(*) FROM radar_fetches GROUP BY source,status').fetchall(),'last_source_attempt':db.q('SELECT source,MAX(fetched_at) FROM radar_fetches GROUP BY source').fetchall(),'deliveries':db.q('SELECT channel,status,COUNT(*) FROM radar_deliveries GROUP BY channel,status').fetchall()},ensure_ascii=False))
        return 0
    finally: db.close()
if __name__=='__main__': sys.exit(main())
