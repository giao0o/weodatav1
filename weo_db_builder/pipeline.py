from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,re,sqlite3,sys
from pathlib import Path
import fitz
from .config import SCENARIOS,TECHNOLOGIES
VERSION='2.0.0'
def sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def year_from(path,title=''):
 m=re.search(r'(19|20)\d{2}',path.name+' '+(title or ''))
 return int(m.group()) if m else None
def connect(db):
 con=sqlite3.connect(db); con.execute('PRAGMA foreign_keys=ON')
 schema=Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'); con.executescript(schema); return con
def ingest_one(con,path,store_pages=True):
 digest=sha256(path); old=con.execute('SELECT id FROM documents WHERE sha256=?',(digest,)).fetchone()
 if old:return {'file':path.name,'status':'skipped_duplicate','document_id':old[0]}
 doc=fitz.open(path); title=doc.metadata.get('title') or ''; year=year_from(path,title)
 cur=con.execute('INSERT INTO documents(sha256,filename,publication_year,title,author,pages,ingested_at,extraction_version) VALUES(?,?,?,?,?,?,?,?)',
 (digest,path.name,year,title,doc.metadata.get('author'),len(doc),dt.datetime.now(dt.timezone.utc).isoformat(),VERSION)); did=cur.lastrowid
 mention_rows=[]
 for n,page in enumerate(doc,1):
  text=re.sub(r'\s+',' ',page.get_text('text').replace('\u00a0',' ')).strip()
  if store_pages: con.execute('INSERT INTO pages(document_id,page_number,text) VALUES(?,?,?)',(did,n,text))
  for cat,mapping in [('scenario',SCENARIOS),('technology',TECHNOLOGIES)]:
   for label,patterns in mapping.items():
    count=sum(len(re.findall(p,text,re.I)) for p in patterns)
    if count: mention_rows.append((did,n,cat,label,count))
 con.executemany('INSERT INTO mentions(document_id,page_number,category,label,mention_count) VALUES(?,?,?,?,?)',mention_rows); con.commit()
 return {'file':path.name,'status':'ingested','document_id':did,'year':year,'pages':len(doc),'mention_rows':len(mention_rows)}
def export_all(con,out):
 out.mkdir(parents=True,exist_ok=True)
 queries={
 'documents':'SELECT * FROM documents ORDER BY publication_year,filename',
 'mention_summary':'''SELECT d.publication_year,d.filename,m.category,m.label,SUM(m.mention_count) total_mentions,COUNT(DISTINCT m.page_number) pages_mentioned FROM mentions m JOIN documents d ON d.id=m.document_id GROUP BY d.id,m.category,m.label ORDER BY d.publication_year,m.category,total_mentions DESC''',
 'projections':'SELECT * FROM projections ORDER BY publication_year,scenario,technology,target_year',
 'realized_values':'SELECT * FROM realized_values ORDER BY technology,indicator,observation_year',
 'projection_errors':'SELECT * FROM projection_errors ORDER BY technology,publication_year,target_year'}
 for name,q in queries.items():
  cur=con.execute(q); rows=cur.fetchall();
  with (out/f'{name}.csv').open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.writer(f); w.writerow([d[0] for d in cur.description]); w.writerows(rows)
 # blank import templates
 templates={
 'projections_import_template.csv':['document_filename','publication_year','scenario','technology','indicator','region','target_year','projected_value','unit','source_page','evidence_text','review_status','notes'],
 'realized_values_import_template.csv':['technology','indicator','region','observation_year','realized_value','unit','source_name','source_url','notes']}
 for fn,cols in templates.items():
  p=out/fn
  if not p.exists():
   with p.open('w',newline='',encoding='utf-8-sig') as f: csv.writer(f).writerow(cols)
 stats={'documents':con.execute('SELECT COUNT(*) FROM documents').fetchone()[0],'pages':con.execute('SELECT COUNT(*) FROM pages').fetchone()[0],'mentions':con.execute('SELECT COUNT(*) FROM mentions').fetchone()[0],'projections':con.execute('SELECT COUNT(*) FROM projections').fetchone()[0],'realized_values':con.execute('SELECT COUNT(*) FROM realized_values').fetchone()[0]}
 (out/'database_summary.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
 return stats
def main(argv=None):
 ap=argparse.ArgumentParser(description='Build a multi-vintage IEA WEO SQLite research database')
 ap.add_argument('input',type=Path,help='PDF file or directory containing WEO PDFs'); ap.add_argument('--db',type=Path,default=Path('weo_research.db')); ap.add_argument('--out',type=Path,default=Path('exports')); ap.add_argument('--no-page-text',action='store_true')
 a=ap.parse_args(argv); paths=sorted(a.input.glob('*.pdf')) if a.input.is_dir() else [a.input]
 if not paths: raise SystemExit('No PDF files found')
 con=connect(a.db); results=[ingest_one(con,p,not a.no_page_text) for p in paths]; stats=export_all(con,a.out); con.close()
 print(json.dumps({'results':results,'database':str(a.db),'exports':str(a.out),'stats':stats},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
