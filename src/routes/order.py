from flask import Blueprint, request, jsonify
from models.order import Order, OrderStatus, PaymentStatus
from middleware.auth import require_auth
from config.database import db
from bson import ObjectId
from datetime import datetime

order = Blueprint('order', __name__)

@order.route('/api/orders', methods=['POST'])
@require_auth
def create_order(current_user):
    """Create a new order"""
    try:
        data = request.json
        
        # Create order instance
        order = Order(
            user_id=str(current_user['_id']),
            restaurant_id=data['restaurant_id'],
            items=data['items'],
            delivery_info=data['delivery_info'],
            payment_info=data['payment_info'],
            is_scheduled=data.get('is_scheduled', False),
            scheduled_for=data.get('scheduled_for'),
            estimated_preparation_time=data['estimated_preparation_time'],
            special_instructions=data.get('special_instructions')
        )
        
        # Insert into database
        result = db.get_db().orders.insert_one(order.dict(by_alias=True))
        order.id = str(result.inserted_id)
        
        # Update restaurant's active orders
        db.get_db().restaurants.update_one(
            {'_id': ObjectId(order.restaurant_id)},
            {'$inc': {'active_orders': 1}}
        )
        
        return jsonify(order.dict(by_alias=True)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@order.route('/api/orders/<order_id>', methods=['GET'])
@require_auth
def get_order(current_user, order_id):
    """Get order details"""
    try:
        order_data = db.get_db().orders.find_one({'_id': ObjectId(order_id)})
        if not order_data:
            return jsonify({'error': 'Order not found'}), 404
            
        # Check if user has permission to view this order
        if str(order_data['user_id']) != str(current_user['_id']) and \
           current_user['role'] not in ['admin', 'restaurant_owner']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        return jsonify({**order_data, '_id': str(order_data['_id'])}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@order.route('/api/orders/<order_id>/status', methods=['PUT'])
@require_auth
def update_order_status(current_user, order_id):
    """Update order status"""
    try:
        data = request.json
        new_status = data['status']
        
        # Validate status
        if new_status not in OrderStatus.__members__:
            return jsonify({'error': 'Invalid status'}), 400
            
        # Get order
        order_data = db.get_db().orders.find_one({'_id': ObjectId(order_id)})
        if not order_data:
            return jsonify({'error': 'Order not found'}), 404
            
        # Check permissions
        if current_user['role'] not in ['admin', 'restaurant_owner']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Update status
        db.get_db().orders.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': new_status,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # If order is delivered or cancelled, decrement restaurant's active orders
        if new_status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            db.get_db().restaurants.update_one(
                {'_id': ObjectId(order_data['restaurant_id'])},
                {'$inc': {'active_orders': -1}}
            )
        
        return jsonify({'message': 'Order status updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@order.route('/api/orders/<order_id>/payment', methods=['PUT'])
@require_auth
def update_payment_status(current_user, order_id):
    """Update order payment status"""
    try:
        data = request.json
        new_status = data['status']
        
        # Validate status
        if new_status not in PaymentStatus.__members__:
            return jsonify({'error': 'Invalid payment status'}), 400
            
        # Get order
        order_data = db.get_db().orders.find_one({'_id': ObjectId(order_id)})
        if not order_data:
            return jsonify({'error': 'Order not found'}), 404
            
        # Check permissions
        if str(order_data['user_id']) != str(current_user['_id']) and \
           current_user['role'] not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Update payment status
        db.get_db().orders.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'payment_info.status': new_status,
                    'payment_info.transaction_id': data.get('transaction_id'),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return jsonify({'message': 'Payment status updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@order.route('/api/orders', methods=['GET'])
@require_auth
def list_orders(current_user):
    """List orders with filtering options"""
    try:
        # Parse query parameters
        status = request.args.get('status')
        restaurant_id = request.args.get('restaurant_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        
        # Build query
        query = {}
        if status:
            query['status'] = status
        if restaurant_id:
            query['restaurant_id'] = restaurant_id
            
        # Add date range if provided
        if from_date or to_date:
            query['created_at'] = {}
            if from_date:
                query['created_at']['$gte'] = datetime.fromisoformat(from_date)
            if to_date:
                query['created_at']['$lte'] = datetime.fromisoformat(to_date)
                
        # Add user filter based on role
        if current_user['role'] == 'customer':
            query['user_id'] = str(current_user['_id'])
        elif current_user['role'] == 'restaurant_owner':
            query['restaurant_id'] = {'$in': current_user['restaurant_ids']}
            
        # Execute query
        orders = list(db.get_db().orders.find(query)
                     .sort('created_at', -1)
                     .skip(skip)
                     .limit(limit))
                     
        # Convert ObjectId to string
        for order in orders:
            order['_id'] = str(order['_id'])
            
        return jsonify(orders), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400 