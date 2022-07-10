import random
import csv
import os

class Participant:
    
    def __init__(self,id):
        self.participantId = id
        self.productSets = list(range(1,41))
        random.shuffle(self.productSets)
        self.currentSet = None
        self.highlightingTechniques = list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))
        random.shuffle(self.highlightingTechniques)
        self.currentHighlightingTechnique = None
        self.paused = True
        self.decisions = {}
        
    def getId(self):
        return self.participantId
        
    def nextProductSet(self):
        self.currentSet = self.productSets.pop()
        return self.currentSet
    
    def getProductSet(self):
        return self.currentSet
        
    def remainingSets(self):
        return len(self.productSets)
    
    def nextHighlightingTechnique(self):
        self.currentHighlightingTechnique = self.highlightingTechniques.pop()
        return self.currentHighlightingTechnique
    
    def isPaused(self):
        return self.paused
    
    def pause(self):
        self.paused = True
    
    def endPause(self):
        self.paused = False
        
    def saveDecision(self, productSet, product, inTime):
        self.decisions.update({str(productSet): (productSet, product, self.currentHighlightingTechnique, inTime)})
        
    def generateLogFiles(self):
        global dirName 
        dirName= './log/p'+str(self.participantId)
        while os.path.exists(dirName):
            dirName = dirName+'_IdColl'
            
        os.mkdir(dirName)
            
    
    def printDecisions(self):    
        with open(dirName + '/decisions.csv', 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            while self.decisions:
                item = self.decisions.popitem()
                filewriter.writerow([item[1][0],item[1][1],item[1][2],item[1][3]])
        