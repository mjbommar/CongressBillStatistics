# Basic example of building the HTML report.

# Backup old file if present
if [ -e congress.db ]
then
    mv congress.db congress.db.`date +%Y%m%d%H%M%S`
fi

# Initialize new SQLite DB.
sqlite3 congress.db < sql/schema.sql

# Update data from Congress.
PYTHONPATH=src python src/com/bommaritollc/model/Congress.py

# Run report
PYTHONPATH=src python src/com/bommaritollc/model/Report.py


