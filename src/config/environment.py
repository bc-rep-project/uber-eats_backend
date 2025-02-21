"""Environment configuration validator"""
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def validate_environment():
    """Validate required environment variables"""
    required_vars = {
        'MONGO_URI': 'MongoDB connection string',
        'SECRET_KEY': 'Application secret key',
        'JWT_SECRET': 'JWT secret key',
        'CORS_ORIGIN': 'CORS allowed origin'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        raise EnvironmentError(
            "Missing required environment variables:\n" + 
            "\n".join(f"- {var}" for var in missing_vars)
        )
    
    # Validate MongoDB URI format
    mongo_uri = os.getenv('MONGO_URI')
    if 'mongodb+srv://' in mongo_uri:
        if not all(x in mongo_uri for x in ['@', '/', '?']):
            raise EnvironmentError(
                "Invalid MongoDB Atlas URI format. Expected format:\n"
                "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>"
                "?retryWrites=true&w=majority"
            )
    
    print("Environment validation successful")
    return True 