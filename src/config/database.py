from pymongo import MongoClient
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
            
            # Connect to MongoDB with SSL configuration
            if 'mongodb+srv' in mongo_uri:
                # Atlas connection with SSL
                self.client = MongoClient(
                    mongo_uri,
                    tls=True,
                    tlsCAFile=certifi.where(),
                    retryWrites=True,
                    w='majority'
                )
            else:
                # Local connection
                self.client = MongoClient(mongo_uri)
            
            # Get database name from URI or use default
            db_name = os.getenv('MONGODB_NAME', 'ubereats')
            self.db = self.client.get_database(db_name)
            
            # Test connection
            self.client.server_info()
            print("Successfully connected to MongoDB")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
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