import numpy as np
import matplotlib.pyplot as plt
import pandas
from scipy.stats import norm

likert = ('Strongly Disagree','Disagree','Neutral','Agree','Strongly Agree')

def createDecisionBarChart(noHighlighting,largerText,redText,blinking,s):
    x = np.arange(1,6)  # the label locations
    width = 0.2  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width*1.5, noHighlighting, width, label='No Highlighting')
    rects2 = ax.bar(x - width/2, largerText, width, label='Larger Text')
    rects3 = ax.bar(x + width/2, redText, width, label='Red Text')
    rects4 = ax.bar(x + width*1.5, blinking, width, label='Blinking')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Amount')
    ax.set_xlabel('Product')
    ax.set_title('Times each product was chosen out of set: ' + str(s))
    ax.set_xticks(x)
    
    plt.yticks(range(21))
    ax.legend()

    ax.bar_label(rects1, padding=1)
    ax.bar_label(rects2, padding=1)
    ax.bar_label(rects3, padding=1)
    ax.bar_label(rects4, padding=1)

    fig.tight_layout()

    plt.show()
    
def createQuestionaireBarChart(values,objects,title,y1=0,y2=21,ylabel='Amount Answer'):
    x = np.arange(len(objects))  # the label locations
    
    rects = plt.bar(x,values, align='center', alpha=0.5)
    plt.bar_label(rects, values)

    plt.xticks(x, objects,rotation='vertical')
    plt.yticks(range(y1,y2))
    plt.ylim(y1,y2)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()



def createComparisonBarChart(largerText,redText,blinking,title):
    x = np.arange(5)  # the label locations
    width = 0.2  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width, largerText, width, label='Larger Text')
    rects2 = ax.bar(x, redText, width, label='Red Text')
    rects3 = ax.bar(x + width, blinking, width, label='Blinking')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Amount Answer')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(likert,rotation='vertical')
    
    plt.yticks(range(21))
    ax.legend()

    ax.bar_label(rects1, padding=1)
    ax.bar_label(rects2, padding=1)
    ax.bar_label(rects3, padding=1)

    fig.tight_layout()

    plt.show()


def createComparisonAllBarChart(noHighlighting,largerText,redText,blinking,title):
    x = np.arange(1,6)  # the label locations
    width = 0.2  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width*1.5, noHighlighting, width, label='No Highlighting')
    rects2 = ax.bar(x - width/2, largerText, width, label='Larger Text')
    rects3 = ax.bar(x + width/2, redText, width, label='Red Text')
    rects4 = ax.bar(x + width*1.5, blinking, width, label='Blinking')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Amount Answer')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(likert,rotation='vertical')
    
    plt.yticks(range(21))
    ax.legend()

    ax.bar_label(rects1, padding=1)
    ax.bar_label(rects2, padding=1)
    ax.bar_label(rects3, padding=1)
    ax.bar_label(rects4, padding=1)

    fig.tight_layout()

    plt.show()

def evaluateDecisions():
    decisions = [[[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]] for x in range(41)]
    #decisionTime = [0,0,0,0]
    #decisionTime = [[0 for x in range(61)],[0 for x in range(61)],[0 for x in range(61)],[0 for x in range(61)]]
    decisionTime = [[],[],[],[]]
    timeHighlighting = [0,0,0,0]
    id = 501
    
    while (id <= 518):
        path = './log/p'+str(id)+'/decisions.csv'
        file = pandas.read_csv(path, header=None)
        file.sort_values(by=0, inplace=True)
        file.set_index(0,inplace=True)
        
        for index, row in file.iterrows():
            if row[3] > 0 :
                decisions[index][int(row[2])][int(row[1])-1]=decisions[index][int(row[2])][int(row[1])-1]+1
                if index > 0:
                    #decisionTime[row[2]] = decisionTime[row[2]]+60-row[3]
                    decisionTime[row[2]].append(60-row[3]) 
                    
                    #decisionTime[row[2]][60-row[3]] = decisionTime[row[2]][60-row[3]] + 1 
                    timeHighlighting[row[2]] = timeHighlighting[row[2]] + 1
            
        id = id+1
    #for i in range(41):
        #createDecisionBarChart(decisions[i][0], decisions[i][1], decisions[i][2], decisions[i][3],i)
        
    for i in range(len(decisionTime)):
        #decisionTime[i] = statistics.median(decisionTime[i])
        #decisionTime[i].sort()
        data = decisionTime[i]
        
        # Fit a normal distribution to the data:
        mu = np.average(data)
        std = np.std(data)
        
        # Plot the histogram.
        
        plt.hist(data,61,density=(True))
        
        # Plot the PDF.
        x = np.linspace(0, 60, 100)
        p = norm.pdf(x, mu, std)
        plt.plot(x, p, 'k', linewidth=2)
        title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
        plt.title(title)
        plt.show()
    #createQuestionaireBarChart(decisionTime, ('no Highlighting','larger Font','red Font','blinking'),'Mean time until decision is made, depending on highlighting technique',20,30, 'Mean decision making time')
    
def evaluateDemographicsQuestionaire():
    gender = [0,0,0]
    age = []
    amountGroceriesOnline = [0,0,0,0,0,0,0]
    amountGroceriesOverall = [0,0,0,0,0,0]
    decisionTime = [0,0,0,0,0]
    visionCorrection = [0,0,0]
    
    path = './log/demographics.csv'
    file = pandas.read_csv(path)
    file = file.loc[file["ParticipantID"]>500]
    
    for index,row in file.iterrows():
        if (row[1]=="male"):
            gender[0] = gender[0] + 1
        elif (row[1]=="female"):
            gender[1] = gender[1] + 1
        else:
            gender[2] = gender[2] + 1
        age.append(row[2])
        amountGroceriesOnline[int(row[4])] = amountGroceriesOnline[int(row[4])] + 1
        amountGroceriesOverall[int(row[5])] = amountGroceriesOverall[int(row[5])] + 1
        decisionTime[int(row[6])-1] = decisionTime[int(row[6])-1] + 1
        if (row[7]=="glasses"):
            visionCorrection[0] = visionCorrection[0] + 1
        elif (row[7]=="contacts"):
            visionCorrection[1] = visionCorrection[1] + 1
        else:
            visionCorrection[2] = visionCorrection[2] + 1
            
    createQuestionaireBarChart(gender, ('Male','Female','Diverse'), 'Participants Gender')

    countedAges = {i:age.count(i) for i in age}
    keys = list(countedAges.keys())
    keys.sort()
    values = []
    for key in keys:
        values = values + [countedAges[key]]
    
    plt.bar(range(len(countedAges)), values, align='center')
    
    plt.xticks(range(len(countedAges)), keys)
    plt.yticks(range(21))
    
    plt.show()
    
    createQuestionaireBarChart(amountGroceriesOnline, ('Never','1-2 times overall','less than once a month','1-3 times a month','1-2 times a week','3-4 times a week','5-6 times a week'), 'Amount of Groceries the participant buys online')
    createQuestionaireBarChart(amountGroceriesOverall, ('Never','less than once a month','1-3 times a month','1-2 times a week','3-4 times a week','5-6 times a week'), 'Amount of Groceries the participant buys overall')
    createQuestionaireBarChart(decisionTime, likert, 'Do you take much time making buying decisions?')
    createQuestionaireBarChart(visionCorrection, ('Glasses','Contact lenses','None'), 'Seeing Aids the participant wore during the study')


def evaluateEvaluationQuestionaire():
    
    favVersion = [0,0,0,0]
    influence = [0,0,0,0,0]
    largerFont = [0,0,0,0,0]
    redFont = [0,0,0,0,0]
    blinking = [0,0,0,0,0]
    standard = [0,0,0,0,0]
    confidenceLargerFont = [0,0,0,0,0]
    attention1LargerFont = [0,0,0,0,0]
    attention2LargerFont = [0,0,0,0,0]
    searchStrategyLargerFont = [0,0,0,0,0]
    recognitionBiasLargerFont = [0,0,0,0,0]
    autonomousLargerFont = [0,0,0,0,0]
    reasonResponsiveLargerFont = [0,0,0,0,0]
    confidenceRedFont = [0,0,0,0,0]
    attention1RedFont = [0,0,0,0,0]
    attention2RedFont = [0,0,0,0,0]
    searchStrategyRedFont = [0,0,0,0,0]
    recognitionBiasRedFont = [0,0,0,0,0]
    autonomousRedFont = [0,0,0,0,0]
    reasonResponsiveRedFont = [0,0,0,0,0]
    confidenceBlinking = [0,0,0,0,0]
    attention1Blinking = [0,0,0,0,0]
    attention2Blinking = [0,0,0,0,0]
    searchStrategyBlinking = [0,0,0,0,0]
    recognitionBiasBlinking = [0,0,0,0,0]
    autonomousBlinking = [0,0,0,0,0]
    reasonResponsiveBlinking = [0,0,0,0,0]
    realism = [0,0,0,0,0]
    relevancy = [0,0,0,0,0]
    time = [0,0,0,0,0]
    pressure = [0,0,0,0,0]
    

    path = './log/evaluation.csv'
    file = pandas.read_csv(path)
    file = file.loc[file["Id"]>500]
    
    
    for index,row in file.iterrows():
        if (row[1]=="noHighlighting"):
            favVersion[0] = favVersion[0] + 1
        elif (row[1]=="largerFont"):
            favVersion[1] = favVersion[1] + 1
        elif (row[1]=="redFont"):
            favVersion[2] = favVersion[2] + 1
        else:
            favVersion[3] = favVersion[3] + 1
        influence[int(row[2])-1] = influence[int(row[2])-1] + 1
        largerFont[int(row[3])-1] = largerFont[int(row[3])-1] + 1
        redFont[int(row[4])-1] = redFont[int(row[4])-1] + 1
        blinking[int(row[5])-1] = blinking[int(row[5])-1] + 1
        standard[int(row[6])-1] = standard[int(row[6])-1] + 1
        confidenceLargerFont[int(row[7])-1] = confidenceLargerFont[int(row[7])-1] + 1
        attention1LargerFont[int(row[8])-1] = attention1LargerFont[int(row[8])-1] + 1
        attention2LargerFont[int(row[9])-1] = attention2LargerFont[int(row[9])-1] + 1
        searchStrategyLargerFont[int(row[10])-1] = searchStrategyLargerFont[int(row[10])-1] + 1
        recognitionBiasLargerFont[int(row[11])-1] = recognitionBiasLargerFont[int(row[11])-1] + 1
        autonomousLargerFont[int(row[12])-1] = autonomousLargerFont[int(row[12])-1] + 1
        reasonResponsiveLargerFont[int(row[13])-1] = reasonResponsiveLargerFont[int(row[13])-1] + 1
        confidenceRedFont[int(row[14])-1] = confidenceRedFont[int(row[14])-1] + 1
        attention1RedFont[int(row[15])-1] = attention1RedFont[int(row[15])-1] + 1
        attention2RedFont[int(row[16])-1] = attention2RedFont[int(row[16])-1] + 1
        searchStrategyRedFont[int(row[17])-1] = searchStrategyRedFont[int(row[17])-1] + 1
        recognitionBiasRedFont[int(row[18])-1] = recognitionBiasRedFont[int(row[18])-1] + 1
        autonomousRedFont[int(row[19])-1] = autonomousRedFont[int(row[19])-1] + 1
        reasonResponsiveRedFont[int(row[20])-1] = reasonResponsiveRedFont[int(row[20])-1] + 1
        confidenceBlinking[int(row[21])-1] = confidenceBlinking[int(row[21])-1] + 1
        attention1Blinking[int(row[22])-1] = attention1Blinking[int(row[22])-1] + 1
        attention2Blinking[int(row[23])-1] = attention2Blinking[int(row[23])-1] + 1
        searchStrategyBlinking[int(row[24])-1] = searchStrategyBlinking[int(row[24])-1] + 1
        recognitionBiasBlinking[int(row[25])-1] = recognitionBiasBlinking[int(row[25])-1] + 1
        autonomousBlinking[int(row[26])-1] = autonomousBlinking[int(row[26])-1] + 1
        reasonResponsiveBlinking[int(row[27])-1] = reasonResponsiveBlinking[int(row[27])-1] +1
        realism[int(row[28])-1] = realism[int(row[28])-1] +1
        relevancy[int(row[29])-1] = relevancy[int(row[29])-1] +1
        time[int(row[30])-1] = time[int(row[30])-1] +1
        pressure[int(row[31])-1] = pressure[int(row[31])-1] +1
        
    createQuestionaireBarChart(favVersion, ('no Highlighting','larger Font','red Font','blinking'), 'Participants favorite Version')
    createQuestionaireBarChart(influence, (('negative','rather negative','neutral','rather positive','positive')), 'How did the highlighting in general influence your decision process?')
    createComparisonAllBarChart(standard, largerFont, redFont, blinking, 'I liked the online shop with this highlighitng technique.')
    createComparisonBarChart(confidenceLargerFont, confidenceRedFont, confidenceBlinking, 'I made good decisions.')
    createComparisonBarChart(attention1LargerFont, attention1RedFont, attention1Blinking, 'My gaze was attracted by the highlighting')
    createComparisonBarChart(attention2LargerFont, attention2RedFont, attention2Blinking, 'I searched for the highlighted information.')
    createComparisonBarChart(searchStrategyLargerFont, searchStrategyRedFont, searchStrategyBlinking,  'I chnanged the way I search for information')
    createComparisonBarChart(recognitionBiasLargerFont, recognitionBiasRedFont, recognitionBiasBlinking, 'I decided for products i knew.')
    createComparisonBarChart(autonomousLargerFont, autonomousRedFont, autonomousBlinking, 'I felt autonomous in my decision making.')
    createComparisonBarChart(reasonResponsiveLargerFont, reasonResponsiveRedFont, reasonResponsiveBlinking, 'My decisions where based on good reasons.')
    createQuestionaireBarChart(realism, likert, 'The product selection was realistic.')
    createQuestionaireBarChart(relevancy, likert, 'The highlighted information was relevant for my decision.')
    createQuestionaireBarChart(time, likert, 'I had enought time to make a decision')
    createQuestionaireBarChart(pressure, likert, 'I was under pressure during decision making.')
    

#evaluateDemographicsQuestionaire()
evaluateDecisions()
#evaluateEvaluationQuestionaire()
































