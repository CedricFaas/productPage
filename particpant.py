import random
import csv
import os
import tobii_research as tobii
from element import Element 

class Participant:
    
    filePath = None
    visit1 = 0
    visit2 = 0
    visit3 = 0
    visit4 = 0
    visit5 = 0
    
    def __init__(self,id):
        self.participantId = id
        self.productSets = list(range(1,41))
        random.shuffle(self.productSets)
        self.currentSet = 0
        self.currentProduct = 0
        self.currentVisit = 0
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
        self.currentHighlightingTechnique = 0
        if self.tested:
            if (self.currentSet in self.higlightS):
                self.currentHighlightingTechnique = self.highlightingTechniquesS.pop()
            elif (self.currentSet in self.higlightM):
                self.currentHighlightingTechnique = self.highlightingTechniquesM.pop()
            elif (self.currentSet in self.higlightL):
                self.currentHighlightingTechnique = self.highlightingTechniquesL.pop()
            
        self.currentSet = self.productSets.pop()
        return self.currentSet
    
    def getProductSet(self):
        return self.currentSet
        
    def remainingSets(self):
        return len(self.productSets)
    
    def getHighlightingTechnique(self):
        return self.currentHighlightingTechnique
    
    def saveProduct(self, prod):
        self.currentProduct = prod
        if (prod == 1):
            global visit1
            visit1 = visit1 + 1
            self.currentVisit = visit1
        elif (prod == 2):
            global visit2
            visit2 = visit2 + 1
            self.currentVisit = visit2
        elif (prod == 3):
            global visit3
            visit3 = visit3 + 1
            self.currentVisit = visit3
        elif (prod == 4):
            global visit4
            visit4 = visit4 + 1
            self.currentVisit = visit4
        elif (prod == 5):
            global visit5
            visit5 = visit5 + 1
            self.currentVisit = visit5
                
                
    
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
    
    def startTracking(self):
        global filePath
        self.currPath = dirName + "/gazeData/gaze" + "_" + str(self.currentSet)+ "_"+ str(self.currentHighlightingTechnique)
        filePath = self.currPath
        self.eyeTracker = tobii.findEyeTracker()
        with open(filePath + '.csv',  'a') as csvfile, open(filePath + '_FULL' + '.csv', "a") as full_csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            full_filewriter = csv.writer(full_csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

            filewriter.writerow(['ProductId','Visited','LeftGazePointX', 'LeftGazePointY','LeftGazePointValidity', 'RightGazePointX', 'RightGazePointY','RightGazePointValidity','Timestamp'])
            full_filewriter.writerow(
                    ['ProductId','Visited','RightPupilValidity', 'RightPupilDiameter', 'LeftPupilValidity', 'LeftPupilDiameter',
                        'RightGazePointValidity', 'RightGazePointOnDisplayAreaX', 'RightGazePointOnDisplayAreaY',
                        'RightGazePointInUserCoordinateSystemX', 'RightGazePointInUserCoordinateSystemY',
                        'RightGazePointInUserCoordinateSystemZ', 'LeftGazePointValidity', 'LeftGazePointOnDisplayAreaX',
                        'LeftGazePointOnDisplayAreaY', 'LeftGazePointInUserCoordinateSystemX',
                        'LeftGazePointInUserCoordinateSystemY', 'LeftGazePointInUserCoordinateSystemZ',
                        'RightGazeOriginValidity', 'RightGazeOriginInUserCoordinateSystemX',
                        'RightGazeOriginInUserCoordinateSystemY', 'RightGazeOriginInUserCoordinateSystemZ',
                        'RightGazeOriginInTrackboxCoordinateSystemX', 'RightGazeOriginInTrackboxCoordinateSystemY',
                        'RightGazeOriginInTrackboxCoordinateSystemZ', 'LeftGazeOriginValidity',
                        'LeftGazeOriginInUserCoordinateSystemX', 'LeftGazeOriginInUserCoordinateSystemY',
                        'LeftGazeOriginInUserCoordinateSystemZ', 'LeftGazeOriginInTrackboxCoordinateSystemX',
                        'LeftGazeOriginInTrackboxCoordinateSystemY', 'LeftGazeOriginInTrackboxCoordinateSystemZ',
                        'SystemTimestamp', 'DeviceTimestamp'])
            self.eyeTracker.subscribe_to(tobii.EYETRACKER_GAZE_DATA, self.gaze_data_callback, as_dictionary=True)
            
        
        
        
    def stopTracking(self):
        global filePath
        print("Eye Tracker:")
        print(self.eyeTracker)
        self.eyeTracker.unsubscribe_from(tobii.EYETRACKER_GAZE_DATA, self.gaze_data_callback)
        filePath = None
        self.eyeTracker = None
        global visit1
        global visit2
        global visit3
        global visit4
        global visit5
        visit1 = 0
        visit2 = 0
        visit3 = 0
        visit4 = 0
        visit5 = 0
        self.currentVisit = 0

    ##### Callback function for eye tracker #####
    def gaze_data_callback(self,gaze_data):
        global filePath
        with open(filePath +'.csv',  'a') as csvfile, open(filePath + '_FULL' + '.csv', "a") as full_csvfile:
            filewriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
            full_filewriter = csv.writer(full_csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow([self.currentProduct,self.currentVisit,gaze_data['left_gaze_point_on_display_area'][0],gaze_data['left_gaze_point_on_display_area'][1],gaze_data['left_gaze_point_validity'],gaze_data['right_gaze_point_on_display_area'][0],gaze_data['right_gaze_point_on_display_area'][1],gaze_data['right_gaze_point_validity'],gaze_data['device_time_stamp']])
            full_filewriter.writerow([self.currentProduct,self.currentVisit,gaze_data['right_pupil_validity'],gaze_data['right_pupil_diameter'],gaze_data['left_pupil_validity'],gaze_data['left_pupil_diameter'],gaze_data['right_gaze_point_validity'],gaze_data['right_gaze_point_on_display_area'][0],gaze_data['right_gaze_point_on_display_area'][1],gaze_data['right_gaze_point_in_user_coordinate_system'][0],gaze_data['right_gaze_point_in_user_coordinate_system'][1],gaze_data['right_gaze_point_in_user_coordinate_system'][2],gaze_data['left_gaze_point_validity'],gaze_data['left_gaze_point_on_display_area'][0],gaze_data['left_gaze_point_on_display_area'][1],gaze_data['left_gaze_point_in_user_coordinate_system'][0],gaze_data['left_gaze_point_in_user_coordinate_system'][1],gaze_data['left_gaze_point_in_user_coordinate_system'][2],gaze_data['right_gaze_origin_validity'],gaze_data['right_gaze_origin_in_user_coordinate_system'][0],gaze_data['right_gaze_origin_in_user_coordinate_system'][1],gaze_data['right_gaze_origin_in_user_coordinate_system'][2],gaze_data['right_gaze_origin_in_trackbox_coordinate_system'][0],gaze_data['right_gaze_origin_in_trackbox_coordinate_system'][1],gaze_data['right_gaze_origin_in_trackbox_coordinate_system'][2],gaze_data['left_gaze_origin_validity'],gaze_data['left_gaze_origin_in_user_coordinate_system'][0],gaze_data['left_gaze_origin_in_user_coordinate_system'][1],gaze_data['left_gaze_origin_in_user_coordinate_system'][2],gaze_data['left_gaze_origin_in_trackbox_coordinate_system'][0],gaze_data['left_gaze_origin_in_trackbox_coordinate_system'][1],gaze_data['left_gaze_origin_in_trackbox_coordinate_system'][2],gaze_data['system_time_stamp'],gaze_data['device_time_stamp']])        
    
    