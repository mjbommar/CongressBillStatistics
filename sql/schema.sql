DROP TABLE IF EXISTS congress;
DROP TABLE IF EXISTS document;
DROP TABLE IF EXISTS document_statistics;

CREATE TABLE congress (
	id INTEGER PRIMARY KEY,
	description VARCHAR
);

CREATE TABLE document (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	filename VARCHAR,
	congress_id INTEGER NOT NULL,
	session VARCHAR,
	published DATETIME,
	citation VARCHAR,
	type VARCHAR,
	title VARCHAR,
	stage VARCHAR,
	chamber VARCHAR,
	md5 VARCHAR,
	processed BOOLEAN,
	FOREIGN KEY(congress_id) REFERENCES congress(id)
);

CREATE TABLE document_statistics (
	document_id INTEGER NOT NULL,
	statistic_id VARCHAR,
	statistic_value REAL,
	FOREIGN KEY(document_id) REFERENCES document(id)
);