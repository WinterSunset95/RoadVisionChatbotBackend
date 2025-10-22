from pymongo import MongoClient
from pymongo.database import Database
from app.config import settings

class MongoClientConnection:
    def __init__(self, mongo_url: str):
        try:
            # Set a timeout to quickly fail if the DB is not available
            self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            print("✅ MongoDB connection successful.")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB at {settings.MONGODB_HOST}:{settings.MONGODB_PORT}. Please ensure it is running.")
            print(f"   Error: {e}")
            raise

    def get_database(self) -> Database:
        return self.client[settings.MONGODB_DB]

# Initialize the client, this will be run once on application startup
mongo_client = MongoClientConnection(settings.MONGODB_URL)

# FastAPI dependency to be used in endpoint functions
def get_database() -> Database:
    return mongo_client.get_database()
