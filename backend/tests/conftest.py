import os

# Ensure required settings are present during pytest collection.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "zimprep_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
