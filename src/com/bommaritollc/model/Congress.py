'''
Created on Feb 15, 2012
@author: mjbommar
'''

# Standard library imports.
import dateutil.parser
import lxml.html
import os
import sqlite3
import urllib2

# CongressNLP imports.
from Document import Document

class Congress(object):
    '''
    A Congress object stores information about a Congressional term.
    '''
    
    def __init__(self, id=None):
        '''
        Default constructor.
        '''
        
        # Initialize instance fields.
        self.id = id
        self.documents = []
        self.connection = None
        
        # Set URL.
        if id != None:
            self.url = "http://thomas.loc.gov/home/gpoxmlc{0}".format(self.id)
            self.dataPath = "data/{0}".format(self.id)
            try:
                os.mkdir(self.dataPath)
            except:
                pass
        else:
            self.url = None
            self.dataPath = "data"
    
        # Sync up with DB.
        self.syncDB()
        
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
    
    def syncDB(self):
        '''
        Synchronize with the DB, which means upsert ID and 
        load any documents.
        '''
        
        # Initialize database.
        self.initDB()
        
        # Select-upsert Congress object.
        cursor = self.connection.cursor()
        
        # Execute select.
        cursor.execute("SELECT id FROM congress WHERE id=?", (self.id,))
        rows = cursor.fetchall()
        
        # Insert this congress.
        if len(rows) == 0:
            cursor.execute("INSERT INTO congress (id) VALUES (?)", (self.id,))
        
        # Now fetch the list of documents.
        cursor.execute("SELECT id FROM document WHERE congress_id=?", (self.id,))
        for row in cursor:
            self.documents.append(row[0])

        # Close cursor.
        cursor.close()
        
    def updateIndexList(self):
        '''
        Get the index list of files on the remote GPO server.
        '''
        # Fetch the index buffer.
        indexBuffer = urllib2.urlopen(self.url).read()
        indexDoc = lxml.html.fromstring(indexBuffer)
        body = indexDoc.iterchildren(tag='body').next()
        bodyPre = body.iterchildren(tag='pre').next()
        
        self.index = []
        self.indexDate = {}
        
        # Iterate over all <pre> text.
        bodyText = [t.strip() for t in bodyPre.itertext()][9:]
        for i in range(len(bodyText) / 2):
            fileName = bodyText[2 * i]
            tokens = bodyText[2 * i + 1].split()

            # Skip strange lines.
            if len(tokens) != 3:
                continue

            # Check the file type.
            if fileName.lower().endswith('xml'):
                self.index.append(fileName)
                self.indexDate[fileName] = dateutil.parser.parse(tokens[0] + " " + tokens[1])

    
    def updateDocument(self, fileName):
        '''
        Update/download a file based on filename.
        '''
        
        filePath = "{0}/{1}".format(self.dataPath, fileName)
        
        if not os.path.exists(filePath):
            print 'Fetching {0} from remote.'.format(filePath)
            
            # Read the page buffer.
            pageURI = "{0}/{1}".format(self.url, fileName)
            pageBuffer = urllib2.urlopen(pageURI).read()
            
            # Store into data.
            pageFile = open(filePath, 'w')
            pageFile.write(pageBuffer)
            pageFile.close()
        else:
            # Read data.
            print 'Reading {0} from local cache.'.format(filePath)
            pageFile = open(filePath, 'r')
            pageBuffer = pageFile.read()
            pageFile.close()            
        
        # Parse the file now.
        self.parseDocument(fileName, pageBuffer)
    
    def parseDocument(self, fileName, fileBuffer):
        '''
        Parse a document to update the database.
        '''
        doc = Document(fileBuffer)
        
        # Print errors and return if not valid.
        if doc.valid != True:
            print fileName, doc.exceptions
            return
        
        # Otherwise, populate database.
        cursor = self.connection.cursor()
        
        # Insert document and store the row ID.
        cursor.execute("INSERT INTO document (filename, congress_id, session, published, citation, type, title, stage, chamber) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (fileName, self.id, doc.session, self.indexDate[fileName], doc.cite, doc.type, doc.title, doc.stage, doc.chamber))
        docId = cursor.lastrowid
        
        cursor.executemany("INSERT INTO document_statistics (document_id, statistic_id, statistic_value) VALUES (?,?,?)",
                           ((docId, "Sections", doc.sectionCount),
                            (docId, "Sentences", doc.sentenceCount),
                            (docId, "Words", doc.tokenCount),
                            (docId, "Uniq. Words", doc.uniqTokenCount),
                            (docId, "Uniq. Stems", doc.uniqStemCount),
                            (docId, "Reading Level", doc.readingLevel),
                            (docId, "Avg. Word Length", doc.avgCharsPerWord),
                            (docId, "Avg. Sentence Length", doc.avgWordsPerSentence))) 
        
        self.connection.commit()
        
        # Close cursor.
        cursor.close()
        
    
    def update(self, overwrite=False):
        '''
        Update the database and filesystem from remote GPO data.
        '''
        
        # Create data and report directories if not exist.
        if not os.path.exists('data'):
            os.mkdir('data')
            
        # Get the index of files on the remote server.
        self.updateIndexList()
        
        for fileName in self.index:
            # Only download files that are not in the index.
            if overwrite == False and fileName in self.documents:
                continue
            
            # Otherwise, download and parse.
            self.updateDocument(fileName)

if __name__ == "__main__":
    C = Congress(112)
    C.update()
    print C
        
        
        
    
    
