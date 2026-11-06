import argparse,csv,sqlite3
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',required=True); ap.add_argument('--projections'); ap.add_argument('--realized'); a=ap.parse_args(); con=sqlite3.connect(a.db)
 if a.projections:
  for r in csv.DictReader(open(a.projections,encoding='utf-8-sig')):
   doc=con.execute('SELECT id FROM documents WHERE filename=?',(r['document_filename'],)).fetchone()
   if not doc: raise ValueError('Unknown document: '+r['document_filename'])
   fy=int(r['publication_year']) if r['publication_year'] else None; ty=int(r['target_year']); horizon=ty-fy if fy else None
   con.execute('''INSERT INTO projections(document_id,publication_year,scenario,technology,indicator,region,target_year,forecast_horizon,projected_value,unit,source_page,evidence_text,review_status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(doc[0],fy,r['scenario'],r['technology'],r['indicator'],r.get('region') or 'World',ty,horizon,float(r['projected_value']),r['unit'],int(r['source_page']) if r['source_page'] else None,r['evidence_text'],r.get('review_status') or 'unreviewed',r.get('notes')))
 if a.realized:
  for r in csv.DictReader(open(a.realized,encoding='utf-8-sig')):
   con.execute('''INSERT OR REPLACE INTO realized_values(technology,indicator,region,observation_year,realized_value,unit,source_name,source_url,notes) VALUES(?,?,?,?,?,?,?,?,?)''',(r['technology'],r['indicator'],r.get('region') or 'World',int(r['observation_year']),float(r['realized_value']),r['unit'],r['source_name'],r.get('source_url'),r.get('notes')))
 con.commit(); con.close()
if __name__=='__main__':main()
