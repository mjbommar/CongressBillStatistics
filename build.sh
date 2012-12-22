# Basic example of building the HTML report.

# Make sure we have the required Python libraries.
# I'm assuming you have root; if not, and you're using a venv, comment out sudo and use your pip/python path.
if [ -e requirements.txt ]
then
    for python_library in `cat requirements.txt`
    do
	sudo pip install $python_library;
    done
fi

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


