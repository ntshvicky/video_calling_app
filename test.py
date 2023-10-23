import time
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app, 
                    cors_allowed_origins="*",
                    #max_http_buffer_size=9999999999
                    )

rooms = {}  # For simplicity, store rooms in-memory

@app.route('/create_room', methods=['POST'])
def create_room():
    room_id = request.json.get('room_id')
    if room_id in rooms:
        return jsonify(success=False, message="Room already exists"), 400
    rooms[room_id] = {"participants": []}
    return jsonify(success=True)

@app.route('/get_rooms', methods=['GET'])
def get_rooms():
    return jsonify(list(rooms.keys()))

@socketio.on('join')
def on_join(data):
    username = data['username']
    room_id = data['room_id']
    if room_id not in rooms:
        return {"success": False, "message": "Room not found"}
    join_room(room_id)
    rooms[room_id]["participants"].append(username)
    print(f"User {username} has joined room {room_id}")

    # Notify other users in the room about the new user
    for participant in rooms[room_id]["participants"]:
        if participant != username:
            socketio.emit('user_joined', {"username": username, "userId": request.sid}, room=participant)
            time.sleep(0.5)

    # Notify other users in the room about the new user
    socketio.emit('user_joined', {"username": username, "userId": request.sid}, room=room_id)
    

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room_id = data['room_id']
    if room_id not in rooms:
        return {"success": False, "message": "Room not found"}
    leave_room(room_id)
    rooms[room_id]["participants"].remove(username)
    socketio.emit('user_left', {"username": username, "userId": request.sid}, room=room_id)

@socketio.on('signal')
def on_signal(data):
    target_user = data['userId']
    room_id = data['room_id']
    signal = data['signal']


    print(f"Signal from {request.sid} to {target_user}")
    # Send the signal to the specified user in the room
    socketio.emit('signal', {"userId": request.sid, "signal": signal}, room=target_user)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
