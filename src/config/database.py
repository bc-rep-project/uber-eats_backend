from pymongo import MongoClient, ASCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import certifi
import ssl

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        
    def connect(self):
        try:
            # Get MongoDB URI from environment variables or use default
            mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ubereats')
            
            # Connect to MongoDB with SSL configuration
            if 'mongodb+srv' in mongo_uri:
                # Atlas connection with SSL
                self.client = MongoClient(
                    mongo_uri,
                    server_api=ServerApi('1'),  # Use stable API
                    tls=True,
                    tlsCAFile=certifi.where(),
                    tlsAllowInvalidCertificates=False,
                    tlsInsecure=False,
                    retryWrites=True,
                    w='majority',
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                    minPoolSize=0,
                    maxPoolSize=100,
                    ssl_match_hostname=True,
                    ssl_cert_reqs=ssl.CERT_REQUIRED,
                    ssl_ca_certs=certifi.where()
                )
            else:
                # Local connection
                self.client = MongoClient(mongo_uri)
            
            # Get database name from URI or use default
            db_name = os.getenv('MONGODB_NAME', 'ubereats')
            self.db = self.client.get_database(db_name)
            
            # Test connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB")
            
            # Create indexes if needed
            self._ensure_indexes()
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
            if 'mongodb+srv' in mongo_uri:
                print("Connection Details:")
                print(f"CA File: {certifi.where()}")
                print(f"MongoDB URI format: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority")
                print(f"Python version: {ssl.OPENSSL_VERSION}")
                print(f"SSL/TLS version: {ssl.OPENSSL_VERSION_INFO}")
            raise e
    
    def _ensure_indexes(self):
        """Create necessary indexes if they don't exist"""
        try:
            # Example: Create index on users collection
            self.db.users.create_index([("email", ASCENDING)], unique=True)
            # Add more indexes as needed
        except Exception as e:
            print(f"Warning: Could not create indexes: {str(e)}")
    
    def get_db(self):
        if not self.db:
            self.connect()
        return self.db
    
    def close(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

# Create a singleton instance
db = Database() 