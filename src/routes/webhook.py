from flask import Blueprint, request, jsonify
import paypalrestsdk
from config.paypal import paypal_keys
from services.order_service import OrderService
from models.order import PaymentStatus

webhook = Blueprint('webhook', __name__)

@webhook.route('/api/webhook/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook events"""
    try:
        # Verify webhook signature
        webhook_id = paypal_keys['webhook_id']
        event_body = request.get_json()
        event_type = event_body.get('event_type')
        
        # Handle the event
        if event_type == 'PAYMENT.SALE.COMPLETED':
            resource = event_body.get('resource', {})
            custom = resource.get('custom', '')  # This contains our order ID
            
            if custom:
                OrderService.update_payment_status(
                    order_id=custom,
                    payment_status=PaymentStatus.COMPLETED,
                    transaction_id=resource.get('id')
                )
                
        elif event_type == 'PAYMENT.SALE.DENIED':
            resource = event_body.get('resource', {})
            custom = resource.get('custom', '')
            
            if custom:
                OrderService.update_payment_status(
                    order_id=custom,
                    payment_status=PaymentStatus.FAILED,
                    transaction_id=resource.get('id')
                )
                
        elif event_type == 'PAYMENT.SALE.REFUNDED':
            resource = event_body.get('resource', {})
            custom = resource.get('custom', '')
            
            if custom:
                OrderService.update_payment_status(
                    order_id=custom,
                    payment_status=PaymentStatus.REFUNDED,
                    transaction_id=resource.get('id')
                )

        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400 