from pymongo import MongoClient
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
            
            # Print debug information
            print(f"CA File: {certifi.where()}")
            print(f"Certifi Version: {certifi.__version__}")
            print(f"SSL Version: {ssl.OPENSSL_VERSION}")
            
            # Connect to MongoDB with SSL configuration
            if 'mongodb+srv' in mongo_uri:
                # Atlas connection with SSL
                self.client = MongoClient(
                    mongo_uri,
                    server_api=ServerApi('1'),
                    tlsCAFile=certifi.where(),
                    tls=True,
                    tlsAllowInvalidCertificates=True,  # Temporarily allow invalid certs for debugging
                    retryWrites=True,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                    w='majority'
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
            
            # Print connection details for debugging
            server_info = self.client.server_info()
            print(f"Connected to MongoDB version: {server_info.get('version', 'unknown')}")
            print(f"Server connection parameters: {self.client.options}")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
            if 'mongodb+srv' in mongo_uri:
                print("Connection Details:")
                print(f"CA File: {certifi.where()}")
                print(f"MongoDB URI format: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority")
                print(f"Certifi Version: {certifi.__version__}")
                print(f"SSL Version: {ssl.OPENSSL_VERSION}")
            raise e
    
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