from __future__ import division
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ctypes
import detectors
import csv
from element import Element
from os.path import exists
from scipy.stats import norm

pAmount = 518

""""
Inputs dataset and list of all UI elements
Computes all metrics for each element
Returns updated version of elements
"""
def analyseDataset(elements,prodId,dataset):
    elements = elements
    #Add new metric entry to metrics dictionairy of each element
    for elem in elements:
        elem.metrics[prodId] = {
        'timeToFirstFixation' : 0,
        'firstPassGazeDuration': 0,
        'secondPassGazeDuration': 0,
        'refixationsCount': 0,
        'sumOfFixations': 0,
        'overallDwellTime': 0,
    }

    #Loading new dataset
    gazeData = dataset

    #Run validity check and filtering
    gazeData = filterUnvalidEntries(gazeData)
    gazeData = computeActualGazePoint(gazeData)
    gazeData = filterOffDisplayValues(gazeData)
    gazeData.reset_index()

    #If no gaze data returm elements
    if gazeData.empty or len(gazeData) == 1:
        return elements
    else:
        pass

    #Extract timestamps, coordinates and events
    timestamps = getTimestampsInMilliseconds(gazeData)
    x_gazePoints, width = getXGazePointsAsPixel(gazeData)
    y_gazePoints, height = getYGazePointsAsPixel(gazeData)
    x_gazePoints, y_gazePoints, timestamps = discardEdgeGazePoints(x_gazePoints,y_gazePoints,timestamps, elements)

    fixations = detectors.fixation_detection(x_gazePoints, y_gazePoints, timestamps, mindur=10)

    #If no fixation were detected return elements
    if len(fixations) == 0 or len(timestamps) == 0:
        return elements
    else:
        pass

    ##################################################
    ######## Start with metric computation ###########
    ##################################################

    #Time to first fixation -- Orientation
    #First pass gaze duration -- Orientation
    #Second pass gaze duration -- Evaluation
    #Refixations count -- Evaluation
    elements = computeTemporalFixationMetrices(fixations,elements,prodId)

    #Sum of fixations -- Verification
    elements = computeSumOfFixations(fixations,elements,prodId)

    #Overall Dwell Time -- Verification
    elements = computeDwellTime(x_gazePoints,y_gazePoints,timestamps,elements,prodId)

    return elements


######### Helper methods to filter and process dataframe ###########

#Map points to elements
def mapToAOI(x,y,elements):
    for e in elements:
        if (x in np.arange(e.boundaries[0],e.boundaries[2]+1)):
            if (y in np.arange(e.boundaries[1],e.boundaries[3]+1)):
                return e.aoiCode
    return 'OFF'

#Get element from aoiCode
def getElementOfAOI(elements,aoi):
    for e in elements:
        if (aoi == e.aoiCode):
            return e


#Delete all unvalid gaze data
def filterUnvalidEntries(dataframe):
    validLeft = dataframe[dataframe['LeftGazePointValidity'] == 1]
    allValid = validLeft[validLeft['RightGazePointValidity'] == 1]
    return allValid


#Compute GazePoint from Left and Right Eye GazeData
def computeActualGazePoint(dataframe):
    actualGazePointX = []
    actualGazePointY = []

    for index, row in dataframe.iterrows():
        leftX = row['LeftGazePointX']
        leftY = row['LeftGazePointY']
        rightX = row['RightGazePointX']
        rightY = row['RightGazePointY']

        actualX = leftX+(rightX-leftX)/2
        actualY = leftY+(rightY-leftY)/2

        actualGazePointX.append(actualX)
        actualGazePointY.append(actualY)

    s = pd.Series(actualGazePointX)
    t = pd.Series(actualGazePointY)
    dataframe = dataframe.assign(ActualGazePointX=s.values)
    dataframe = dataframe.assign(ActualGazePointY=t.values)
    return dataframe

#Remove all off Display values
def filterOffDisplayValues(dataframe):

    inboundAll = dataframe[dataframe['ActualGazePointX'] <= 1]
    inboundAll = inboundAll[inboundAll['ActualGazePointX'] >= 0]

    inboundAll = inboundAll[inboundAll['ActualGazePointY'] <= 1]
    inboundAll = inboundAll[inboundAll['ActualGazePointY'] >= 0]

    return inboundAll

def  getTimestampsInMilliseconds(dataframe):
    time = dataframe.Timestamp
    time.reset_index(drop=True, inplace=True)
    t_temp = []
    initalTime = time[1]/1000
    for t in time[1:]:
        #print(round(t/1000-initalTime))
        t_temp.append(t/1000-initalTime)
    return t_temp

def getXGazePointsAsPixel(dataframe):
    #user32 = ctypes.windll.user32
    #width = user32.GetSystemMetrics(0)
    width = 1535
    x_temp = []
    actualX = dataframe['ActualGazePointX']
    for x in actualX[1:]:
        x_temp.append(round(x*width))
    return x_temp, width


def getYGazePointsAsPixel(dataframe):
    #user32 = ctypes.windll.user32
    #height = user32.GetSystemMetrics(1)
    height = 863
    y_temp = []
    actualY = dataframe['ActualGazePointY']
    for y in actualY[1:]:
        y_temp.append(round(y*height))
    return y_temp, height

def discardEdgeGazePoints(x_gazePoints, y_gazePoints, timestamp, elements):
    x_temp = []
    y_temp = []
    time_temp = []
    for i in range(0,len(x_gazePoints)):
        aoi = mapToAOI(x_gazePoints[i],y_gazePoints[i],elements)
        if aoi != 'OFF':
            x_temp.append(x_gazePoints[i])
            y_temp.append(y_gazePoints[i])
            time_temp.append(timestamp[i])
    return x_temp, y_temp, time_temp


######### Computation of single metrics ###########

#Compute temporal fixation metrices
#Inputs list of detected fixations and elements
#Computes Time to firs fixation, first- and second-pass-gaze as well as refixation count
def computeTemporalFixationMetrices(fixations,elements,prodId):
    firstPass = 0
    secondPass = 0
    for i in np.arange(0, len(fixations)-1, 1):
        aoi_one = mapToAOI(fixations[i][3], fixations[i][4],elements)
        aoi_two = mapToAOI(fixations[i + 1][3], fixations[i + 1][4], elements)
        elem = getElementOfAOI(elements, aoi_one)
        if elem.metrics[prodId]['timeToFirstFixation'] == 0:
            elem.metrics[prodId]['timeToFirstFixation'] = fixations[i][0]
            firstPass = fixations[i][2]
        secondPass = secondPass + fixations[i][2]
        if aoi_one == aoi_two:
            firstPass = firstPass+fixations[i+1][2]
            secondPass = secondPass + fixations[i+1][2]
        else:
            if elem.metrics[prodId]['refixationsCount'] == 0:
                elem.metrics[prodId]['firstPassGazeDuration'] = firstPass
            elif elem.metrics[prodId]['refixationsCount'] == 1:
                elem.metrics[prodId]['secondPassGazeDuration'] = secondPass
            firstPass = 0
            secondPass = 0
            elem.metrics[prodId]['refixationsCount'] += 1
    aoi_last = mapToAOI(fixations[(len(fixations) - 1)][3], fixations[(len(fixations) - 1)][4], elements)
    elem = getElementOfAOI(elements, aoi_last)
    if firstPass != 0 or secondPass != 0:
        if elem.metrics[prodId]['refixationsCount'] == 0:
            elem.metrics[prodId]['firstPassGazeDuration'] = firstPass
        elif elem.metrics[prodId]['refixationsCount'] == 1:
            elem.metrics[prodId]['secondPassGazeDuration'] = secondPass
    elem.metrics[prodId]['refixationsCount'] += 1
    return elements

#Compute sum of fixations
def computeSumOfFixations(fixations,elements,prodId):
    for fix in fixations:
        aoi_hit = mapToAOI(fix[3],fix[4],elements)
        elem = getElementOfAOI(elements,aoi_hit)
        elem.metrics[prodId]['sumOfFixations'] += 1
    return elements

#Compute overall Dwell Time
def computeDwellTime(x_gazePoints,y_gazePoints,timestamps,elements,prodId):
    current = 0
    startT = 0
    lastT = 0
    for i in np.arange(1, len(timestamps), 1):
        x = x_gazePoints[i]
        y = y_gazePoints[i]
        t = timestamps[i]
        aoi = mapToAOI(x, y, elements)
        if current == 0:
            current = aoi
            startT = t
        elif aoi == current and i != len(timestamps) - 1:
            lastT = t
        else:
            try:
                d = lastT - startT  # add to aoi dwell time
                e = getElementOfAOI(elements, current)
                e.metrics[prodId]['overallDwellTime'] = e.metrics[prodId]['overallDwellTime'] + d
                current = aoi
                startT = t
                lastT = t
            except AttributeError:
                current = aoi
                print ('Error')
                print (i)
    return elements
# reads area of interest elements out of csv file
# returns a set containing 40 sets (one for each decision), which contain
# 5 sets each (one for each product), containg the aois of each product 
def readElements():
    file = pd.read_csv('./calcAoI/aois.csv')
    sets = []
    products1 = []
    sets.append(products1)
    products2 = []
    sets.append(products2)
    products3 = []
    sets.append(products3)
    products4 = []
    sets.append(products4)
    products5 = []
    sets.append(products5)
    products6 = []
    sets.append(products6)
    products7 = []
    sets.append(products7)
    products8 = []
    sets.append(products8)
    products9 = []
    sets.append(products9)
    products10 = []
    sets.append(products10)
    products11 = []
    sets.append(products11)
    products12 = []
    sets.append(products12)
    products13 = []
    sets.append(products13)
    products14 = []
    sets.append(products14)
    products15 = []
    sets.append(products15)
    products16 = []
    sets.append(products16)
    products17 = []
    sets.append(products17)
    products18 = []
    sets.append(products18)
    products19 = []
    sets.append(products19)
    products20 = []
    sets.append(products20)
    products21 = []
    sets.append(products21)
    products22 = []
    sets.append(products22)
    products23 = []
    sets.append(products23)
    products24 = []
    sets.append(products24)
    products25 = []
    sets.append(products25)
    products26 = []
    sets.append(products26)
    products27 = []
    sets.append(products27)
    products28 = []
    sets.append(products28)
    products29 = []
    sets.append(products29)
    products30 = []
    sets.append(products30)
    products31 = []
    sets.append(products31)
    products32 = []
    sets.append(products32)
    products33 = []
    sets.append(products33)
    products34 = []
    sets.append(products34)
    products35 = []
    sets.append(products35)
    products36 = []
    sets.append(products36)
    products37 = []
    sets.append(products37)
    products38 = []
    sets.append(products38)
    products39 = []
    sets.append(products39)
    products40 = []
    sets.append(products40)
    for index, row in file.iterrows():
        aoiId = int(row['Id'])
        setId = int(aoiId / 100)
        
        x1 = row['x1']
        x2 = row['x2']
        y1 = row['y1']
        y2 = row['y2']
        
        diffX = x2 - x1
        diffY = y2 - y1
        
        if (diffX <= 40):
            diffX = int((40-diffX)/2)
            x1 = x1 - diffX
            x2 = x2 - diffX
        if (diffY <= 40):
            diffY = int((40-diffY)/2)
            y1 = y1 - diffY
            y2 = y2 + diffY
        
        sets[setId-1].append(Element(aoiId,x1,y1,x2,y2))
    newSets = []
    for productSet in sets:
        product = []
        aois0 = []
        product.append(aois0)
        aois1 = []
        product.append(aois1)
        aois2 = []
        product.append(aois2)
        aois3 = []
        product.append(aois3)
        aois4 = []
        product.append(aois4)
        aois5 = []
        product.append(aois5)
        for aoi in productSet:
            aoiId = int((aoi.aoiCode % 100)/10)
            product[aoiId].append(aoi)
        newSets.append(product)
    return newSets

def analyse():
    sets = readElements()
    pId = 501
    while (pId <= pAmount):
        productSet = 1
        dirName = './log/p'+str(pId)
        while (productSet <= 40):
            file = None
            highlighting = 0
            
            if exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_0.csv'):
                highlighting = 0
                file = pd.read_csv('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_0.csv')
                
            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_1.csv'):
                highlighting = 1
                file = pd.read_csv('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_1.csv')
                
            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_2.csv'):
                highlighting = 2
                file = pd.read_csv('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_2.csv')
                
            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_3.csv'):
                highlighting = 3
                file = pd.read_csv('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_3.csv')
            
            if file is not None:
                gaze0 = file[file.ProductId == 0]
                gaze1 = file[file.ProductId == 1]
                gaze2 = file[file.ProductId == 2]
                gaze3 = file[file.ProductId == 3]
                gaze4 = file[file.ProductId == 4]
                gaze5 = file[file.ProductId == 5]
                sets[productSet-1][0] = analyseDataset(sets[productSet-1][0], str(10*productSet), gaze0)
                sets[productSet-1][1] = analyseDataset(sets[productSet-1][1], str(10*productSet+1), gaze1)
                sets[productSet-1][2] = analyseDataset(sets[productSet-1][2], str(10*productSet+2), gaze2)
                sets[productSet-1][3] = analyseDataset(sets[productSet-1][3], str(10*productSet+3), gaze3)
                sets[productSet-1][4] = analyseDataset(sets[productSet-1][4], str(10*productSet+4), gaze4)
                sets[productSet-1][5] = analyseDataset(sets[productSet-1][5], str(10*productSet+5), gaze5)
                
                i = 0
                while (i <= 5):
                    aois = sets[productSet-1][i]
                    for elem in aois:
                        with open(dirName+'/metrics'+str(pId)+'_40px_10ms_sanity_custom2.csv', 'a') as csvfile:
                            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                            row = []
                            row.append(str(pId))
                            row.append(str(highlighting))
                            row.append(str(elem.aoiCode))
                            row.append(str(elem.metrics[str(10*productSet+i)]['timeToFirstFixation']))
                            row.append(str(elem.metrics[str(10*productSet+i)]['firstPassGazeDuration']))
                            row.append(str(elem.metrics[str(10*productSet+i)]['secondPassGazeDuration']))
                            row.append(str(elem.metrics[str(10*productSet+i)]['refixationsCount']))
                            row.append(str(elem.metrics[str(10*productSet+i)]['sumOfFixations']))
                            row.append(str(elem.metrics[str(10*productSet+i)]['overallDwellTime']))
                            filewriter.writerow(row)
                    i=i+1
            productSet = productSet + 1
        pId = pId + 1
        
def createDiagrams():
    #[total sum of fixations, amount of aois]
    sumOfFixations0 = [0,0]
    sumOfFixations1 = [0,0]
    sumOfFixations2 = [0,0]
    sumOfFixations3 = [0,0]
    
    timeToFirstFixation0 = [0,0]
    timeToFirstFixation1 = [0,0]
    timeToFirstFixation2 = [0,0]
    timeToFirstFixation3 = [0,0]
    
    overallDwellTime0 = [0,0]
    overallDwellTime1 = [0,0]
    overallDwellTime2 = [0,0]
    overallDwellTime3 = [0,0]
    
    pId = 501
    
    while pId <= pAmount:
        path = './log/p'+str(pId)+'/metrics'+str(pId)+'_50px_10ms.csv'
        if (exists(path)):
            file = pd.read_csv(path)
            for row in file.itertuples():
                
                if (row[2]==0):
                    if (row[8]!=0):
                        sumOfFixations0[0] = sumOfFixations0[0] + row[8]
                        sumOfFixations0[1] = sumOfFixations0[1] + 1
                    if (row[4]!=0):
                        timeToFirstFixation0[0] = timeToFirstFixation0[0] + row[4]
                        timeToFirstFixation0[1] = timeToFirstFixation0[1] + 1
                    if (row[9]!=0):
                        overallDwellTime0[0] = overallDwellTime0[0] + row[9]
                        overallDwellTime0[1] = overallDwellTime0[1] + 1
                elif (row[2]==1):
                    if (row[8]!=0):
                        sumOfFixations1[0] = sumOfFixations1[0] + row[8]
                        sumOfFixations1[1] = sumOfFixations1[1] + 1
                    if (row[4]!=0):
                        timeToFirstFixation1[0] = timeToFirstFixation1[0] + row[4]
                        timeToFirstFixation1[1] = timeToFirstFixation1[1] + 1
                    if (row[9]!=0):
                        overallDwellTime1[0] = overallDwellTime1[0] + row[9]
                        overallDwellTime1[1] = overallDwellTime1[1] + 1
                elif (row[2]==2):
                    if (row[8]!=0):
                        sumOfFixations2[0] = sumOfFixations2[0] + row[8]
                        sumOfFixations2[1] = sumOfFixations2[1] + 1
                    if (row[4]!=0):
                        timeToFirstFixation2[0] = timeToFirstFixation2[0] + row[4]
                        timeToFirstFixation2[1] = timeToFirstFixation2[1] + 1
                    if (row[9]!=0):
                        overallDwellTime2[0] = overallDwellTime2[0] + row[9]
                        overallDwellTime2[1] = overallDwellTime2[1] + 1
                elif (row[2]==3):
                    if (row[8]!=0):
                        sumOfFixations3[0] = sumOfFixations3[0] + row[8]
                        sumOfFixations3[1] = sumOfFixations3[1] + 1
                    if (row[4]!=0):
                        timeToFirstFixation3[0] = timeToFirstFixation3[0] + row[4]
                        timeToFirstFixation3[1] = timeToFirstFixation3[1] + 1
                    if (row[9]!=0):
                        overallDwellTime3[0] = overallDwellTime3[0] + row[9]
                        overallDwellTime3[1] = overallDwellTime3[1] + 1
                                                                                
                
        pId = pId + 1
    sumOfFixations = [sumOfFixations0[0]/sumOfFixations0[1],sumOfFixations1[0]/sumOfFixations1[1],sumOfFixations2[0]/sumOfFixations2[1],sumOfFixations3[0]/sumOfFixations3[1]]
    timeToFirstFixation = [timeToFirstFixation0[0]/timeToFirstFixation0[1],timeToFirstFixation1[0]/timeToFirstFixation1[1],timeToFirstFixation2[0]/timeToFirstFixation2[1],timeToFirstFixation3[0]/timeToFirstFixation3[1]]
    overallDwellTime = [overallDwellTime0[0]/overallDwellTime0[1],overallDwellTime1[0]/overallDwellTime1[1],overallDwellTime2[0]/overallDwellTime2[1],overallDwellTime3[0]/overallDwellTime3[1]]
    print(sumOfFixations)
    print(timeToFirstFixation)
    print(overallDwellTime)
    
def createDiagramsStd():
    #[total sum of fixations, amount of aois]
    sumOfFixations0 = [[],0]
    sumOfFixations1 = [[],0]
    sumOfFixations2 = [[],0]
    sumOfFixations3 = [[],0]
    
    timeToFirstFixation0 = [[],0]
    timeToFirstFixation1 = [[],0]
    timeToFirstFixation2 = [[],0]
    timeToFirstFixation3 = [[],0]
    
    overallDwellTime0 = [[],0]
    overallDwellTime1 = [[],0]
    overallDwellTime2 = [[],0]
    overallDwellTime3 = [[],0]
    
    pId = 501
    
    while pId <= pAmount:
        path = './log/p'+str(pId)+'/metrics'+str(pId)+'_40px_10ms_sanity_custom2.csv'
        if (exists(path)):
            file = pd.read_csv(path)
            skip = False
            for row in file.itertuples():
                id = row[3]
                if ((id%100) == 0):
                    if (row[9] == 0):
                        skip = True
                    else:
                        skip = False
                    
                if not skip:
                    if (row[2]==0):
                        if (row[8]>=0):
                            sumOfFixations0[0].append(row[8])
                            sumOfFixations0[1] = sumOfFixations0[1] + 1
                        if (row[4]>0):
                            timeToFirstFixation0[0].append(row[4])
                            timeToFirstFixation0[1] = timeToFirstFixation0[1] + 1
                        if (row[9]>0):
                            overallDwellTime0[0].append(row[9])
                            overallDwellTime0[1] = overallDwellTime0[1] + 1
                    elif (row[2]==1):
                        if (row[8]>=0):
                            sumOfFixations1[0].append(row[8])
                            sumOfFixations1[1] = sumOfFixations1[1] + 1
                        if (row[4]>0):
                            timeToFirstFixation1[0].append(row[4])
                            timeToFirstFixation1[1] = timeToFirstFixation1[1] + 1
                        if (row[9]>0):
                            overallDwellTime1[0].append(row[9])
                            overallDwellTime1[1] = overallDwellTime1[1] + 1
                    elif (row[2]==2):
                        if (row[8]>=0):
                            sumOfFixations2[0].append(row[8])
                            sumOfFixations2[1] = sumOfFixations2[1] + 1
                        if (row[4]>0):
                            timeToFirstFixation2[0].append(row[4])
                            timeToFirstFixation2[1] = timeToFirstFixation2[1] + 1
                        if (row[9]>0):
                            overallDwellTime2[0].append( + row[9])
                            overallDwellTime2[1] = overallDwellTime2[1] + 1
                    elif (row[2]==3):
                        if (row[8]>=0):
                            sumOfFixations3[0].append(row[8])
                            sumOfFixations3[1] = sumOfFixations3[1] + 1
                        if (row[4]>0):
                            timeToFirstFixation3[0].append(row[4])
                            timeToFirstFixation3[1] = timeToFirstFixation3[1] + 1
                        if (row[9]>0):
                            overallDwellTime3[0].append(row[9])
                            overallDwellTime3[1] = overallDwellTime3[1] + 1
                                                                                
                
        pId = pId + 1
    
        
    # Fit a normal distribution to the data:
    mu = np.average(sumOfFixations0[0])
    std = np.std(sumOfFixations0[0])
    
    # Plot the histogram.
    
    plt.hist(sumOfFixations0[0],density=(True))
    
    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(sumOfFixations1[0])
    std = np.std(sumOfFixations1[0])

    # Plot the histogram.

    plt.hist(sumOfFixations1[0],density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(sumOfFixations2[0])
    std = np.std(sumOfFixations2[0])

    # Plot the histogram.

    plt.hist(sumOfFixations2[0],density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(sumOfFixations3[0])
    std = np.std(sumOfFixations3[0])

    # Plot the histogram.

    plt.hist(sumOfFixations3[0],density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(timeToFirstFixation0[0])
    std = np.std(timeToFirstFixation0[0])

    # Plot the histogram.

    plt.hist(timeToFirstFixation0[0],100,density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(timeToFirstFixation1[0])
    std = np.std(timeToFirstFixation1[0])

    # Plot the histogram.

    plt.hist(timeToFirstFixation1[0],100,density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(timeToFirstFixation2[0])
    std = np.std(timeToFirstFixation2[0])

    # Plot the histogram.

    plt.hist(timeToFirstFixation2[0],100,density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(timeToFirstFixation3[0])
    std = np.std(timeToFirstFixation3[0])

    # Plot the histogram.

    plt.hist(timeToFirstFixation3[0],100,density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(overallDwellTime0[0])
    std = np.std(overallDwellTime0[0])

    # Plot the histogram.

    plt.hist(overallDwellTime0[0],100,density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(overallDwellTime1[0])
    std = np.std(overallDwellTime1[0])

    # Plot the histogram.

    plt.hist(overallDwellTime1[0],100,density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(overallDwellTime2[0])
    std = np.std(overallDwellTime2[0])

    # Plot the histogram.

    plt.hist(overallDwellTime2[0],100,density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
    
    # Fit a normal distribution to the data:
    mu = np.average(overallDwellTime3[0])
    std = np.std(overallDwellTime3[0])

    # Plot the histogram.

    plt.hist(overallDwellTime3[0],100,density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, 100)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.show()
        
#analyse()
createDiagramsStd()