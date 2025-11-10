from flask import Blueprint
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
import logging

# Register SocketIO event handlers
socketio_bp = Blueprint('socketio', __name__)
logger = logging.getLogger(__name__)


def init_socketio_events(socketio, app):
    """Initialize SocketIO event handlers"""

    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            app.logger.info(f"User {current_user.username} connected via WebSocket")
            emit('connection_response', {'status': 'connected', 'user': current_user.username})
        else:
            app.logger.warning("Unauthenticated WebSocket connection attempt")

    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            app.logger.info(f"User {current_user.username} disconnected")

    @socketio.on('join_room')
    def handle_join_room(data):
        if current_user.is_authenticated:
            room = data.get('room', f'user_{current_user.id}')
            join_room(room)
            app.logger.info(f"User {current_user.username} joined room {room}")
            emit('room_joined', {'room': room, 'status': 'success'})

    @socketio.on('leave_room')
    def handle_leave_room(data):
        if current_user.is_authenticated:
            room = data.get('room', f'user_{current_user.id}')
            leave_room(room)
            app.logger.info(f"User {current_user.username} left room {room}")
