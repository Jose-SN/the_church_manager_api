from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Global MongoDB client instance
client = None

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client[settings.DATABASE_NAME]
        print(f"Connected to MongoDB at {settings.MONGODB_URI}")

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

# Create a global instance
mongodb = MongoDB()

# Database connection events
async def connect_to_mongo():
    """Initialize MongoDB connection."""
    await mongodb.connect()

async def close_mongo_connection():
    """Close MongoDB connection."""
    await mongodb.close()

# Get database instance
def get_database():
    """Get the MongoDB database instance."""
    return mongodb.db

# Get collection
def get_collection(collection_name: str):
    """Get a MongoDB collection."""
    return mongodb.db[collection_name]