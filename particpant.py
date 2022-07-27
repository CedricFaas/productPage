import random
import csv
import os
import tracker
from element import Element 

class Participant:
    
    def __init__(self,id):
        self.participantId = id
        self.productSets = list(range(1,41))
        random.shuffle(self.productSets)
        self.currentSet = 0
        self.higlightS = [11,12,17,19,20,33,34,35,36,37,38,39,40]
        self.higlightM = [2,3,4,5,9,13,14,15,16,18,24,29,30,31,32]
        self.higlightL = [1,6,7,8,10,21,22,23,25,26,27,28]
        self.highlightingTechniquesS = list(range(4))+list(range(4))+list(range(4))+[0]
        self.highlightingTechniquesM = list(range(4))+list(range(4))+list(range(4))+list(range(1,4))
        self.highlightingTechniquesL = list(range(4))+list(range(4))+list(range(4))
        random.shuffle(self.highlightingTechniquesS)
        random.shuffle(self.highlightingTechniquesM)
        random.shuffle(self.highlightingTechniquesL)
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
        self.currentHighlightingTechnique = 0
        if self.tested:
            if (self.currentSet in self.higlightS):
                self.currentHighlightingTechnique = self.highlightingTechniquesS.pop()
            elif (self.currentSet in self.higlightM):
                self.currentHighlightingTechnique = self.highlightingTechniquesM.pop()
            elif (self.currentSet in self.higlightL):
                self.currentHighlightingTechnique = self.highlightingTechniquesL.pop()
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
        while os.path.exists(self.currPath + ".csv"):
            n = n+1
            self.currPath = dirName + "/gazeData/gaze" + "_" + str(self.currentSet)+"_"+str(currProd) + "_" + str(self.currentHighlightingTechnique) + "_" + str(n)
        self.eyeTracker = tracker.startTracking(self.currPath)
        
    
    def stopTracking(self, prod):
        tracker.stopTracking(self.eyeTracker)
        self.eyeTracker = None
        
        