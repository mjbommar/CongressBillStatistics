# Basic example of building the HTML report.

# Create the report directory
mkdir -p report

# Install the packages
sudo apt-get install `cat debian-requirements.txt | xargs`

if [ ! -e venv ]
then
    virtualenv venv
    ./venv/bin/pip install -r python-requirements.txt
fi

# Install nltk packages
./venv/bin/python -c "import nltk; nltk.download('stopwords')"
./venv/bin/python -c "import nltk; nltk.download('punkt')"

# Backup old file if present
if [ -e congress.db ]
then
    mv congress.db congress.db.`date +%Y%m%d%H%M%S`
fi

# Initialize new SQLite DB.
sqlite3 congress.db < sql/schema.sql

# Update data from Congress.
PYTHONPATH=src ./venv/bin/python src/com/bommaritollc/model/Congress.py

# Run report
PYTHONPATH=src ./venv/bin/python src/com/bommaritollc/model/Report.py


