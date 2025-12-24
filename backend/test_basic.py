"""Simple server test without logging complexity."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

async def test_mongo():
    """Test MongoDB connection."""
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print("✓ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

async def main():
    print("Testing basic components...")
    print(f"JWT_SECRET configured: {bool(settings.JWT_SECRET)}")
    print(f"MongoDB URI: {settings.MONGODB_URI[:30]}...")
    
    mongo_ok = await test_mongo()
    
    if mongo_ok:
        print("\n✅ All basic components OK")
    else:
        print("\n⚠️ MongoDB unavailable but server can still start")

if __name__ == "__main__":
    asyncio.run(main())
