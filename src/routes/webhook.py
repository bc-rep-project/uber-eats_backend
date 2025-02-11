from flask import Blueprint, request, jsonify
import stripe
from config.stripe import stripe_keys
from services.order_service import OrderService
from models.order import PaymentStatus

webhook = Blueprint('webhook', __name__)

@webhook.route('/api/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys['webhook_secret']
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    try:
        if event.type == 'payment_intent.succeeded':
            payment_intent = event.data.object
            order_id = payment_intent.metadata.get('order_id')
            
            if order_id:
                OrderService.update_payment_status(
                    order_id=order_id,
                    payment_status=PaymentStatus.COMPLETED,
                    transaction_id=payment_intent.id
                )
                
        elif event.type == 'payment_intent.payment_failed':
            payment_intent = event.data.object
            order_id = payment_intent.metadata.get('order_id')
            
            if order_id:
                OrderService.update_payment_status(
                    order_id=order_id,
                    payment_status=PaymentStatus.FAILED,
                    transaction_id=payment_intent.id
                )
                
        elif event.type == 'charge.refunded':
            charge = event.data.object
            payment_intent_id = charge.payment_intent
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            order_id = payment_intent.metadata.get('order_id')
            
            if order_id:
                OrderService.update_payment_status(
                    order_id=order_id,
                    payment_status=PaymentStatus.REFUNDED,
                    transaction_id=payment_intent_id
                )

        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400 