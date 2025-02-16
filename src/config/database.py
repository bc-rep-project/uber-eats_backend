from pymongo import MongoClient, ASCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import certifi
import ssl
import urllib.parse

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
                # Parse the URI to add additional options
                if '?' in mongo_uri:
                    mongo_uri += '&'
                else:
                    mongo_uri += '?'
                mongo_uri += urllib.parse.urlencode({
                    'tls': 'true',
                    'tlsAllowInvalidCertificates': 'true',
                    'retryWrites': 'true',
                    'w': 'majority'
                })
                
                # Atlas connection with SSL
                self.client = MongoClient(
                    mongo_uri,
                    server_api=ServerApi('1'),
                    tlsCAFile=certifi.where(),
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                    connect=True,
                    minPoolSize=0
                )
            else:
                # Local connection
                self.client = MongoClient(mongo_uri)
            
            # Get database name from URI or use default
            db_name = os.getenv('MONGODB_NAME', 'ubereats')
            self.db = self.client.get_database(db_name)
            
            # Test connection with a simple operation instead of ping
            self.db.list_collection_names()
            print("Successfully connected to MongoDB")
            
            # Print connection details for debugging
            print(f"Connected to database: {db_name}")
            print(f"Available collections: {', '.join(self.db.list_collection_names())}")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
            if 'mongodb+srv' in mongo_uri:
                print("Connection Details:")
                print(f"CA File: {certifi.where()}")
                print(f"MongoDB URI format: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority")
                print(f"Certifi Version: {certifi.__version__}")
                print(f"SSL Version: {ssl.OPENSSL_VERSION}")
                print(f"Connection options being used: tls=true, retryWrites=true, w=majority")
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