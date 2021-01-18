import functools
from flask import render_template, abort, request, redirect, url_for
from flask_login import current_user
from flask_socketio import join_room, leave_room, send, disconnect, emit

def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

def initializeEvents(socketio):

    @socketio.on('message')
    @authenticated_only
    def handle_message(data):
        if(data['data'] == ''):
            return
        room = data['room']
        print(request.sid)
        print('received message: "' + data['data'] + '" from: ' + current_user.data.name + ' in room: ' + str(room))
        data['username'] = current_user.data.name
        data['id'] = current_user.data.id
        emit('message',data, room=room)

    @socketio.on('join')
    @authenticated_only
    def on_join(data):
        username = current_user.data.name
        room = data['room']
        join_room(room)
        print(current_user.data.name + ' connected to room: ' + str(room))
        emit('register',current_user.data.id, room=request.sid)
        #send(username + ' has entered the room.', room=room)

    @socketio.on('leave')
    def on_leave(data):
        username = current_user.data.name
        room = data['room']
        leave_room(room)
        print(current_user.data.name + ' disconnected from room: ' + str(room))
        #send(username + ' has left the room.', room=room)
