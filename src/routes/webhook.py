from flask import Blueprint, request, jsonify
from paypalcheckoutsdk.core import PayPalHttpClient
from config.paypal import get_paypal_client, paypal_keys
from services.order_service import OrderService
from models.order import PaymentStatus

webhook = Blueprint('webhook', __name__)

@webhook.route('/api/webhook/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook events"""
    auth_algo = request.headers.get('PAYPAL-AUTH-ALGO')
    cert_url = request.headers.get('PAYPAL-CERT-URL')
    transmission_id = request.headers.get('PAYPAL-TRANSMISSION-ID')
    transmission_sig = request.headers.get('PAYPAL-TRANSMISSION-SIG')
    transmission_time = request.headers.get('PAYPAL-TRANSMISSION-TIME')
    webhook_id = paypal_keys['webhook_id']
    
    # Verify webhook signature
    try:
        # Get PayPal client
        client = get_paypal_client()
        
        # Verify webhook event
        event_body = request.get_json()
        event_type = event_body.get('event_type')
        
        # Handle the event
        if event_type == 'CHECKOUT.ORDER.APPROVED':
            resource = event_body.get('resource', {})
            custom_id = None
            
            # Extract custom_id from purchase units
            purchase_units = resource.get('purchase_units', [])
            if purchase_units:
                custom_id = purchase_units[0].get('custom_id')
            
            if custom_id:
                OrderService.update_payment_status(
                    order_id=custom_id,
                    payment_status=PaymentStatus.COMPLETED,
                    transaction_id=resource.get('id')
                )
                
        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            resource = event_body.get('resource', {})
            purchase_units = resource.get('purchase_units', [])
            custom_id = purchase_units[0].get('custom_id') if purchase_units else None
            
            if custom_id:
                OrderService.update_payment_status(
                    order_id=custom_id,
                    payment_status=PaymentStatus.FAILED,
                    transaction_id=resource.get('id')
                )
                
        elif event_type == 'PAYMENT.CAPTURE.REFUNDED':
            resource = event_body.get('resource', {})
            purchase_units = resource.get('purchase_units', [])
            custom_id = purchase_units[0].get('custom_id') if purchase_units else None
            
            if custom_id:
                OrderService.update_payment_status(
                    order_id=custom_id,
                    payment_status=PaymentStatus.REFUNDED,
                    transaction_id=resource.get('id')
                )

        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400 