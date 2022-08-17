from flask import Flask, render_template
from flask_socketio import SocketIO
import csv

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
aois = {}

#Routing Requests

#Initial routing request

@app.route('/')
def index(): 
    return render_template('aoi.html')
    

@socketio.on('message')
def test_message(message):
    print('Incoming message:',message)
    app.logger.info('Incoming message: %s',message)
    
@socketio.on('coordinates')
def go_coordinates(c):
    app.logger.info('Shop sent coordinates')
    coordinates = [c['x1'], c['y1'], c['x2'], c['y2']]
    key = c['Id']
    aois[key] = coordinates

@socketio.on('end')
def go_end():
    with open('./aois.csv', 'a') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow(['Id','x1','y1','x2','y2'])
        for aoi in aois:
            filewriter.writerow([aoi]+aois[aoi])
            
    print('Done!')
   

if __name__ == '__main__':
    socketio.run(app, debug=False)
    #app.run()