'''
Created on Feb 15, 2012
@author: mjbommar
'''


import dateutil.parser
import lxml.html
import nltk
import nltk_contrib.readability.readabilitytests
import re

class Document(object):
    '''
    The Document class handles parsing and storing 
    data about a GPO document.
    '''
    
    def __init__(self, buffer=None):
        '''
        Constructor.
        '''
        
        # Initialize local fields.
        self.buffer = buffer
        self.session = None
        self.date = None
        self.cite = None
        self.type = None
        self.title = None
        self.stage = None
        self.chamber = None
        self.text = None
        self.sentences = None
        self.tokens = []
        self.tokenFreq = {}
        self.stems = []
        self.stemFreq = {}
        self.readability = None
        self.sectionCount = 0
        self.sentenceCount = 0
        self.tokenCount = 0
        self.uniqTokenCount = 0
        self.uniqStemCount = 0
        self.avgWordsPerSentence = 0.0
        self.avgCharsPerWord = 0.0
        
        # Parsing values
        self.valid = True
        self.exceptions = []
        
        # NLTK stemmer and stopwords.
        self.stemmer = nltk.stem.PorterStemmer()
        self.stopwords = nltk.corpus.stopwords.words("english")
        
        self.parseDocument()
        
    def matchFirstXPath(self, expression):
        '''
        Match the first element that meets the XPath expression.
        '''
        elementList = self.document.xpath(expression)
        
        if len(elementList) > 0:
            return elementList[0]
        else:
            return None
    
    def parseDocument(self):
        '''
        Parse the document.
        '''
        
        # Parse the document or report an error.
        try:
            self.document = lxml.etree.fromstring(self.buffer)
        except Exception, E:
            self.exceptions.append(E)
            self.valid = False
            return
        
        # Identify each of the document variables.
        try:
            self.parseDate()
            self.parseCongress()
            self.parseSession()
            self.parseLegislationNumber()
            self.parseLegislationType()
            self.parseLegislationTitle()
            self.parseStage()
            self.parseCurrentChamber()
            self.parseText()
        except Exception, E:
            self.exceptions.append(E)
            self.valid = False
            return
    
    def parseDate(self):
        '''
        Parse the dc:date flag.
        '''
        elementDate = self.matchFirstXPath('/bill/dublinCore/date')
        
        if elementDate != None:
            self.date = dateutil.parser.parse(' '.join([t for t in elementDate.itertext()]))
    
    def parseCongress(self):
        '''
        Parse the congress.
        '''
        elementCongress = self.matchFirstXPath('/bill/form/congress')

        if elementCongress != None:
            self.congress = ' '.join([t for t in elementCongress.itertext()])

    def parseSession(self):
        '''
        Parse the session.
        '''
        elementSession = self.matchFirstXPath('/bill/form/session')

        if elementSession != None:
            self.session = ' '.join([t for t in elementSession.itertext()])

    def parseLegislationNumber(self):
        '''
        Parse the legislation number.
        '''
        elementLegislationNumber = self.matchFirstXPath('/bill/form/legis-num')

        if elementLegislationNumber != None:
            self.cite = ' '.join([t for t in elementLegislationNumber.itertext()])

    def parseLegislationType(self):
        '''
        Parse the legislation type.
        '''
        elementLegislationType = self.matchFirstXPath('/bill/form/legis-type')

        if elementLegislationType != None:
            self.type = ' '.join([t for t in elementLegislationType.itertext()])

    def parseLegislationTitle(self):
        '''
        Parse the legislation title.
        '''
        elementLegislationTitle = self.matchFirstXPath('/bill/form/official-title')

        if elementLegislationTitle != None:
            self.title = ' '.join([t for t in elementLegislationTitle.itertext()])
            self.title = self.title.replace(u"\u2019", "-")

    def parseStage(self):
        '''
        Parse the stage.
        '''
        if 'bill-stage' in self.document.attrib:
            self.stage = self.document.attrib['bill-stage']
        
    def parseCurrentChamber(self):
        '''
        Parse the current chamber.
        '''
        elementCurrentChamber = self.matchFirstXPath('/bill/form/current-chamber')

        if elementCurrentChamber != None:
            self.chamber = ' '.join([t for t in elementCurrentChamber.itertext()])
    
    def parseText(self):
        '''
        Extract the document text.
        '''
        # Extract text from legis-body.
        legisBody = self.matchFirstXPath('/bill/legis-body')
        
        # Number of sections
        sectionList = legisBody.xpath('//section')
        self.sectionCount = len(sectionList)

        textList = legisBody.xpath('//text')
        self.text = unicode("")
        for text in textList:
            curText = unicode(" ").join([unicode(t.strip()) for t in text.itertext() if t.strip()])
            curText = re.sub("\s{2,}", " ", curText, re.UNICODE)
            self.text += curText + unicode("\n")

        # Build sentence, token, and stem lists and sets.
        self.sentences = nltk.sent_tokenize(self.text)
        self.tokens = nltk.word_tokenize(self.text)
        self.stems = [self.stemmer.stem(t) for t in self.tokens]
        self.tokenFreq = nltk.FreqDist(self.tokens)
        self.stemFreq = nltk.FreqDist(self.stems)
        
        # Get some counts.
        self.sentenceCount = len(self.sentences)
        self.tokenCount = len(self.tokens)
        self.uniqTokenCount = len(self.tokenFreq)
        self.uniqStemCount = len(self.stemFreq)
        
        # Calculate reading level.
        self.readability = nltk_contrib.readability.readabilitytests.ReadabilityTool(self.text)
        self.readingLevel = self.readability.FleschKincaidGradeLevel()
        self.avgCharsPerWord = self.readability.analyzedVars['charCount'] / self.readability.analyzedVars['wordCount']
        self.avgWordsPerSentence = self.readability.analyzedVars['wordCount'] / self.readability.analyzedVars['sentenceCount']
