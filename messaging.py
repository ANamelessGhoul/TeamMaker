import functools
from flask import render_template, abort, request, redirect, url_for
from flask_login import current_user
from flask_socketio import join_room, leave_room, send, disconnect, emit

from database import Database

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

        print('received message: "' + data['data'] + '" from: ' + current_user.data.name + ' in room: ' + str(room))
        data['username'] = current_user.data.name
        data['id'] = current_user.data.id

        Database.getInstance().InsertMessage(data['id'], room, data['data'])

        emit('message',data, room=room)

    @socketio.on('join')
    @authenticated_only
    def on_join(data):
        user_data = current_user.data
        room = data['room']
        if not Database.getInstance().IsUserInChatroom(user_data.id, room):
            disconnect()
            return

        join_room(room)
        print(user_data.name + ' connected to room: ' + str(room))
        emit('register',user_data.id, room=request.sid)

    @socketio.on('leave')
    def on_leave(data):
        username = current_user.data.name
        room = data['room']
        leave_room(room)
        print(current_user.data.name + ' disconnected from room: ' + str(room))
