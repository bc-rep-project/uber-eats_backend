import os

paypal_keys = {
    'client_id': os.getenv('PAYPAL_CLIENT_ID', 'your_paypal_client_id'),
    'client_secret': os.getenv('PAYPAL_CLIENT_SECRET', 'your_paypal_client_secret'),
    'mode': os.getenv('PAYPAL_MODE', 'sandbox'),
    'webhook_id': os.getenv('PAYPAL_WEBHOOK_ID', 'your_paypal_webhook_id')
}

def validate_paypal_config():
    """Validate PayPal configuration"""
    required_keys = ['client_id', 'client_secret', 'mode', 'webhook_id']
    for key in required_keys:
        if not paypal_keys[key] or paypal_keys[key].startswith('your_paypal_'):
            raise ValueError(f"Missing or invalid PayPal {key}. Please set the PAYPAL_{key.upper()} environment variable.") 