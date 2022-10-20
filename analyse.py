from __future__ import division
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import detectors
import csv
from element import Element
from os.path import exists
from scipy.stats import norm
import scipy.stats as stats
from statsmodels.stats.anova import AnovaRM
import math
import seaborn

##
# The code used to analyzed the gaze data is used from
##
# Anna Maria Feit, Lukas Vordemann, Seonwook Park, Caterina
# Berube, and Otmar Hilliges. 2020. Detecting Relevance during
# Decision-Making from Eye Movements for UI Adaptation.
# ACM Symposium on Eye Tracking Research and Applications (6 2020), 1–11.
# DOI:http://dx.doi.org/10.1145/3379155.3391321
##
# and can be found on:
##
# https://github.com/vordemann/relevance-detection-etra2020
##
# Some additions and changes were made to fit our study.
##


""""
Inputs dataset and list of all UI elements
Computes all metrics for each element
Returns updated version of elements
"""


def analyseDataset(elements, prodId, dataset):
    elements = elements
    # Add new metric entry to metrics dictionairy of each element
    for elem in elements:
        elem.metrics[prodId] = {
            'timeToFirstFixation': 0,
            'firstPassGazeDuration': 0,
            'secondPassGazeDuration': 0,
            'refixationsCount': 0,
            'sumOfFixations': 0,
            'overallDwellTime': 0,
        }

    # Loading new dataset
    gazeData = dataset

    # Run validity check and filtering
    gazeData = filterUnvalidEntries(gazeData)
    gazeData = computeActualGazePoint(gazeData)
    gazeData = filterOffDisplayValues(gazeData)
    gazeData.reset_index()

    # If no gaze data returm elements
    if gazeData.empty or len(gazeData) == 1:
        return elements
    else:
        pass

    # Extract timestamps, coordinates and events
    timestamps = getTimestampsInMilliseconds(gazeData)
    x_gazePoints, width = getXGazePointsAsPixel(gazeData)
    y_gazePoints, height = getYGazePointsAsPixel(gazeData)
    x_gazePoints, y_gazePoints, timestamps = discardEdgeGazePoints(
        x_gazePoints, y_gazePoints, timestamps, elements)

    fixations = detectors.fixation_detection(
        x_gazePoints, y_gazePoints, timestamps, mindur=50)

    # If no fixation were detected return elements
    if len(fixations) == 0 or len(timestamps) == 0:
        return elements
    else:
        pass

    ##################################################
    ######## Start with metric computation ###########
    ##################################################

    # Time to first fixation -- Orientation
    # First pass gaze duration -- Orientation
    # Second pass gaze duration -- Evaluation
    # Refixations count -- Evaluation
    elements = computeTemporalFixationMetrices(fixations, elements, prodId)

    # Sum of fixations -- Verification
    elements = computeSumOfFixations(fixations, elements, prodId)

    # Overall Dwell Time -- Verification
    elements = computeDwellTime(
        x_gazePoints, y_gazePoints, timestamps, elements, prodId)

    return elements


######### Helper methods to filter and process dataframe ###########

# Map points to elements
def mapToAOI(x, y, elements):
    for e in elements:
        if (x in np.arange(e.boundaries[0], e.boundaries[2]+1)):
            if (y in np.arange(e.boundaries[1], e.boundaries[3]+1)):
                return e.aoiCode
    return 'OFF'

# Get element from aoiCode


def getElementOfAOI(elements, aoi):
    for e in elements:
        if (aoi == e.aoiCode):
            return e


# Delete all unvalid gaze data
def filterUnvalidEntries(dataframe):
    validLeft = dataframe[dataframe['LeftGazePointValidity'] == 1]
    allValid = validLeft[validLeft['RightGazePointValidity'] == 1]
    return allValid


# Compute GazePoint from Left and Right Eye GazeData
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

    actualGazePointX = filterData(actualGazePointX)
    actualGazePointY = filterData(actualGazePointY)

    s = pd.Series(actualGazePointX)
    t = pd.Series(actualGazePointY)
    dataframe = dataframe.assign(ActualGazePointX=s.values)
    dataframe = dataframe.assign(ActualGazePointY=t.values)
    return dataframe

# Remove all off Display values


def filterOffDisplayValues(dataframe):

    inboundAll = dataframe[dataframe['ActualGazePointX'] <= 1]
    inboundAll = inboundAll[inboundAll['ActualGazePointX'] >= 0]

    inboundAll = inboundAll[inboundAll['ActualGazePointY'] <= 1]
    inboundAll = inboundAll[inboundAll['ActualGazePointY'] >= 0]

    return inboundAll


def getTimestampsInMilliseconds(dataframe):
    time = dataframe.Timestamp
    visited = dataframe.Visited
    time.reset_index(drop=True, inplace=True)
    visited.reset_index(drop=True, inplace=True)
    t_temp = []
    initialTime = time[1]/1000
    currVisit = 1
    i = 1
    while i < len(time):
        if (visited[i] != currVisit):
            currVisit = visited[i]
            initialTime = time[i-1]/1000

        t_temp.append(time[i]/1000-initialTime)
        i = i+1
    return t_temp


def getXGazePointsAsPixel(dataframe):
    #user32 = ctypes.windll.user32
    #width = user32.GetSystemMetrics(0)
    width = 1920
    x_temp = []
    actualX = dataframe['ActualGazePointX']
    for x in actualX[1:]:
        x_temp.append(round(x*width))
    return x_temp, width


def getYGazePointsAsPixel(dataframe):
    #user32 = ctypes.windll.user32
    #height = user32.GetSystemMetrics(1)
    height = 1080
    y_temp = []
    actualY = dataframe['ActualGazePointY']
    for y in actualY[1:]:
        y_temp.append(round(y*height))
    return y_temp, height


def discardEdgeGazePoints(x_gazePoints, y_gazePoints, timestamp, elements):
    x_temp = []
    y_temp = []
    time_temp = []
    for i in range(0, len(x_gazePoints)):
        aoi = mapToAOI(x_gazePoints[i], y_gazePoints[i], elements)
        if aoi != 'OFF':
            x_temp.append(x_gazePoints[i])
            y_temp.append(y_gazePoints[i])
            time_temp.append(timestamp[i])
    return x_temp, y_temp, time_temp


######### Computation of single metrics ###########

# Compute temporal fixation metrices
# Inputs list of detected fixations and elements
# Computes Time to first fixation, first- and second-pass-gaze as well as refixation count
def computeTemporalFixationMetrices(fixations, elements, prodId):
    firstPass = 0
    secondPass = 0
    for i in np.arange(0, len(fixations)-1, 1):
        aoi_one = mapToAOI(fixations[i][3], fixations[i][4], elements)
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
    aoi_last = mapToAOI(fixations[(len(fixations) - 1)]
                        [3], fixations[(len(fixations) - 1)][4], elements)
    elem = getElementOfAOI(elements, aoi_last)
    if firstPass != 0 or secondPass != 0:
        if elem.metrics[prodId]['refixationsCount'] == 0:
            elem.metrics[prodId]['firstPassGazeDuration'] = firstPass
        elif elem.metrics[prodId]['refixationsCount'] == 1:
            elem.metrics[prodId]['secondPassGazeDuration'] = secondPass
    elem.metrics[prodId]['refixationsCount'] += 1
    return elements

# Compute sum of fixations


def computeSumOfFixations(fixations, elements, prodId):
    for fix in fixations:
        aoi_hit = mapToAOI(fix[3], fix[4], elements)
        elem = getElementOfAOI(elements, aoi_hit)
        elem.metrics[prodId]['sumOfFixations'] += 1
    return elements

# Compute overall Dwell Time


def computeDwellTime(x_gazePoints, y_gazePoints, timestamps, elements, prodId):
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
                print('Error')
                print(i)
    return elements

##
# The following code only consists of additions to the previous mentioned code
##

# Filter the gaze data with a weighted average filter and a gaussian kernel function
def filterData(gazePoints):
    filteredPoints = []
    weightFunc = gauss()
    i = 0
    while i < len(gazePoints):
        if i < 40:
            filteredPoints.append(gazePoints[i])
        else:
            temp_points = gazePoints[(i-40):i]
            filteredPoints.append(np.average(
                a=temp_points, weights=weightFunc))
        i = i+1
    return filteredPoints

# Calculate weights for each gaze point according to gaussian kernel function
def gauss():
    array = np.arange(1, 41)
    gauss = []
    for x in array:
        x = math.e ** -((x ** 2)/(2 * (17 ** 2)))
        gauss.append(x)
    gauss.reverse()
    return gauss

# Reads area of interest elements out of csv file
# Returns a set containing 40 sets (one for each decision), which contain
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

        if (diffX <= 50):
            diffX = int((50-diffX)/2)
            x1 = x1 - diffX
            x2 = x2 - diffX
        if (diffY <= 50):
            diffY = int((50-diffY)/2)
            y1 = y1 - diffY
            y2 = y2 + diffY

        sets[setId-1].append(Element(aoiId, x1, y1, x2, y2))
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


pAmount = 518

# Analyzes the gaze data of each participant
# Saves calculated gaze metrics in a cvs file
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
                file = pd.read_csv('./log/p'+str(pId) +
                                   '/gazeData/gaze_'+str(productSet)+'_0.csv')

            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_1.csv'):
                highlighting = 1
                file = pd.read_csv('./log/p'+str(pId) +
                                   '/gazeData/gaze_'+str(productSet)+'_1.csv')

            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_2.csv'):
                highlighting = 2
                file = pd.read_csv('./log/p'+str(pId) +
                                   '/gazeData/gaze_'+str(productSet)+'_2.csv')

            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_3.csv'):
                highlighting = 3
                file = pd.read_csv('./log/p'+str(pId) +
                                   '/gazeData/gaze_'+str(productSet)+'_3.csv')

            if file is not None:
                gaze0 = file[file.ProductId == 0]
                gaze1 = file[file.ProductId == 1]
                gaze2 = file[file.ProductId == 2]
                gaze3 = file[file.ProductId == 3]
                gaze4 = file[file.ProductId == 4]
                gaze5 = file[file.ProductId == 5]
                sets[productSet-1][0] = analyseDataset(
                    sets[productSet-1][0], str(10*productSet), gaze0)
                sets[productSet-1][1] = analyseDataset(
                    sets[productSet-1][1], str(10*productSet+1), gaze1)
                sets[productSet-1][2] = analyseDataset(
                    sets[productSet-1][2], str(10*productSet+2), gaze2)
                sets[productSet-1][3] = analyseDataset(
                    sets[productSet-1][3], str(10*productSet+3), gaze3)
                sets[productSet-1][4] = analyseDataset(
                    sets[productSet-1][4], str(10*productSet+4), gaze4)
                sets[productSet-1][5] = analyseDataset(
                    sets[productSet-1][5], str(10*productSet+5), gaze5)

                i = 0
                while (i <= 5):
                    aois = sets[productSet-1][i]
                    for elem in aois:
                        with open(dirName+'/metrics_'+str(pId)+'_50px_50ms_filtered3.csv', 'a') as csvfile:
                            filewriter = csv.writer(
                                csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                            row = []
                            row.append(str(pId))
                            row.append(str(highlighting))
                            row.append(str(elem.aoiCode))
                            row.append(
                                str(elem.metrics[str(10*productSet+i)]['timeToFirstFixation']))
                            row.append(
                                str(elem.metrics[str(10*productSet+i)]['firstPassGazeDuration']))
                            row.append(
                                str(elem.metrics[str(10*productSet+i)]['secondPassGazeDuration']))
                            row.append(
                                str(elem.metrics[str(10*productSet+i)]['refixationsCount']))
                            row.append(
                                str(elem.metrics[str(10*productSet+i)]['sumOfFixations']))
                            row.append(
                                str(elem.metrics[str(10*productSet+i)]['overallDwellTime']))
                            filewriter.writerow(row)
                    i = i+1
            productSet = productSet + 1
        pId = pId + 1

# Draw Histogram with a normaldistribution fitted to the data
def drawNormalDist(data, steps, metric):
    # Fit a normal distribution to the data:
    mu = np.average(data)
    std = np.std(data)

    # Plot the histogram.

    plt.hist(data, steps, density=(True))

    # Plot the PDF.
    l, r = plt.xlim()
    x = np.linspace(l, r, steps)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "mu = %.2f,  std = %.2f" % (mu, std)
    title = metric + title
    plt.title(title)
    plt.show()

# Reads metrics from cvs file, draws Histograms for each gaze metric and runs statistical tests
def createDiagrams():
    sumOfFixations = [[], [], [], []]
    refixationCount = [[], [], [], []]
    timeToFirstFixation = [[], [], [], []]
    overallDwellTime = [[], [], [], []]
    fixatedAreas = [[], [], [], []]
    areasPerDecision = [[], [], [], []]
    pId = 501

    while pId <= pAmount:
        if not (pId == 506 or pId == 512 or pId == 517 or pId == 518):
            path = './log/p'+str(pId)+'/metrics_'+str(pId) + \
                '_50px_50ms_filtered3.csv'

            sumOfFixationsParticipants = [[], [], [], []]
            refixationCountParticipants = [[], [], [], []]
            timeToFirstFixationParticipants = [[], [], [], []]
            overallDwellTimeParticipants = [[], [], [], []]
            fixatedAreasParticipants = [0, 0, 0, 0]
            areasOverall = [0, 0, 0, 0]
            areasPerDecisionParticipants = [[], [], [], []]
            currDecision = 0
            currHighlighting = 0
            areasForDecision = 0
            if (exists(path)):
                file = pd.read_csv(path)
                for row in file.itertuples():
                    if ((math.floor(row[3]/100)) != currDecision):
                        areasPerDecisionParticipants[currHighlighting].append(areasForDecision)
                        currDecision = (math.floor(row[3]/100))
                        currHighlighting = row[2]
                        areasForDecision = 0
                    if (row[7] >= 0):
                        refixationCountParticipants[row[2]].append(row[7])
                    if (row[8] >= 0):
                        sumOfFixationsParticipants[row[2]].append(row[8])
                        if (row[8] > 0):
                            areasForDecision = areasForDecision + 1
                            fixatedAreasParticipants[row[2]] = fixatedAreasParticipants[row[2]] + 1
                    if (row[4] > 0):
                        timeToFirstFixationParticipants[row[2]].append(row[4])
                    if (row[9] > 0):
                        overallDwellTimeParticipants[row[2]].append(row[9])
                    areasOverall[row[2]] = areasOverall[row[2]]+1
            i = 0
            while i < 4:
                sumOfFixations[i].append(
                    np.mean(sumOfFixationsParticipants[i]))

                refixationCount[i].append(
                    np.mean(refixationCountParticipants[i]))

                timeToFirstFixation[i].append(np.mean(timeToFirstFixationParticipants[i]))

                overallDwellTime[i].append(np.mean(overallDwellTimeParticipants[i]))

                fixatedAreas[i].append(
                    fixatedAreasParticipants[i]/areasOverall[i])

                areasPerDecision[i].append(np.mean(areasPerDecisionParticipants[i]))
                i = i+1
        pId = pId + 1

    participants = np.tile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], 4)
    highlights = np.repeat(['no Highlighting', 'larger Font', 'red Text', 'blinking Text'], 14)

    data = [item for sublist in areasPerDecision for item in sublist]
    dataframe = pd.DataFrame({'Participant': participants, 'Highlighting': highlights, 'Data': data})
    print("Areas per Decision:")
    print(np.mean(areasPerDecision[0]),np.std(areasPerDecision[0]))
    print(np.mean(areasPerDecision[1]),np.std(areasPerDecision[1]))
    print(np.mean(areasPerDecision[2]),np.std(areasPerDecision[2]))
    print(np.mean(areasPerDecision[3]),np.std(areasPerDecision[3]))
    print(stats.shapiro(areasPerDecision[0]))
    print(stats.shapiro(areasPerDecision[1]))
    print(stats.shapiro(areasPerDecision[2]))
    print(stats.shapiro(areasPerDecision[3]))
    print(AnovaRM(data=dataframe, depvar='Data', subject='Participant',within=['Highlighting'], aggregate_func='mean').fit())
    plot = seaborn.violinplot(data=dataframe, x='Highlighting', y='Data', inner="point")
    plot.set(xlabel="Test Condition",ylabel="Amount of AoIs fixated per Decision:", ylim=0)
    plt.show()

    data = [item for sublist in fixatedAreas for item in sublist]
    dataframe = pd.DataFrame({'Participant': participants, 'Highlighting': highlights, 'Data': data})
    print("Fixated Areas:")
    print(np.mean(fixatedAreas[0]),np.std(fixatedAreas[0]))
    print(np.mean(fixatedAreas[1]),np.std(fixatedAreas[1]))
    print(np.mean(fixatedAreas[2]),np.std(fixatedAreas[2]))
    print(np.mean(fixatedAreas[3]),np.std(fixatedAreas[3]))
    print(stats.shapiro(fixatedAreas[0]))
    print(stats.shapiro(fixatedAreas[1]))
    print(stats.shapiro(fixatedAreas[2]))
    print(stats.shapiro(fixatedAreas[3]))
    print(AnovaRM(data=dataframe, depvar='Data', subject='Participant',within=['Highlighting'], aggregate_func='mean').fit())
    plot = seaborn.violinplot(data=dataframe, x='Highlighting', y='Data', inner="point")
    plot.set(xlabel="Test Condition",ylabel="Proportion of fixated Areas of Interest:", ylim=0)
    plt.show()

    data = [item for sublist in refixationCount for item in sublist]
    dataframe = pd.DataFrame({'Participant': participants, 'Highlighting': highlights, 'Data': data})
    print("Refixation Count:")
    print(np.mean(refixationCount[0]),np.std(refixationCount[0]))
    print(np.mean(refixationCount[1]),np.std(refixationCount[1]))
    print(np.mean(refixationCount[2]),np.std(refixationCount[2]))
    print(np.mean(refixationCount[3]),np.std(refixationCount[3]))
    print(stats.shapiro(refixationCount[0]))
    print(stats.shapiro(refixationCount[1]))
    print(stats.shapiro(refixationCount[2]))
    print(stats.shapiro(refixationCount[3]))
    print(AnovaRM(data=dataframe, depvar='Data', subject='Participant',within=['Highlighting'], aggregate_func='mean').fit())
    plot = seaborn.violinplot(data=dataframe, x='Highlighting', y='Data', inner="point")
    plot.set(xlabel="Test Condition", ylabel="Refixation Count", ylim=0)
    plt.show()

    data = [item for sublist in sumOfFixations for item in sublist]
    dataframe = pd.DataFrame({'Participant': participants, 'Highlighting': highlights, 'Data': data})
    print("Sum of Fixations:")
    print(np.mean(sumOfFixations[0]),np.std(sumOfFixations[0]))
    print(np.mean(sumOfFixations[1]),np.std(sumOfFixations[1]))
    print(np.mean(sumOfFixations[2]),np.std(sumOfFixations[2]))
    print(np.mean(sumOfFixations[3]),np.std(sumOfFixations[3]))
    print(stats.shapiro(sumOfFixations[0]))
    print(stats.shapiro(sumOfFixations[1]))
    print(stats.shapiro(sumOfFixations[2]))
    print(stats.shapiro(sumOfFixations[3]))
    print(AnovaRM(data=dataframe, depvar='Data', subject='Participant', within=['Highlighting'], aggregate_func='mean').fit())
    plot = seaborn.violinplot(data=dataframe, x='Highlighting', y='Data', inner="point")
    plot.set(xlabel="Test Condition", ylabel="Sum of Fixations", ylim=0)
    plt.show()

    data = [item for sublist in timeToFirstFixation for item in sublist]
    dataframe = pd.DataFrame({'Participant': participants, 'Highlighting': highlights, 'Data': data})
    print("Time to first Fixation")
    print(np.mean(timeToFirstFixation[0]),np.std(timeToFirstFixation[0]))
    print(np.mean(timeToFirstFixation[1]),np.std(timeToFirstFixation[1]))
    print(np.mean(timeToFirstFixation[2]),np.std(timeToFirstFixation[2]))
    print(np.mean(timeToFirstFixation[3]),np.std(timeToFirstFixation[3]))
    print(stats.shapiro(timeToFirstFixation[0]))
    print(stats.shapiro(timeToFirstFixation[1]))
    print(stats.shapiro(timeToFirstFixation[2]))
    print(stats.shapiro(timeToFirstFixation[3]))
    print(stats.friedmanchisquare(timeToFirstFixation[0], timeToFirstFixation[1], timeToFirstFixation[2], timeToFirstFixation[3]))
    plot = seaborn.violinplot(data=dataframe, x='Highlighting', y='Data', inner="point")
    plot.set(xlabel="Test Condition",ylabel="Time to first Fixation in milliseconds", ylim=0)
    plt.show()
    
    data = [item for sublist in overallDwellTime for item in sublist]
    dataframe = pd.DataFrame({'Participant': participants, 'Highlighting': highlights, 'Data': data})
    print("Overall Dwell Time")
    print(np.mean(overallDwellTime[0]),np.std(overallDwellTime[0]))
    print(np.mean(overallDwellTime[1]),np.std(overallDwellTime[1]))
    print(np.mean(overallDwellTime[2]),np.std(overallDwellTime[2]))
    print(np.mean(overallDwellTime[3]),np.std(overallDwellTime[3]))
    print(stats.shapiro(overallDwellTime[0]))
    print(stats.shapiro(overallDwellTime[1]))
    print(stats.shapiro(overallDwellTime[2]))
    print(stats.shapiro(overallDwellTime[3]))
    print(AnovaRM(data=dataframe, depvar='Data', subject='Participant',within=['Highlighting'], aggregate_func='mean').fit())
    plot = seaborn.violinplot(data=dataframe, x='Highlighting', y='Data', inner="point")
    plot.set(xlabel="Test Condition",ylabel="Overall Dwell time in milliseconds", ylim=0)
    plt.show()
    runPairedTTest(overallDwellTime[0],overallDwellTime[1],overallDwellTime[2],overallDwellTime[3])


def removeOutliers(data):
    outliers = math.floor(len(data) * 0.05)
    data.sort()
    return data[:-outliers or None]


def runPairedTTest(s1, s2, s3, s4):
    print('Paired t-Test: no Highlighting & larger Font')
    print(stats.ttest_rel(s1, s2))
    print('Paired t-Test: no Highlighting & red Text')
    print(stats.ttest_rel(s1, s3))
    print('Paired t-Test: no Highlighting & blinking Text')
    print(stats.ttest_rel(s1, s4))
    print('Paired t-Test: larger Font & red Text')
    print(stats.ttest_rel(s2, s3))
    print('Paired t-Test: larger Font & blinking Text')
    print(stats.ttest_rel(s2, s4))
    print('Paired t-Test: red Text & blinking Text')
    print(stats.ttest_rel(s3, s4))


def revisit():
    pId = 501
    visits = [[], [], [], []]
    while (pId <= pAmount):
        productSet = 1
        while (productSet <= 40):
            file = None
            highlighting = 0

            if exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_0.csv'):
                highlighting = 0
                file = pd.read_csv('./log/p'+str(pId) +
                                   '/gazeData/gaze_'+str(productSet)+'_0.csv')

            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_1.csv'):
                highlighting = 1
                file = pd.read_csv('./log/p'+str(pId) +
                                   '/gazeData/gaze_'+str(productSet)+'_1.csv')

            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_2.csv'):
                highlighting = 2
                file = pd.read_csv('./log/p'+str(pId) +
                                   '/gazeData/gaze_'+str(productSet)+'_2.csv')

            elif exists('./log/p'+str(pId)+'/gazeData/gaze_'+str(productSet)+'_3.csv'):
                highlighting = 3
                file = pd.read_csv('./log/p'+str(pId) +
                                   '/gazeData/gaze_'+str(productSet)+'_3.csv')

            if file is not None:
                gaze1 = file[file.ProductId == 1]
                column = gaze1["Visited"]
                if not (pd.isna(column.max())):
                    visits[highlighting].append(column.max())
                gaze2 = file[file.ProductId == 2]
                column = gaze2["Visited"]
                if not (pd.isna(column.max())):
                    visits[highlighting].append(column.max())
                gaze3 = file[file.ProductId == 3]
                column = gaze3["Visited"]
                if not (pd.isna(column.max())):
                    visits[highlighting].append(column.max())
                gaze4 = file[file.ProductId == 4]
                column = gaze4["Visited"]
                if not (pd.isna(column.max())):
                    visits[highlighting].append(column.max())
                gaze5 = file[file.ProductId == 5]
                column = gaze5["Visited"]
                if not (pd.isna(column.max())):
                    visits[highlighting].append(column.max())
            productSet = productSet + 1
        pId = pId + 1

    for visit in visits:
        drawNormalDist(visit, 50, "Visits: ")


revisit()
analyse()
createDiagrams()