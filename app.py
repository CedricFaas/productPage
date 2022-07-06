from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

global productSets 
productSets = list(range(1,41))
random.shuffle(productSets)

global productSet

global highlightingTechniques 
highlightingTechniques = list(range(4))+list(range(4))+list(range(4))+list(range(4))+list(range(4))
highlightingTechniques = highlightingTechniques + highlightingTechniques
random.shuffle(highlightingTechniques)

global paused
paused = True

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
    
@app.route('/start')
def start():
    return render_template('start.html')
    

@app.route('/shop')
def shop(): 
    return render_template('shop.html')
    
@app.route('/decision')
def decision():
    return render_template('decision.html')
    
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
def go_consent():
    app.logger.info('Participant has started a new session')
    emit('consent')

@socketio.on('demographics')
def go_demographics():
    app.logger.info('Participant started demographics questionaire!')
    emit('demographics')

@socketio.on('task')
def go_task():
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

@socketio.on('start')
def go_start():
    app.logger.info('Participant ready to start the task!')
    emit('start')


@socketio.on('shop')
def go_shop(selection):
    if (selection is not None):
        print('Set:' + str(selection['ProductSet']) + ' Selected Product:' + str(selection['ProductNumber']))
    app.logger.info('Participant enters Shop!')
    emit('shop', None)
        
@socketio.on('loadProduct')
def loadProduct(selection):
    if (selection is not None):
        print('Set:' + str(selection['ProductSet']) + ' Selected Product:' + str(selection['ProductNumber']))
        
    app.logger.info('New Product loaded!')
    global paused
    global productSet
    if (len(productSets) == 0):
        emit('questionaire')
    elif (len(productSets) % 10 == 0 and not paused):
        paused = True
        emit('pause')
    else:
        paused = False
        productSet = productSets.pop()
        highlightingTechnique = highlightingTechniques.pop()
        emit('loadProduct', {'ProductSet': productSet, 'HighlightingTechnique': highlightingTechnique})

@socketio.on('decision')
def go_decision():
    app.logger.info('Participant needs to decide!')
    emit('decision')

@socketio.on('loadDecision')
def go_loadDecision():
    global productSet
    emit('loadDecision', {'Set': productSet})

@socketio.on('pause')
def go_pause():
    app.logger.info('Study paused!')
    emit('pause')

@socketio.on('questionaire')
def go_questionaire():
    app.logger.info('Participant finished task and started Questionaire!')
    emit('questionaire')

@socketio.on('interview')
def go_interview():
    app.logger.info('Participant started interview!')
    emit('interview')

@socketio.on('end')
def go_end():
    app.logger.info('Participant finished study!')
    emit('end')
   

if __name__ == '__main__':
    socketio.run(app, debug=False)
    #app.run()

