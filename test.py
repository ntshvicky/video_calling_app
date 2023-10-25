
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('test.html')

@socketio.on('create_room')
def create_room(data):
    room = data['room']
    join_room(room)
    emit('room_status', {'message': f'Room {room} created.'}, room=room)

@socketio.on('join_room')
def join_a_room(data):
    room = data['room']
    join_room(room)
    emit('room_status', {'message': f'User joined room {room}.'}, room=room)

@socketio.on('leave_room')
def leave_a_room(data):
    room = data['room']
    leave_room(room)
    emit('room_status', {'message': f'User left room {room}.'}, room=room)

@socketio.on('signal')
def handle_signal(data):
    room = data.get('room', None)
    if room:
        emit('signal', data, room=room)
    else:
        send(data, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
