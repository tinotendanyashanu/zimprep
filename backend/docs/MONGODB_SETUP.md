"""MongoDB setup documentation for ZimPrep.

This guide provides step-by-step instructions for setting up MongoDB
for local development and production deployment.
"""

# MongoDB Setup Guide

## Local Development with Docker

The easiest way to run MongoDB locally is using Docker Compose:

```bash
# Start MongoDB with the provided docker-compose.yml
docker-compose up -d mongodb

# Verify MongoDB is running
docker ps | grep mongo
```

## Manual MongoDB Setup (Without Docker)

### 1. Install MongoDB

**Windows:**
```powershell
# Download from https://www.mongodb.com/try/download/community
# Or use chocolatey
choco install mongodb
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install mongodb-org

# RHEL/CentOS
sudo yum install mongodb-org
```

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
```

### 2. Start MongoDB Service

```bash
# Linux
sudo systemctl start mongod
sudo systemctl enable mongod  # Auto-start on boot

# macOS
brew services start mongodb-community

# Windows
# MongoDB should auto-start as a service
# Or manually: net start MongoDB
```

### 3. Create ZimPrep Database and User

Connect to MongoDB:
```bash
mongosh
```

Create database and user:
```javascript
// Switch to admin database
use admin

// Create zimprep user with read/write permissions
db.createUser({
  user: "zimprep",
  pwd: "zimprep_local_password_CHANGE_IN_PRODUCTION",
  roles: [
    { role: "readWrite", db: "zimprep" },
    { role: "dbAdmin", db: "zimprep" }
  ]
})

// Switch to zimprep database
use zimprep

// Create required collections
db.createCollection("exam_results")
db.createCollection("mark_overrides")
db.createCollection("audit_events")
db.createCollection("submissions")
db.createCollection("exam_structures")

// Create indexes for performance
db.exam_results.createIndex({ trace_id: 1 }, { unique: true })
db.exam_results.createIndex({ user_id: 1 })
db.mark_overrides.createIndex({ trace_id: 1 })
db.mark_overrides.createIndex({ override_id: 1 }, { unique: true })
db.audit_events.createIndex({ trace_id: 1 })
db.audit_events.createIndex({ event_type: 1 })
db.submissions.createIndex({ trace_id: 1 }, { unique: true })
db.submissions.createIndex({ user_id: 1 })

// Verify collections
show collections

// Exit
exit
```

### 4. Update .env File

```env
# Local development
MONGODB_URI=mongodb://zimprep:zimprep_local_password_CHANGE_IN_PRODUCTION@localhost:27017/zimprep?authSource=admin

# Production (use strong password!)
MONGODB_URI=mongodb://zimprep:YOUR_SECURE_PASSWORD@your-mongo-host:27017/zimprep?authSource=admin\u0026ssl=true
```

### 5. Verify Connection

Test the connection:
```bash
cd backend
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://zimprep:zimprep_local_password_CHANGE_IN_PRODUCTION@localhost:27017/zimprep?authSource=admin'); print(client.server_info())"
```

Expected output: MongoDB version information

## Production Setup

### MongoDB Atlas (Recommended for Production)

1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster
3. Configure network access (whitelist your IP/VPC)
4. Create database user `zimprep` with strong password
5. Get connection string:
   ```
   mongodb+srv://zimprep:PASSWORD@cluster0.xxxxx.mongodb.net/zimprep?retryWrites=true\u0026w=majority
   ```

6. Update `.env`:
   ```env
   MONGODB_URI=mongodb+srv://zimprep:PASSWORD@cluster0.xxxxx.mongodb.net/zimprep?retryWrites=true\u0026w=majority
   ```

### Self-Hosted Production

For production deployments:

1. Use replica sets (minimum 3 nodes)
2. Enable authentication
3. Use SSL/TLS
4. Set up monitoring
5. Configure backups

Example connection string:
```
mongodb://zimprep:PASSWORD@mongo1:27017,mongo2:27017,mongo3:27017/zimprep?authSource=admin\u0026ssl=true\u0026replicaSet=rs0
```

## Troubleshooting

### "Authentication failed"

- Verify username/password
- Check `authSource=admin` in connection string
- Ensure user has correct permissions

### "Connection timeout"

- Check MongoDB is running: `sudo systemctl status mongod`
- Verify firewall allows port 27017
- Check network connectivity

### "Database not found"

- Create database: `use zimprep` in mongosh
- Database is created automatically on first write

### "Index creation failed"

- Ensure you're connected as admin user
- Drop existing indexes if conflicting
- Check for duplicate data

## Testing

```python
# Test script: test_mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test_connection():
    client = AsyncIOMotorClient("mongodb://zimprep:PASSWORD@localhost:27017/zimprep?authSource=admin")
    try:
        # Test connection
        await client.admin.command('ping')
        print("✓ MongoDB connection successful")
        
        # List databases
        dbs = await client.list_database_names()
        print(f"✓ Available databases: {dbs}")
        
        # Test write
        db = client.zimprep
        result = await db.test_collection.insert_one({"test": "value"})
        print(f"✓ Write test successful: {result.inserted_id}")
        
        # Cleanup
        await db.test_collection.delete_one({"_id": result.inserted_id})
        print("✓ All tests passed!")
        
    except Exception as e:
        print(f"❌ MongoDB test failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run: `python test_mongodb.py`
