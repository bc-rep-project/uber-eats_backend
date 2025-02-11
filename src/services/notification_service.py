from flask_socketio import SocketIO, emit, join_room, leave_room
from typing import Dict, Set
from datetime import datetime

socketio = SocketIO()

class NotificationService:
    # Store active connections
    user_connections: Dict[str, Set[str]] = {}  # user_id -> set of socket_ids
    restaurant_connections: Dict[str, Set[str]] = {}  # restaurant_id -> set of socket_ids
    driver_connections: Dict[str, Set[str]] = {}  # driver_id -> set of socket_ids

    @staticmethod
    @socketio.on('connect')
    def handle_connect():
        """Handle new WebSocket connection"""
        emit('connected', {'status': 'connected'})

    @staticmethod
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection"""
        socket_id = request.sid
        # Remove socket from all connection maps
        for connections in [NotificationService.user_connections, 
                          NotificationService.restaurant_connections,
                          NotificationService.driver_connections]:
            for entity_id in connections:
                if socket_id in connections[entity_id]:
                    connections[entity_id].remove(socket_id)

    @staticmethod
    @socketio.on('join')
    def handle_join(data):
        """Handle client joining a room"""
        entity_type = data.get('type')  # 'user', 'restaurant', or 'driver'
        entity_id = data.get('id')
        
        if not entity_type or not entity_id:
            return
            
        socket_id = request.sid
        room = f"{entity_type}_{entity_id}"
        join_room(room)
        
        # Store connection
        if entity_type == 'user':
            if entity_id not in NotificationService.user_connections:
                NotificationService.user_connections[entity_id] = set()
            NotificationService.user_connections[entity_id].add(socket_id)
        elif entity_type == 'restaurant':
            if entity_id not in NotificationService.restaurant_connections:
                NotificationService.restaurant_connections[entity_id] = set()
            NotificationService.restaurant_connections[entity_id].add(socket_id)
        elif entity_type == 'driver':
            if entity_id not in NotificationService.driver_connections:
                NotificationService.driver_connections[entity_id] = set()
            NotificationService.driver_connections[entity_id].add(socket_id)

    @staticmethod
    @socketio.on('leave')
    def handle_leave(data):
        """Handle client leaving a room"""
        entity_type = data.get('type')
        entity_id = data.get('id')
        
        if not entity_type or not entity_id:
            return
            
        socket_id = request.sid
        room = f"{entity_type}_{entity_id}"
        leave_room(room)
        
        # Remove connection
        if entity_type == 'user' and entity_id in NotificationService.user_connections:
            NotificationService.user_connections[entity_id].discard(socket_id)
        elif entity_type == 'restaurant' and entity_id in NotificationService.restaurant_connections:
            NotificationService.restaurant_connections[entity_id].discard(socket_id)
        elif entity_type == 'driver' and entity_id in NotificationService.driver_connections:
            NotificationService.driver_connections[entity_id].discard(socket_id)

    @staticmethod
    def notify_order_status_update(order_id: str, status: str, additional_data: dict = None):
        """Notify relevant parties about order status update"""
        data = {
            'type': 'order_status_update',
            'order_id': order_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            **additional_data if additional_data else {}
        }
        
        # Emit to order-specific room
        emit('order_update', data, room=f"order_{order_id}")

    @staticmethod
    def notify_new_order(restaurant_id: str, order_data: dict):
        """Notify restaurant about new order"""
        data = {
            'type': 'new_order',
            'order': order_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emit to restaurant room
        emit('new_order', data, room=f"restaurant_{restaurant_id}")

    @staticmethod
    def notify_order_assigned(driver_id: str, order_data: dict):
        """Notify driver about assigned order"""
        data = {
            'type': 'order_assigned',
            'order': order_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emit to driver room
        emit('order_assigned', data, room=f"driver_{driver_id}")

    @staticmethod
    def notify_payment_update(order_id: str, status: str, user_id: str):
        """Notify about payment status update"""
        data = {
            'type': 'payment_update',
            'order_id': order_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emit to user room
        emit('payment_update', data, room=f"user_{user_id}")

    @staticmethod
    def notify_delivery_update(order_id: str, status: str, location: dict = None):
        """Notify about delivery status/location update"""
        data = {
            'type': 'delivery_update',
            'order_id': order_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if location:
            data['location'] = location
            
        # Emit to order-specific room
        emit('delivery_update', data, room=f"order_{order_id}")

    @staticmethod
    def broadcast_restaurant_status(restaurant_id: str, is_online: bool):
        """Broadcast restaurant online/offline status"""
        data = {
            'type': 'restaurant_status',
            'restaurant_id': restaurant_id,
            'is_online': is_online,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast to all connected clients
        emit('restaurant_status', data, broadcast=True) 