from pymongo import MongoClient
from datetime import datetime
import logging
from config import Config

class DatabaseManager:
    def __init__(self):
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.DATABASE_NAME]
            self.users = self.db.users
            self.files = self.db.files
            self.audit_logs = self.db.audit_logs
            self.sessions = self.db.sessions
            
            # Test connection
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB successfully")
            
            # Create indexes for better performance
            self._create_indexes()
        except Exception as e:
            print(f"⚠️ MongoDB connection failed, using in-memory storage: {e}")
            # Fallback to in-memory storage
            self._init_memory_storage()
    
    def _init_memory_storage(self):
        """Initialize in-memory storage as fallback"""
        self.memory_users = {}
        self.memory_files = {}
        self.memory_audit_logs = []
        self.memory_sessions = {}
        self.use_memory = True
    
    def _create_indexes(self):
        """Create database indexes"""
        try:
            self.users.create_index("username", unique=True)
            self.files.create_index([("user_id", 1), ("file_id", 1)])
            self.audit_logs.create_index([("user_id", 1), ("timestamp", -1)])
            self.sessions.create_index("user_id")
            print("✅ Database indexes created")
        except Exception as e:
            logging.error(f"Error creating indexes: {e}")
    
    def create_user(self, username, password_hash, email=None):
        """Create a new user"""
        try:
            if hasattr(self, 'use_memory'):
                user_id = f"user_{len(self.memory_users) + 1}"
                self.memory_users[user_id] = {
                    'username': username,
                    'password_hash': password_hash,
                    'email': email,
                    'created_at': datetime.utcnow(),
                    'is_active': True,
                    'role': 'user'
                }
                return user_id
            else:
                user_data = {
                    'username': username,
                    'password_hash': password_hash,
                    'email': email,
                    'created_at': datetime.utcnow(),
                    'is_active': True,
                    'role': 'user'
                }
                result = self.users.insert_one(user_data)
                return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return None
    
    def get_user_by_username(self, username):
        """Get user by username"""
        try:
            if hasattr(self, 'use_memory'):
                for user_id, user_data in self.memory_users.items():
                    if user_data['username'] == username and user_data['is_active']:
                        return {**user_data, '_id': user_id}
                return None
            else:
                return self.users.find_one({'username': username, 'is_active': True})
        except Exception as e:
            logging.error(f"Error getting user: {e}")
            return None
    
    def store_file_metadata(self, file_id, user_id, filename, file_size, file_type, mega_file_id):
        """Store file metadata"""
        try:
            file_data = {
                'file_id': file_id,
                'user_id': user_id,
                'filename': filename,
                'file_size': file_size,
                'file_type': file_type,
                'mega_file_id': mega_file_id,
                'upload_time': datetime.utcnow(),
                'is_active': True,
                'access_count': 0,
                'tags': []
            }
            
            if hasattr(self, 'use_memory'):
                self.memory_files[file_id] = file_data
            else:
                self.files.insert_one(file_data)
            
            print(f"✅ Stored metadata for file: {filename}")
            return True
        except Exception as e:
            logging.error(f"Error storing file metadata: {e}")
            return False
    
    def get_file_metadata(self, file_id):
        """Get file metadata"""
        try:
            if hasattr(self, 'use_memory'):
                return self.memory_files.get(file_id)
            else:
                return self.files.find_one({'file_id': file_id, 'is_active': True})
        except Exception as e:
            logging.error(f"Error getting file metadata: {e}")
            return None
    
    def get_user_files(self, user_id, limit=50):
        """Get all files for a user"""
        try:
            if hasattr(self, 'use_memory'):
                user_files = []
                for file_id, file_data in self.memory_files.items():
                    if file_data.get('user_id') == user_id and file_data.get('is_active', True):
                        user_files.append(file_data)
                # Sort by upload time (most recent first)
                user_files.sort(key=lambda x: x.get('upload_time', datetime.min), reverse=True)
                return user_files[:limit]
            else:
                return list(self.files.find(
                    {'user_id': user_id, 'is_active': True}
                ).sort('upload_time', -1).limit(limit))
        except Exception as e:
            print(f"❌ Error getting user files: {e}")
            return []

    def log_activity(self, user_id, action, file_id=None, ip_address=None, details=None):
        """Log user activity"""
        try:
            log_entry = {
                'user_id': user_id,
                'action': action,
                'file_id': file_id,
                'ip_address': ip_address,
                'details': details,
                'timestamp': datetime.utcnow()
            }
            
            if hasattr(self, 'use_memory'):
                self.memory_audit_logs.append(log_entry)
            else:
                self.audit_logs.insert_one(log_entry)
            
            print(f"📝 Logged activity: {action} by user {user_id}")
        except Exception as e:
            logging.error(f"Error logging activity: {e}")
    
    def update_file_access_count(self, file_id):
        """Update file access count"""
        try:
            if hasattr(self, 'use_memory'):
                if file_id in self.memory_files:
                    self.memory_files[file_id]['access_count'] += 1
            else:
                self.files.update_one(
                    {'file_id': file_id},
                    {'$inc': {'access_count': 1}}
                )
        except Exception as e:
            logging.error(f"Error updating access count: {e}")
    
    def get_audit_logs(self, user_id, limit=50):
        """Get audit logs for user"""
        try:
            if hasattr(self, 'use_memory'):
                user_logs = [log for log in self.memory_audit_logs if log['user_id'] == user_id]
                return sorted(user_logs, key=lambda x: x['timestamp'], reverse=True)[:limit]
            else:
                return list(self.audit_logs.find(
                    {'user_id': user_id}
                ).sort('timestamp', -1).limit(limit))
        except Exception as e:
            logging.error(f"Error getting audit logs: {e}")
            return []