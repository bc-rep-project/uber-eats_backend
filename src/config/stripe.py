import os

stripe_keys = {
    'secret_key': os.getenv('STRIPE_SECRET_KEY', 'your_stripe_secret_key'),
    'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY', 'your_stripe_publishable_key'),
    'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET', 'your_stripe_webhook_secret')
}

def validate_stripe_config():
    """Validate Stripe configuration"""
    required_keys = ['secret_key', 'publishable_key', 'webhook_secret']
    for key in required_keys:
        if not stripe_keys[key] or stripe_keys[key].startswith('your_stripe_'):
            raise ValueError(f"Missing or invalid Stripe {key}. Please set the STRIPE_{key.upper()} environment variable.") 