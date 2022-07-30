from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from particpant import Participant
import csv

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

global activeParticipant

#Routing Requests

#Initial routing request
@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/consent')
def consent():
    return render_template('consent.html')
    
@app.route('/demographics')
def demographics():
    return render_template('demographics.html')
    
@app.route('/task')
def task():
    return render_template('task.html')
    
@app.route('/description')
def description():
    return render_template('description.html')
    
@app.route('/calibration')
def calibrate():
    return render_template('calibration.html')
    
@app.route('/test')
def test():
    return render_template('test.html')
    
@app.route('/start')
def start():
    return render_template('start.html')
    

@app.route('/shop')
def shop(): 
    return render_template('shop.html')
    
@app.route('/decision')
def decision():
    return render_template('decision.html')

@app.route('/nextProduct')
def nextProduct():
    return render_template('nextProduct.html')
    
@app.route('/pause')
def pause():
    return render_template('pause.html')
    
@app.route('/questionaire')
def questionaire():
    return render_template('questionaire.html')
    
@app.route('/interview')
def interview():
    return render_template('interview.html')
    
@app.route('/end')
def end():
    return render_template('end.html')
    

@socketio.on('message')
def test_message(message):
    print('Incoming message:',message)
    app.logger.info('Incoming message: %s',message)

@socketio.on('consent')
def go_consent(message):
    global activeParticipant 
    activeParticipant = Participant(message['ParticipantId'])
    activeParticipant.generateLogFiles()
    app.logger.info('Participant has started a new session')
    emit('consent')

@socketio.on('demographics')
def go_demographics():
    app.logger.info('Participant started demographics questionaire!')
    emit('demographics')

@socketio.on('task')
def go_task(results):
    with open('./log/demographics.csv', 'a') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow([str(activeParticipant.participantId),results['gender'],
                              str(results['age']),results['job'],str(results['amountGroceriesOnline']),
                              str(results['amountGroceriesOverall']),str(results['decisionTime']),
                              results['visionCorrection']])
    app.logger.info('Task is presented to Participant!')
    emit('task')

@socketio.on('description')
def go_description():
    app.logger.info('Description is presented to Participant!')
    emit('description')

@socketio.on('calibration')
def go_calibration():
    app.logger.info('Participant started with calibration!')
    emit('calibration')

@socketio.on('test')
def go_test():
    app.logger.info('Participant started with test!')
    emit('test')

@socketio.on('start')
def go_start():
    app.logger.info('Participant ready to start the task!')
    emit('start')

@socketio.on('coordinates')
def go_coordinates(c):
    app.logger.info('Shop sent coordinates')
    activeParticipant.generateElement(c['Id'], c['x1'], c['y1'], c['x2'], c['y2'])

@socketio.on('startTracking')
def go_Tracking(message):
    app.logger.info('Tracking started')
    activeParticipant.startTracking(message['Prod'])

@socketio.on('stopTracking')
def go_stopTracking(message):
    app.logger.info('Tracking stopped')
    activeParticipant.stopTracking(message['Prod'])

@socketio.on('shop')
def go_shop():
    app.logger.info('Participant enters Shop!')
    emit('shop')
    
@socketio.on('nextProduct')
def go_nextProduct(selection):
    if (selection is not None):
        activeParticipant.saveDecision(str(selection['ProductSet']),selection['ProductNumber'], selection['InTime'])
        if (selection['ProductSet'] == 0):
            activeParticipant.test()
            emit('start')
        
    if (activeParticipant.remainingSets() == 0):
        emit('questionaire')
    elif (activeParticipant.remainingSets() % 10 == 0 and not activeParticipant.isPaused()):
        activeParticipant.pause()
        emit('pause')
    else:
        activeParticipant.endPause()
        emit('nextProduct')
    
    
@socketio.on('loadNextProduct')
def go_loadNextProduct():
    emit('loadNextProduct',{'Set': activeParticipant.nextProductSet()})
        
@socketio.on('loadProduct')
def loadProduct():
    app.logger.info('New Product loaded!')
    emit('loadProduct', {'ProductSet': activeParticipant.getProductSet(), 'HighlightingTechnique': activeParticipant.nextHighlightingTechnique()})

@socketio.on('decision')
def go_decision():
    app.logger.info('Participant needs to decide!')
    emit('decision')

@socketio.on('loadDecision')
def go_loadDecision():
    emit('loadDecision', {'Set': activeParticipant.currentSet})

@socketio.on('pause')
def go_pause():
    app.logger.info('Study paused!')
    emit('pause')

@socketio.on('questionaire')
def go_questionaire():
    app.logger.info('Participant finished task and started Questionaire!')
    emit('questionaire')

@socketio.on('interview')
def go_interview(results):
    with open('./log/evaluation.csv', 'a') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow([str(activeParticipant.participantId),
                             str(results['favVersion']),
                             str(results['influence']),
                             str(results['largerFont']),
                             str(results['redFont']),
                             str(results['blinking']),
                             str(results['standard']), 
                             str(results['confidenceLargerFont']),
                             str(results['attentionLargerFont1']),
                             str(results['attentionLargerFont2']),
                             str(results['search_strategyLargerFont']),
                             str(results['recognitionBiasLargerFont']),
                             str(results['autonomousLargerFont']),
                             str(results['reasonResponsiveLargerFont']),
                             str(results['confidenceRedFont']),
                             str(results['attentionRedFont1']),
                             str(results['attentionRedFont2']),
                             str(results['search_strategyRedFont']),
                             str(results['recognitionBiasRedFont']),
                             str(results['autonomousRedFont']),
                             str(results['reasonResponsiveRedFont']),
                             str(results['confidenceBlinking']),
                             str(results['attentionBlinking1']),
                             str(results['attentionBlinking2']),
                             str(results['search_strategyBlinking']),
                             str(results['recognitionBiasBlinking']),
                             str(results['autonomousBlinking']),
                             str(results['reasonResponsiveBlinking']),
                             str(results['realism']),
                             str(results['relevancy']),
                             str(results['time']),
                             str(results['pressure'])])
    app.logger.info('Participant started interview!')
    emit('interview')

@socketio.on('end')
def go_end():
    activeParticipant.printDecisions()
    app.logger.info('Participant finished study!')
    emit('end')
   

if __name__ == '__main__':
    socketio.run(app, debug=False)
    #app.run()

