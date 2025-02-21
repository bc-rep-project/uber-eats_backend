from pymongo import MongoClient, ASCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import certifi
from .indexes import setup_indexes

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

            # Create indexes
            self._create_indexes()
            print("Database indexes created successfully")
            
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
                print("4. TLS/SSL is enabled in your MongoDB Atlas cluster")
                print("5. Your connection string includes all required parameters")
            raise e

    def _create_indexes(self):
        """Create required database indexes"""
        try:
            # Set up all indexes using the indexes module
            setup_indexes(self.db)
        except Exception as e:
            print(f"Error creating indexes: {str(e)}")
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

def init_db():
    """Initialize database connection and setup"""
    try:
        print("Initializing database connection...")
        db.connect()
        return True
    except Exception as e:
        print(f"Failed to initialize database: {str(e)}")
        return False 