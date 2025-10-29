from pymongo import MongoClient
from pymongo.database import Database
from app.config import settings

class MongoClientConnection:
    def __init__(self):
        self.client = None

    def connect(self):
        try:
            self.client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=5000, uuidRepresentation="standard")
            self.client.admin.command('ismaster')
            print("✅ MongoDB connection successful.")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB at {settings.MONGO_HOST}:{settings.MONGO_PORT}. Please ensure it is running.")
            print(f"   Error: {e}")
            raise
    
    def get_database(self) -> Database:
        if not self.client:
            raise Exception("MongoDB client not connected. Call connect() first.")
        return self.client[settings.MONGO_DB]

# Declare the client, to be initialized on application startup
mongo_client = MongoClientConnection()

# FastAPI dependency to be used in endpoint functions
def get_database() -> Database:
    return mongo_client.get_database()
