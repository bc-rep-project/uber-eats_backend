from pymongo import MongoClient, ASCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import certifi

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
            
            # Connect to MongoDB
            if 'mongodb+srv' in mongo_uri:
                # Atlas connection
                self.client = MongoClient(
                    mongo_uri,
                    server_api=ServerApi('1'),
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
            
            # Test connection with a simple operation
            self.db.list_collection_names()
            print("Successfully connected to MongoDB")
            print(f"Connected to database: {db_name}")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
            if 'mongodb+srv' in mongo_uri:
                print("Connection Details:")
                print(f"MongoDB URI format: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/dbname")
                print("Please ensure your MongoDB Atlas connection string is correct and includes all necessary parameters")
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