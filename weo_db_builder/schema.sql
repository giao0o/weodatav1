PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS documents (
 id INTEGER PRIMARY KEY, sha256 TEXT UNIQUE NOT NULL, filename TEXT NOT NULL,
 publication_year INTEGER, title TEXT, author TEXT, pages INTEGER,
 ingested_at TEXT NOT NULL, extraction_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pages (
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL, page_number INTEGER NOT NULL,
 text TEXT NOT NULL, FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
 UNIQUE(document_id,page_number)
);
CREATE TABLE IF NOT EXISTS mentions (
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL, page_number INTEGER NOT NULL,
 category TEXT NOT NULL, label TEXT NOT NULL, mention_count INTEGER NOT NULL,
 FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS projections (
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL, publication_year INTEGER,
 scenario TEXT, technology TEXT, indicator TEXT, region TEXT DEFAULT 'World',
 target_year INTEGER, forecast_horizon INTEGER, projected_value REAL, unit TEXT,
 source_page INTEGER, evidence_text TEXT, extraction_method TEXT DEFAULT 'manual_review',
 review_status TEXT DEFAULT 'unreviewed', notes TEXT,
 FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS realized_values (
 id INTEGER PRIMARY KEY, technology TEXT, indicator TEXT, region TEXT DEFAULT 'World',
 observation_year INTEGER, realized_value REAL, unit TEXT, source_name TEXT,
 source_url TEXT, notes TEXT, UNIQUE(technology,indicator,region,observation_year,source_name)
);
CREATE VIEW IF NOT EXISTS projection_errors AS
SELECT p.id AS projection_id,p.publication_year,p.scenario,p.technology,p.indicator,p.region,
 p.target_year,p.forecast_horizon,p.projected_value,p.unit,r.realized_value,r.source_name,
 (p.projected_value-r.realized_value) AS error,
 ABS(p.projected_value-r.realized_value) AS absolute_error,
 CASE WHEN r.realized_value<>0 THEN 100.0*(p.projected_value-r.realized_value)/r.realized_value END AS percentage_error,
 CASE WHEN (ABS(p.projected_value)+ABS(r.realized_value))<>0 THEN 200.0*ABS(p.projected_value-r.realized_value)/(ABS(p.projected_value)+ABS(r.realized_value)) END AS smape
FROM projections p JOIN realized_values r ON p.technology=r.technology AND p.indicator=r.indicator
 AND p.region=r.region AND p.target_year=r.observation_year AND p.unit=r.unit
WHERE p.review_status='verified';
