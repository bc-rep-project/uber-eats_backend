from datetime import datetime
from typing import List, Optional
from models.order import Order, OrderStatus, PaymentStatus
from models.restaurant import Restaurant
from config.database import db
import paypalrestsdk
from config.paypal import paypal_keys
from bson import ObjectId

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": paypal_keys['mode'],  # sandbox or live
    "client_id": paypal_keys['client_id'],
    "client_secret": paypal_keys['client_secret']
})

class OrderService:
    @staticmethod
    def create_order(user_id: str, order_data: dict) -> Order:
        """Create a new order"""
        # Validate restaurant exists and is active
        restaurant = db.get_db().restaurants.find_one({
            '_id': ObjectId(order_data['restaurant_id']),
            'is_active': True
        })
        if not restaurant:
            raise ValueError("Restaurant not found or is inactive")
            
        # Calculate order total and validate items
        total = 0
        for item in order_data['items']:
            menu_item = db.get_db().menu_items.find_one({
                '_id': ObjectId(item['menu_item_id']),
                'restaurant_id': order_data['restaurant_id'],
                'is_available': True
            })
            if not menu_item:
                raise ValueError(f"Menu item {item['menu_item_id']} not found or unavailable")
            
            # Calculate item total with customizations
            item_total = menu_item['price'] * item['quantity']
            for customization in item.get('customizations', []):
                for option in customization['options']:
                    option_price = next(
                        (opt['price'] for cust in menu_item['customizations']
                         for opt in cust['options']
                         if opt['name'] == option),
                        0
                    )
                    item_total += option_price * item['quantity']
            
            item['unit_price'] = menu_item['price']
            item['subtotal'] = item_total
            total += item_total
            
        # Calculate fees and taxes
        delivery_fee = restaurant['delivery_fee'] if order_data.get('is_delivery') else 0
        service_fee = total * 0.05  # 5% service fee
        
        # Calculate applicable taxes
        tax_total = 0
        tax_rules = db.get_db().tax_rules.find({
            'restaurant_id': order_data['restaurant_id'],
            'is_active': True
        })
        
        for rule in tax_rules:
            if total >= rule['minimum_order_amount']:
                if (order_data.get('is_delivery') and rule['applies_to_delivery']) or \
                   (not order_data.get('is_delivery') and rule['applies_to_pickup']):
                    tax_total += total * (float(rule['rate']) / 100)
        
        # Create payment info
        payment_info = {
            'method': order_data['payment_method'],
            'subtotal': total,
            'tax': tax_total,
            'delivery_fee': delivery_fee,
            'service_fee': service_fee,
            'tip': order_data.get('tip', 0),
            'total': total + tax_total + delivery_fee + service_fee + order_data.get('tip', 0),
            'status': PaymentStatus.PENDING
        }
        
        # Create order instance
        order = Order(
            user_id=user_id,
            restaurant_id=order_data['restaurant_id'],
            items=order_data['items'],
            delivery_info=order_data['delivery_info'],
            payment_info=payment_info,
            is_scheduled=order_data.get('is_scheduled', False),
            scheduled_for=order_data.get('scheduled_for'),
            estimated_preparation_time=restaurant['preparation_time'],
            special_instructions=order_data.get('special_instructions')
        )
        
        # Process payment if not cash
        if order_data['payment_method'] != 'cash':
            try:
                # Create PayPal payment
                payment = paypalrestsdk.Payment({
                    "intent": "sale",
                    "payer": {
                        "payment_method": "paypal"
                    },
                    "transactions": [{
                        "amount": {
                            "total": str(payment_info['total']),
                            "currency": "USD"
                        },
                        "custom": str(order.id),  # Store order ID for webhook
                        "description": f"Order from {restaurant['name']}"
                    }],
                    "redirect_urls": {
                        "return_url": "http://localhost:3000/order/success",
                        "cancel_url": "http://localhost:3000/order/cancel"
                    }
                })

                if payment.create():
                    order.payment_info.transaction_id = payment.id
                else:
                    raise ValueError(payment.error)
                    
            except Exception as e:
                raise ValueError(f"Payment processing failed: {str(e)}")
        
        # Save order to database
        result = db.get_db().orders.insert_one(order.dict(by_alias=True))
        order.id = str(result.inserted_id)
        
        # Update restaurant's active orders count
        db.get_db().restaurants.update_one(
            {'_id': ObjectId(order.restaurant_id)},
            {'$inc': {'active_orders': 1}}
        )
        
        return order

    @staticmethod
    def get_order(order_id: str) -> dict:
        """Get order details"""
        order = db.get_db().orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            raise ValueError("Order not found")
        return {**order, '_id': str(order['_id'])}

    @staticmethod
    def update_order_status(order_id: str, new_status: str) -> None:
        """Update order status"""
        if new_status not in OrderStatus.__members__:
            raise ValueError("Invalid status")
            
        order = db.get_db().orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            raise ValueError("Order not found")
            
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
        
        # If order is completed or cancelled, update restaurant's active orders
        if new_status in [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]:
            db.get_db().restaurants.update_one(
                {'_id': ObjectId(order['restaurant_id'])},
                {'$inc': {'active_orders': -1}}
            )

    @staticmethod
    def update_payment_status(order_id: str, payment_status: str, transaction_id: Optional[str] = None) -> None:
        """Update payment status"""
        if payment_status not in PaymentStatus.__members__:
            raise ValueError("Invalid payment status")
            
        update = {
            'payment_info.status': payment_status,
            'updated_at': datetime.utcnow()
        }
        if transaction_id:
            update['payment_info.transaction_id'] = transaction_id
            
        result = db.get_db().orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': update}
        )
        
        if result.modified_count == 0:
            raise ValueError("Order not found")

    @staticmethod
    def list_orders(
        user_id: Optional[str] = None,
        restaurant_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[dict]:
        """List orders with filtering"""
        query = {}
        
        if user_id:
            query['user_id'] = user_id
        if restaurant_id:
            query['restaurant_id'] = restaurant_id
        if status:
            query['status'] = status
            
        if from_date or to_date:
            query['created_at'] = {}
            if from_date:
                query['created_at']['$gte'] = from_date
            if to_date:
                query['created_at']['$lte'] = to_date
                
        orders = list(db.get_db().orders.find(query)
                     .sort('created_at', -1)
                     .skip(skip)
                     .limit(limit))
                     
        # Convert ObjectId to string
        for order in orders:
            order['_id'] = str(order['_id'])
            
        return orders

    @staticmethod
    def cancel_order(order_id: str) -> None:
        """Cancel an order"""
        order = db.get_db().orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            raise ValueError("Order not found")
            
        if order['status'] not in [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value]:
            raise ValueError("Order cannot be cancelled")
            
        # Process refund if payment was completed
        if order['payment_info']['status'] == PaymentStatus.COMPLETED.value:
            try:
                # Create PayPal refund
                sale = paypalrestsdk.Sale.find(order['payment_info']['transaction_id'])
                refund = sale.refund({
                    "amount": {
                        "total": str(order['payment_info']['total']),
                        "currency": "USD"
                    }
                })
                
                if refund.success():
                    # Update payment status
                    db.get_db().orders.update_one(
                        {'_id': ObjectId(order_id)},
                        {'$set': {'payment_info.status': PaymentStatus.REFUNDED.value}}
                    )
                else:
                    raise ValueError(refund.error)
                    
            except Exception as e:
                raise ValueError(f"Refund failed: {str(e)}")
        
        # Update order status
        db.get_db().orders.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': OrderStatus.CANCELLED.value,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Update restaurant's active orders count
        db.get_db().restaurants.update_one(
            {'_id': ObjectId(order['restaurant_id'])},
            {'$inc': {'active_orders': -1}}
        ) 