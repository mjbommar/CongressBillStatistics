'''
Created on Feb 19, 2012
@author: mjbommar
'''

import codecs
import cStringIO
import csv
import sqlite3

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            
reportHtml = u"""<?xml version="1.0" encoding="UTF-8"?>
	<!DOCTYPE html 
	     PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	     "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
	  <head>
	    <title>{0}</title>
	    <link rel="stylesheet" type="text/css" href="style.css" />
	  </head>
	  <body>
<h3>Congressional Bill Complexity</h3>
<p>This data is provided by <a href="http://michaelbommarito.com/">Bommarito Consulting, LLC</a>; for more information about how the data is collected and calculated, please see <a href="http://michaelbommarito.com/2012/04/14/updates-to-data-and-statistics-on-congressional-bill-complexity/">this page</a>.</p>
<script type="text/javascript" src="http://s10.sitemeter.com/js/counter.js?site=s10mjbommar"></script><noscript> <a
href="http://s10.sitemeter.com/stats.asp?site=s10mjbommar" target="_top"> <img
src="http://s10.sitemeter.com/meter.asp?site=s10mjbommar" alt="Site Meter" border="0"/></a> </noscript>
	    {1}
	  </body>
	</html>"""
	
tableHtml = u"<table cellspacing=\"0\" cellpadding=\"0\" border=\"0\">{0}{1}</table>"
theadHtml = u"<thead>{0}</thead>"
tbodyHtml = u"<tbody>{0}</tbody>"
trHtml = u"<tr>{0}</tr>"
thHtml = u"<th class=\"{0}\">{1}</th>"
tdHtml = u"<td class=\"{0}\">{1}</td>"

class Report(object):
	'''
	The Report object handles all reporting tasks.
	'''
	
	def __init__(self):
		'''
		Constructor.
		'''
		self.initDB()
	
	def initDB(self):
		'''
		Initialize the database connection.
		'''
		self.connection = sqlite3.connect("congress.db")
    
	def closeDB(self):
		'''
		Close and clean up database connection.
		'''
		self.connection.commit()
		self.connection.close()
	
	def buildCsv(self, headerRow, dataRows, outputFileName):
		'''
		Build a CSV spreadsheet for the data.
		'''
		outputFile = codecs.open(outputFileName, 'w', 'utf8', 'ignore')
		outputWriter = csv.writer(outputFile)
		outputWriter.writerow(headerRow)
		#outputWriter.writerows([unicode(c).replace(u"\u2013", "-").replace(u"\xed", "").replace(u'\u03ba', ' ' ).replace(u'\u2032', ' ').replace(u'\u03b1', ' ').replace(u'\u03b2', ' ').replace(u'\u03b5', ' ').replace(u'\xdf', " ").replace("\n", " ").replace("\t", " ").decode('utf8') for c in row] for row in dataRows)
                outputWriter.writerows([[unicode(c).encode('ascii', 'ignore') for c in row] for row in dataRows])
		outputFile.close()
		
	def buildHtml(self, title, headerRow, dataRows, outputFileName):
		'''
		Build an HTML document with the given table.
		'''
		
		# Build buffer.
		theadBuffer = theadHtml.format(trHtml.format("".join([thHtml.format(header.lower(), header) for header in headerRow])))
		tbodyBuffer = tbodyHtml.format("".join([trHtml.format("".join([tdHtml.format(headerRow[i].lower().replace(" ", "").replace(".",""), row[i]) for i in range(len(row))])) for row in dataRows])).replace("\n", " ").replace("\t", " ")		
		tableBuffer = tableHtml.format(theadBuffer, tbodyBuffer)
		htmlBuffer = reportHtml.format(title, tableBuffer)
		
		# Write to file.
		outputFile = codecs.open(outputFileName, 'w', 'utf8', 'ignore')
		outputFile.write(htmlBuffer)
		outputFile.close()
		
				
	def buildAll(self, orderBy="-published"):
		# Create cursor.
		cursor = self.connection.cursor()
		
		# Fetch the document.
		if orderBy.startswith("+"):
			sortOrder = "ASC"
			sortField = orderBy[1:]
		elif orderBy.startswith("-"):
			sortOrder = "DESC"
			sortField = orderBy[1:]
		else:
			sortOrder = "DESC"
			sortField = orderBy
						
		cursor.execute("SELECT * FROM document ORDER BY {0} {1}".format(sortField, sortOrder))
		documents = [row for row in cursor]
		
		# Fetch the stats.
		cursor.execute("SELECT * FROM document_statistics")
		documentStatistics = [row for row in cursor]	
		statisticIds = sorted(list(set([row[1] for row in documentStatistics])))
		
		# Build the header
		documentHeaders = ["Congress", "Date", "Citation", "Title", "Stage"]
		documentHeaderMap = {"Congress": 2, "Date": 4, "Citation": 5, "Title": 7, "Stage": 8}
		headerRow = []
		headerRow.extend(documentHeaders)
		headerRow.extend(statisticIds)
		
		# Build data rows.
		dataRows = []
		
		for document in documents:
			# Build current document row portion.
			dataRow = []
			congress = None
			for header in documentHeaders:
				if header == "Congress":
					congress = document[documentHeaderMap[header]]
				if header == "Citation":
					citation = document[documentHeaderMap[header]]
					legUrl = "http://thomas.loc.gov/cgi-bin/bdquery/z?d{0}:{1}:".format(congress, citation.lower().replace(".", ""))
					dataRow.append("<a href=\"{0}\">{1}</a>".format(legUrl, citation))
				elif header == "Date":
					dataRow.append(document[documentHeaderMap[header]].split()[0])
				else:
					dataRow.append(document[documentHeaderMap[header]])
			
			# Build current document stats portion.
			documentData = dict([(row[1], row[2]) for row in documentStatistics if row[0] == document[0]])
			for statisticId in statisticIds:
				try:
					dataRow.append(int(documentData[statisticId]))
				except:
					dataRow.append("%0.2f" % (documentData[statisticId]))
			
			dataRows.append(dataRow)
		
		self.buildCsv(headerRow, dataRows, "report/bills-all.csv")
		self.buildHtml("Bill Statistics - Complete List", headerRow, dataRows, "report/bills-all.html")		
				
		# Close the cursor.
		cursor.close()
		

		

if __name__ == "__main__":
	r = Report()
	r.buildAll()
	r.closeDB()
