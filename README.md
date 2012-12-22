CongressBillStatistics
======================

Congressional Bill Statistics from Bommarito Consulting, LLC; http://bommaritollc.com/

This "application" handles retrieving XML copies of all published bill versions from Congress and parsing them into a basic SQLite research database with some statistics on document properties and natural language features.  There is also a basic example of generating report data.

This is done in about the simplest way possible - no ORM, no formal model, no templating library.  The only required libraries are lxml, nltk, and python-dateutil (managed in requirements.txt).

If you want to try this out, you should simply be able to run build.sh.  Only tested on Debian with python 2.7.