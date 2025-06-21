from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'rdp_stealth')
db = client[db_name]

# Collections
users_collection = db.users
sessions_collection = db.sessions
system_metrics_collection = db.system_metrics
file_operations_collection = db.file_operations
logs_collection = db.logs
rdp_connections_collection = db.rdp_connections
settings_collection = db.settings

class DatabaseManager:
    def __init__(self):
        self.client = client
        self.db = db
    
    async def init_database(self):
        """Initialize database with indexes and default data"""
        try:
            # Create indexes for better performance
            await self.create_indexes()
            
            # Create default settings if not exist
            await self.create_default_settings()
            
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    async def create_indexes(self):
        """Create database indexes"""
        # Users indexes
        await users_collection.create_index("username", unique=True)
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("id", unique=True)
        
        # Sessions indexes
        await sessions_collection.create_index("user_id")
        await sessions_collection.create_index("ip_address")
        await sessions_collection.create_index("start_time")
        await sessions_collection.create_index("status")
        
        # System metrics indexes
        await system_metrics_collection.create_index("timestamp")
        
        # File operations indexes
        await file_operations_collection.create_index("user_id")
        await file_operations_collection.create_index("timestamp")
        await file_operations_collection.create_index("operation_type")
        
        # Logs indexes
        await logs_collection.create_index("timestamp")
        await logs_collection.create_index("level")
        await logs_collection.create_index("source")
        await logs_collection.create_index("user_id")
        
        # RDP connections indexes
        await rdp_connections_collection.create_index("user_id")
        await rdp_connections_collection.create_index("status")
        
        print("Database indexes created successfully")
    
    async def create_default_settings(self):
        """Create default application settings"""
        from models import AppSettings, SecuritySettings, NotificationSettings
        
        existing_settings = await settings_collection.find_one({})
        if not existing_settings:
            default_settings = AppSettings(
                notifications=NotificationSettings(
                    notification_email="admin@example.com"
                ),
                updated_by="system"
            )
            
            await settings_collection.insert_one(default_settings.dict())
            print("Default settings created")
    
    async def cleanup_old_data(self):
        """Clean up old data based on retention policies"""
        try:
            # Get settings for retention policies
            settings = await settings_collection.find_one({})
            if not settings:
                return
            
            retention_days = settings.get('system', {}).get('log_retention_days', 30)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Clean old logs
            result = await logs_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            if result.deleted_count > 0:
                print(f"Cleaned up {result.deleted_count} old log entries")
            
            # Clean old system metrics (keep last 7 days)
            metrics_cutoff = datetime.utcnow() - timedelta(days=7)
            result = await system_metrics_collection.delete_many({
                "timestamp": {"$lt": metrics_cutoff}
            })
            
            if result.deleted_count > 0:
                print(f"Cleaned up {result.deleted_count} old metric entries")
            
            # Clean old inactive sessions (keep last 30 days)
            session_cutoff = datetime.utcnow() - timedelta(days=30)
            result = await sessions_collection.delete_many({
                "status": {"$ne": "active"},
                "end_time": {"$lt": session_cutoff}
            })
            
            if result.deleted_count > 0:
                print(f"Cleaned up {result.deleted_count} old session entries")
                
        except Exception as e:
            print(f"Error during data cleanup: {e}")
    
    async def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = {}
            
            # Collection counts
            stats['users_count'] = await users_collection.count_documents({})
            stats['active_sessions_count'] = await sessions_collection.count_documents({"status": "active"})
            stats['total_sessions_count'] = await sessions_collection.count_documents({})
            stats['logs_count'] = await logs_collection.count_documents({})
            stats['rdp_connections_count'] = await rdp_connections_collection.count_documents({})
            
            # Database size (approximate)
            db_stats = await self.db.command("dbStats")
            stats['database_size_mb'] = round(db_stats.get('dataSize', 0) / (1024 * 1024), 2)
            stats['storage_size_mb'] = round(db_stats.get('storageSize', 0) / (1024 * 1024), 2)
            
            return stats
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}

# Create database manager instance
db_manager = DatabaseManager()

# Database connection events
async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        # Test connection
        await client.admin.command('ping')
        print("Successfully connected to MongoDB")
        
        # Initialize database
        await db_manager.init_database()
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    try:
        client.close()
        print("MongoDB connection closed")
    except Exception as e:
        print(f"Error closing MongoDB connection: {e}")

# Direct access to collections for convenience
class DB:
    users = users_collection
    sessions = sessions_collection
    system_metrics = system_metrics_collection
    file_operations = file_operations_collection
    logs = logs_collection
    rdp_connections = rdp_connections_collection
    settings = settings_collection

# Create db instance
db = DB()