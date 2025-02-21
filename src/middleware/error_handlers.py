from flask import jsonify
from werkzeug.exceptions import HTTPException
from jwt.exceptions import PyJWTError

# Custom business logic errors
class BusinessError(Exception):
    def __init__(self, message, code, status_code=400, details=None):
        super().__init__()
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'message': 'Bad request',
            'code': 'INVALID_REQUEST_FORMAT',
            'details': str(error)
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'message': 'Unauthorized',
            'code': 'AUTH_INVALID_CREDENTIALS',
            'details': str(error)
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'message': 'Forbidden',
            'code': 'AUTH_PERMISSION_DENIED',
            'details': str(error)
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'message': 'Resource not found',
            'code': 'RESOURCE_NOT_FOUND',
            'details': str(error)
        }), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'message': 'Too many requests',
            'code': 'RATE_LIMIT_EXCEEDED',
            'details': str(error)
        }), 429

    @app.errorhandler(PyJWTError)
    def handle_jwt_error(error):
        return jsonify({
            'message': 'Invalid or expired token',
            'code': 'AUTH_TOKEN_EXPIRED',
            'details': str(error)
        }), 401

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        if isinstance(error, HTTPException):
            return jsonify({
                'message': error.description,
                'code': 'HTTP_ERROR',
                'details': str(error)
            }), error.code
        
        # Log the error here
        app.logger.error(f"Unexpected error: {str(error)}")
        
        return jsonify({
            'message': 'Internal server error',
            'code': 'SERVER_ERROR',
            'details': str(error) if app.debug else 'An unexpected error occurred'
        }), 500

    @app.errorhandler(BusinessError)
    def handle_business_error(error):
        return jsonify({
            'message': error.message,
            'code': error.code,
            'details': error.details
        }), error.status_code 