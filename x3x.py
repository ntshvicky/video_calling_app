import time
from flask import Flask, redirect, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room
import uuid

app = Flask(__name__)
socketio = SocketIO(app, 
                    cors_allowed_origins="*",
                    #max_http_buffer_size=9999999999
                    )

rooms = {}  # For simplicity, store rooms in-memory
pending_requests = {}

@app.route('/create_room', methods=['POST'])
def create_room():
    creator = request.json.get('creator')
    room_id = uuid.uuid4().hex[:8] # short unique id for room
    if room_id in rooms:
        return jsonify(success=False, message="Room already exists"), 400
    rooms[room_id] = {
        "participants": [],
        "creator": creator  # Save the creator_id here
    }
    return jsonify({
        "success": True,
        "room_id": room_id
    })

@app.route('/get_rooms', methods=['GET'])
def get_rooms():
    return jsonify(list(rooms.keys()))

@app.route('/delete_room/<room_id>', methods=['GET'])
def delete_room(room_id):
    del rooms[room_id]
    return jsonify({
        "success": True,
        "message": "Room deleted"
    })

@socketio.on('join')
def on_join(data):
    username = data['username']
    room_id = data['room_id']
    join_room(room_id)

    if room_id in rooms:
        if rooms[room_id]['creator'] == username:  # Check if the user is the creator
            rooms[room_id]['creator_sid'] = request.sid  # Save the creator's SID
            approveJoin(username, request.sid, room_id)
        else:
            creator_sid = rooms[room_id].get('creator_sid')
            pending_requests[request.sid] = {'username': username, "room_id": room_id}

            # Do something for regular participants
            socketio.emit('request_approval', {'username': username, 'requester_sid': request.sid, "room_id": room_id}, room=creator_sid)
    else:
        # Handle the case where the room doesn't exist
        socketio.send(f"Room {room_id} does not exist.")
    

def approveJoin(username, requester_sid, room_id):
    
    rooms[room_id]["participants"].append(username)
    
    # Notify other users in the room about the new user
    for participant in rooms[room_id]["participants"]:
        if participant != username:
            socketio.emit('user_joined', {"username": username, "userId": requester_sid}, room=participant)
        else:
            socketio.emit('user_joined', {"username": username, "userId": requester_sid}, room=room_id)
        #time.sleep(5)
    
    print(f"User {username} has joined room {room_id}")
    # Notify other users in the room about the new user
    socketio.emit('user_approved', {"username": username, "userId": requester_sid, "room_id": room_id}, room=requester_sid)

@socketio.on('approval_response')
def on_approval(data):
    approval = data.get('approved')
    requester_sid = data.get('requester_sid')
    
    if approval:
        username = pending_requests[requester_sid]['username']
        room_id = pending_requests[requester_sid]['room_id']
        approveJoin(username, requester_sid, room_id)
    else:
        socketio.emit('not_allowed', {'message': 'You are not allowed to join by the meeting owner.'}, room=requester_sid)
        
        
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

    print(f"Relaying signal from {request.sid} to {target_user}")
    # Send the signal to the specified user in the room
    socketio.emit('signal', {"userId": request.sid, "signal": signal}, room=target_user)


@socketio.on('share_screen')
def handle_share_screen(data):
    room_id = data['room_id']
    user_id = data['userId']
    is_sharing = data['isScreenSharing']
    
    # Broadcast this event to all other users in the same room
    socketio.emit('screen_sharing_status', {'userId': user_id, 'isScreenSharing': is_sharing}, room=room_id, include_self=False)
    
@socketio.on('stop_share_screen')
def handle_stop_share_screen(data):
    room_id = data['room_id']
    user_id = data['userId']
    # Broadcast to all users in the room that the stream has been updated
    socketio.emit('stream_updated', {'userId': user_id, 'type': 'webcam'}, room=room_id)

@socketio.on('request_new_stream')
def on_request_new_stream(data):
    target_user = data['userId']
    room_id = data['room_id']
    
    # Inform the target user to create a new offer for their stream
    socketio.emit('create_new_offer', {'fromUserId': request.sid}, room=target_user)


@socketio.on('new_message')
def handle_new_message(data):
    message = data['message']
    username = data['username']
    room_id = data['room_id']  # You need to have the concept of rooms

    print(f"New message from {username} in room {room_id}: {message}")

    for participant in rooms[room_id]["participants"]:
        print(participant)

    # Broadcasting the message to all users in the room
    socketio.emit('message_received', {'message': message, 'username': username}, room=room_id, include_self=False)

    # Debugging: Log to confirm message broadcasting
    print(f"Broadcasted message to room {room_id}")

@app.route('/room_join/<room_id>')
def room_join(room_id):
    if room_id in rooms.keys():
        return render_template('x2x_3.html', room_id=room_id)
    
    return redirect('/')

@app.route('/')
def index():
    return render_template('x2x_1.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
