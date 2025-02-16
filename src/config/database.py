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
            
            # Print debug information
            print("Attempting to connect to MongoDB...")
            print(f"Using certifi version: {certifi.__version__}")
            print(f"CA file path: {certifi.where()}")
            
            # Connect to MongoDB
            if 'mongodb+srv' in mongo_uri:
                # Atlas connection with explicit SSL configuration
                self.client = MongoClient(
                    mongo_uri,
                    server_api=ServerApi('1'),
                    tls=True,
                    tlsCAFile=certifi.where(),
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                    retryWrites=True,
                    w='majority',
                    ssl_cert_reqs=ssl.CERT_REQUIRED,
                    connect=True,
                    minPoolSize=0
                )
            else:
                # Local connection
                self.client = MongoClient(mongo_uri)
            
            # Get database name from URI or use default
            db_name = os.getenv('MONGODB_NAME', 'ubereats')
            self.db = self.client.get_database(db_name)
            
            # Test connection with a simple operation
            self.db.list_collection_names()
            print("Successfully connected to MongoDB")
            print(f"Connected to database: {db_name}")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
            if 'mongodb+srv' in mongo_uri:
                print("\nConnection Details:")
                print(f"MongoDB URI format: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>")
                print("Required connection options:")
                print("- retryWrites=true")
                print("- w=majority")
                print("\nPlease check:")
                print("1. MongoDB Atlas connection string is correct")
                print("2. Network access is configured for your IP")
                print("3. Database user has correct permissions")
                print("4. SSL/TLS configuration is properly set")
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