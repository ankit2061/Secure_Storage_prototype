import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import Config
from database import DatabaseManager

class AuthManager:
    def __init__(self):
        self.secret_key = Config.SECRET_KEY
        self.db = DatabaseManager()
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def generate_token(self, user_id, username):
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=Config.TOKEN_EXPIRY_HOURS),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    def register_user(self, username, password, email=None):
        """Register new user"""
        try:
            # Check if user exists
            if self.db.get_user_by_username(username):
                return {'error': 'Username already exists'}
            
            # Hash password and create user
            password_hash = self.hash_password(password)
            user_id = self.db.create_user(username, password_hash, email)
            
            if user_id:
                return {'success': True, 'user_id': user_id}
            else:
                return {'error': 'Failed to create user'}
        except Exception as e:
            return {'error': f'Registration failed: {str(e)}'}
    
    def authenticate_user(self, username, password):
        """Authenticate user"""
        try:
            user = self.db.get_user_by_username(username)
            if not user:
                return {'error': 'Invalid credentials'}
            
            if self.verify_password(password, user['password_hash']):
                token = self.generate_token(str(user['_id']), username)
                
                # Log successful login
                self.db.log_activity(
                    str(user['_id']), 
                    'login', 
                    ip_address=request.remote_addr if request else None
                )
                
                return {
                    'success': True,
                    'token': token,
                    'user_id': str(user['_id']),
                    'username': username
                }
            else:
                return {'error': 'Invalid credentials'}
        except Exception as e:
            return {'error': f'Authentication failed: {str(e)}'}

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]  # Remove 'Bearer ' prefix
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        auth_manager = AuthManager()
        payload = auth_manager.verify_token(token)
        
        if 'error' in payload:
            return jsonify(payload), 401
        
        kwargs['user_id'] = payload['user_id']
        kwargs['username'] = payload['username']
        return f(*args, **kwargs)
    
    return decorated_function
