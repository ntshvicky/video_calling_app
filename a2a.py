import time
from flask import Flask, redirect, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send
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
    creator = request.json.get('creator')  # Assuming the creator_id is sent in the POST request as JSON
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

    print(rooms[room_id]['creator'], username)

    if room_id in rooms:
        if rooms[room_id]['creator'] == username:  # Check if the user is the creator
            rooms[room_id]['creator_sid'] = request.sid  # Save the creator's SID
            print(f"The creator's SID is {request.sid}")  # Print the SID of the creator
            join_room(room_id)
            rooms[room_id]["participants"].append(username)
            socketio.emit('user_joined', {"username": username, "userId": request.sid}, room=room_id)
            time.sleep(1)
            socketio.emit('user_approved', room=request.sid)
        else:
            creator_sid = rooms[room_id].get('creator_sid')
            pending_requests[request.sid] = {'username': username, 'room_id': room_id}

            # Do something for regular participants
            socketio.emit('request_approval', {'username': username, 'requester_sid': request.sid, 'room_id': room_id}, room=creator_sid)
    else:
        # Handle the case where the room doesn't exist
        socketio.send(f"Room {room_id} does not exist.")
    
@socketio.on('approval_response')
def on_approval(data):
    approval = data.get('approved')
    requester_sid = data.get('requester_sid')
    
    if approval:
        
        username = pending_requests[requester_sid]['username']
        room_id = pending_requests[requester_sid]['room_id']
        join_room(room_id)
        rooms[room_id]["participants"].append(username)
        
        # Notify other users in the room about the new user
        for participant in rooms[room_id]["participants"]:
            if participant != username:
                socketio.emit('user_joined', {"username": username, "userId": requester_sid}, room=participant)
                time.sleep(3)
        
        print(f"User {username} has joined room {room_id}")

        # Notify other users in the room about the new user
        socketio.emit('user_joined', {"username": username, "userId": requester_sid}, room=room_id)
        time.sleep(2)
        socketio.emit('user_approved', room=requester_sid)
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

    print(f"Signal from {request.sid} to {target_user}")
    # Send the signal to the specified user in the room
    socketio.emit('signal', {"userId": request.sid, "signal": signal}, room=target_user)

@app.route('/room_join/<room_id>')
def room_join(room_id):
    if room_id in rooms.keys():
        return render_template('a2a_2.html', room_id=room_id)
    
    return redirect('/')

@app.route('/')
def index():
    return render_template('a2a_1.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
