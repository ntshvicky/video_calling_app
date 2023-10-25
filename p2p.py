from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/<meet_id>')
def index(meet_id):
    return render_template('p2p.html')

@socketio.on('signal')
def handle_signal(data):
    # Relay the signal to all other connected clients.
    send(data, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
