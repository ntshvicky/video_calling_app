from flask import Flask, jsonify, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
import uuid
from flask_socketio import SocketIO, join_room, leave_room

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meeting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Room(db.Model):
    id = db.Column(db.String, primary_key=True)
    participants = db.Column(db.PickleType, nullable=False, default=[])

db.create_all()

socketio = SocketIO(app, cors_allowed_origins="*")


rooms = {}  # For simplicity, store rooms in-memory


@app.route('/create_room', methods=['POST'])
def create_room():
    room_id = uuid.uuid4().hex[:8] # short unique id for room
    if room_id in rooms:
        return jsonify(success=False, message="Room already exists"), 400
    new_room = Room(id=room_id)
    db.session.add(new_room)
    db.session.commit()
    return jsonify(success=True, room_id=room_id)

@app.route('/get_rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([room.id for room in rooms])

@app.route('/delete_room/<room_id>', methods=['GET'])
def delete_room(room_id):
    room = Room.query.get(room_id)
    if room:
        db.session.delete(room)
        db.session.commit()
        return jsonify(success=True, message="Room deleted")
    return jsonify(success=False, message="Room not found")

@socketio.on('join')
def on_join(data):
    username = data['username']
    room_id = data['room_id']
    room = Room.query.get(room_id)
    if not room:
        return {"success": False, "message": "Room not found"}
    join_room(room_id)
    if username not in room.participants:
        room.participants.append(username)
        db.session.commit()

    # Notify other users in the room about the new user
    for participant in rooms[room_id]["participants"]:
        if participant != username:
            socketio.emit('user_joined', {"username": username, "userId": request.sid}, room=participant)

    print(f"User {username} has joined room {room_id}")

    # Notify other users in the room about the new user
    socketio.emit('user_joined', {"username": username, "userId": request.sid}, room=room_id)
    

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room_id = data['room_id']
    room = Room.query.get(room_id)
    if not room:
        return {"success": False, "message": "Room not found"}
    leave_room(room_id)
    if username in room.participants:
        room.participants.remove(username)
        db.session.commit()

    socketio.emit('user_left', {"username": username, "userId": request.sid}, room=room_id)

@socketio.on('signal')
def on_signal(data):
    target_user = data['userId']
    room_id = data['room_id']
    signal = data['signal']

    print(f"Signal from {request.sid} to {target_user}")
    # Send the signal to the specified user in the room
    socketio.emit('signal', {"userId": request.sid, "signal": signal}, room=target_user)


@socketio.on('share_screen')
def handle_share_screen(data):
    room_id = data['room_id']
    room = Room.query.get(room_id)
    if not room:
        return {"success": False, "message": "Room not found"}
    user_id = data['userId']
    is_sharing = data['isScreenSharing']

    
    # Broadcast this event to all other users in the same room
    socketio.emit('screen_sharing_status', {'userId': user_id, 'isScreenSharing': is_sharing}, room=room_id, include_self=False)
    
@socketio.on('stop_share_screen')
def handle_stop_share_screen(data):
    room_id = data['room_id']
    room = Room.query.get(room_id)
    if not room:
        return {"success": False, "message": "Room not found"}
    
    user_id = data['userId']
    # Broadcast to all users in the room that the stream has been updated
    socketio.emit('stream_updated', {'userId': user_id, 'type': 'webcam'}, room=room_id)

@socketio.on('request_new_stream')
def on_request_new_stream(data):
    target_user = data['userId']
    room_id = data['room_id']
    room = Room.query.get(room_id)
    if not room:
        return {"success": False, "message": "Room not found"}

    
    # Inform the target user to create a new offer for their stream
    socketio.emit('create_new_offer', {'fromUserId': request.sid}, room=target_user)


@socketio.on('new_message')
def handle_new_message(data):
    message = data['message']
    username = data['username']
    room_id = data['room_id']  # You need to have the concept of rooms

    room = Room.query.get(room_id)
    if not room:
        return {"success": False, "message": "Room not found"}

    # Broadcasting the message to all users in the room
    socketio.emit('message_received', {'message': message, 'username': username}, room=room_id, include_self=False)

@app.route('/room_join/<room_id>')
def room_join(room_id):
    room = Room.query.get(room_id)
    if room:
        return render_template('x2x_2.html', room_id=room_id)
    
    return redirect('/')

@app.route('/')
def index():
    return render_template('x2x_1.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
