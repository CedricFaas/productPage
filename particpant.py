import random
import csv
import os
import tracker
import analyse
from element import Element 

class Participant:
    
    def __init__(self,id):
        self.participantId = id
        self.productSets = list(range(1,41))
        random.shuffle(self.productSets)
        self.currentSet = 0
        self.highlightingTechniques = list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))
        random.shuffle(self.highlightingTechniques)
        self.currentHighlightingTechnique = None
        self.paused = True
        self.tested = False
        self.decisions = {}
        self.currPath = ""
        self.eyeTracker = None
        self.elements = []
        
    def getId(self):
        return self.participantId
        
    def nextProductSet(self):
        if self.tested:
            self.currentSet = self.productSets.pop()
        return self.currentSet
    
    def getProductSet(self):
        return self.currentSet
        
    def remainingSets(self):
        return len(self.productSets)
    
    def nextHighlightingTechnique(self):
        if self.tested:
            self.currentHighlightingTechnique = self.highlightingTechniques.pop()
        else:
            self.currentHighlightingTechnique = 0
        return self.currentHighlightingTechnique
    
    def test(self):
        self.tested = True
    
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
        os.mkdir(dirName+"/gazeData")

        with open(dirName+'/metrics.csv', 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow(['ID','Set','ProductId','Visited','Highlighting','AOI','TFF','FPG','SPG','RFX','SFX','ODT'])
    
    def printDecisions(self):    
        with open(dirName + '/decisions.csv', 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            while self.decisions:
                item = self.decisions.popitem()
                filewriter.writerow([item[1][0],item[1][1],item[1][2],item[1][3]])
    
    def generateElement(self, aoiCode, x1, y1, x2, y2):
        self.elements.append(Element(aoiCode, x1, y1, x2, y2))
    
    def startTracking(self, currProd):
        global n 
        n = 1
        self.currPath = dirName + "/gazeData/gaze" + "_" + str(self.currentSet)+"_"+str(currProd) + "_" + str(self.currentHighlightingTechnique) + "_" + str(n)
        while os.path.exists(self.currPath):
            n = n+1
            self.currPath = dirName + "/gazeData/gaze" + "_" + str(self.currentSet)+"_"+str(currProd) + "_" + str(self.currentHighlightingTechnique) + "_" + str(n)
        self.eyeTracker = tracker.startTracking(self.currPath)
        
    
    def stopTracking(self, prod):
        tracker.stopTracking(self.eyeTracker)
        self.eyeTracker = None
        
        self.elements = analyse.analyseDataset(self.elements,self.currentSet,prod,self.currPath+".csv")
        with open(dirName+'/metrics.csv', 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for elem in self.elements:
                row = []
                row.append(str(self.participantId))
                row.append(str(self.currentSet))
                row.append(str(prod))
                row.append(str(n))
                row.append(str(self.currentHighlightingTechnique))
                row.append(str(elem.aoiCode))
                row.append(str(elem.metrics[str(self.currentSet*10+prod)]['timeToFirstFixation']))
                row.append(str(elem.metrics[str(self.currentSet*10+prod)]['firstPassGazeDuration']))
                row.append(str(elem.metrics[str(self.currentSet*10+prod)]['secondPassGazeDuration']))
                row.append(str(elem.metrics[str(self.currentSet*10+prod)]['refixationsCount']))
                row.append(str(elem.metrics[str(self.currentSet*10+prod)]['sumOfFixations']))
                row.append(str(elem.metrics[str(self.currentSet*10+prod)]['overallDwellTime']))
                filewriter.writerow(row)
        