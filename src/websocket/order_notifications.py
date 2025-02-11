from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps
import jwt
from config.stripe import stripe_keys

socketio = SocketIO()

def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not ('token' in kwargs and kwargs['token']):
            disconnect()
            return False
        try:
            decoded = jwt.decode(kwargs['token'], stripe_keys['secret_key'], algorithms=["HS256"])
            kwargs['user_id'] = decoded['user_id']
            kwargs['role'] = decoded['role']
            return f(*args, **kwargs)
        except jwt.InvalidTokenError:
            disconnect()
            return False
    return wrapped

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    return True

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    pass

@socketio.on('join')
@authenticated_only
def on_join(data, user_id=None, role=None):
    """Join order notification rooms"""
    if not data.get('rooms'):
        return
        
    # Join relevant rooms based on user role
    for room in data['rooms']:
        if role == 'admin':
            join_room(room)
        elif role == 'restaurant_owner' and room.startswith('restaurant_'):
            # Verify restaurant ownership here
            join_room(room)
        elif role == 'driver' and room.startswith('driver_'):
            if room == f'driver_{user_id}':
                join_room(room)
        elif room == f'user_{user_id}':
            join_room(room)

@socketio.on('leave')
@authenticated_only
def on_leave(data, user_id=None, role=None):
    """Leave order notification rooms"""
    if not data.get('rooms'):
        return
        
    for room in data['rooms']:
        leave_room(room)

def notify_order_status_update(order_id, restaurant_id, user_id, driver_id, status, estimated_delivery_time=None):
    """Send order status update notification"""
    notification = {
        'type': 'order_status_update',
        'order_id': order_id,
        'status': status,
        'estimated_delivery_time': estimated_delivery_time
    }
    
    # Notify all relevant parties
    emit('notification', notification, room=f'order_{order_id}')
    emit('notification', notification, room=f'restaurant_{restaurant_id}')
    emit('notification', notification, room=f'user_{user_id}')
    
    if driver_id:
        emit('notification', notification, room=f'driver_{driver_id}')

def notify_new_order(order_id, restaurant_id):
    """Send new order notification"""
    notification = {
        'type': 'new_order',
        'order_id': order_id
    }
    
    emit('notification', notification, room=f'restaurant_{restaurant_id}')

def notify_order_assignment(order_id, driver_id):
    """Send order assignment notification to driver"""
    notification = {
        'type': 'order_assignment',
        'order_id': order_id
    }
    
    emit('notification', notification, room=f'driver_{driver_id}') 