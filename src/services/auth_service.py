from datetime import datetime, timedelta
import jwt
import os
from models.user import User

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
        self.jwt_expiration = int(os.getenv('JWT_EXPIRATION', 86400))  # 24 hours in seconds

    def register_user(self, email, password, first_name, last_name, phone_number=None):
        try:
            user = User.create(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number
            )
            return {
                'user': self._user_to_dict(user),
                'token': self.generate_token(user)
            }
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error during registration: {str(e)}")

    def login_user(self, email, password):
        user = User.get_by_email(email)
        if not user or not user.verify_password(password):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is deactivated")

        return {
            'user': self._user_to_dict(user),
            'token': self.generate_token(user)
        }

    def generate_token(self, user):
        payload = {
            'user_id': str(user._id),
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(seconds=self.jwt_expiration)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user = User.get_by_id(payload['user_id'])
            if not user or not user.is_active:
                return None
            return user
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    def refresh_token(self, refresh_token):
        try:
            user = self.verify_token(refresh_token)
            if not user:
                raise ValueError("Invalid refresh token")
            return self.generate_token(user)
        except Exception as e:
            raise ValueError(f"Error refreshing token: {str(e)}")

    def _user_to_dict(self, user):
        """Convert user object to dictionary without sensitive information"""
        user_dict = user.to_dict()
        sensitive_fields = ['password_hash']
        for field in sensitive_fields:
            user_dict.pop(field, None)
        return user_dict

# Create a singleton instance
auth_service = AuthService() 