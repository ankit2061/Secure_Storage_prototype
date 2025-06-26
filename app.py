from datetime import datetime  # Add this line
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from io import BytesIO
from config import Config
from auth import AuthManager, require_auth
from file_manager import SecureFileManager
from database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)
CORS(app)

print("🚀 Starting Heal AI Secure Storage API Server")
print("=" * 50)

# Validate configuration
Config.validate_config()

# Initialize managers
auth_manager = AuthManager()
file_manager = SecureFileManager()
db_manager = DatabaseManager()

print("✅ All managers initialized successfully")
print("🌐 API Server ready to accept requests")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'heal-ai-secure-storage',
        'version': '1.0.0',
        'timestamp': str(datetime.now())
    })

@app.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        print(f"📝 Registration request for username: {username}")
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        result = auth_manager.register_user(username, password, email)
        
        if 'error' in result:
            return jsonify(result), 400
        
        print(f"✅ User registered successfully: {username}")
        return jsonify(result), 201
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    """User login endpoint (flowchart: User logs in)"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        print(f"🔑 Login request for username: {username}")
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        result = auth_manager.authenticate_user(username, password)
        
        if 'error' in result:
            print(f"❌ Login failed for: {username}")
            return jsonify(result), 401
        
        print(f"✅ Login successful for: {username}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/upload', methods=['POST'])
@require_auth
def upload_file(user_id, username):
    """File upload endpoint (flowchart: Upload file workflow)"""
    try:
        print(f"📤 Upload request from user: {username} ({user_id})")
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        result, status_code = file_manager.upload_file(file, user_id)
        
        if status_code == 200:
            print(f"✅ Upload successful for user: {username}")
        else:
            print(f"❌ Upload failed for user: {username}")
        
        return jsonify(result), status_code
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/retrieve/<file_id>', methods=['GET'])
@require_auth
def retrieve_file(file_id, user_id, username):
    """File retrieval endpoint (flowchart: Retrieve file workflow)"""
    try:
        print(f"📥 Retrieve request from user: {username} for file: {file_id}")
        
        result, status_code = file_manager.retrieve_file(file_id, user_id)
        
        if status_code != 200:
            print(f"❌ Retrieve failed for user: {username}")
            return jsonify(result), status_code
        
        # Return file as download
        file_data = result['file_data']
        filename = result['filename']
        
        print(f"✅ File retrieved successfully: {filename}")
        return send_file(
            BytesIO(file_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return jsonify({'error': 'Retrieval failed'}), 500

# 
@app.route('/files', methods=['GET'])
@require_auth
def get_user_files(user_id, username):
    """Get user's files list (maintains user isolation)"""
    try:
        print(f"📋 File list request from user: {username}")
        
        result = file_manager.get_user_files_list(user_id)
        
        # Check if result is a tuple (result, status_code)
        if isinstance(result, tuple):
            result_data, status_code = result
        else:
            result_data = result
            status_code = 200
        
        # Ensure we return proper JSON response
        if status_code == 200:
            return jsonify(result_data), 200
        else:
            return jsonify(result_data), status_code
        
    except Exception as e:
        print(f"❌ Get files error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get files', 'details': str(e)}), 500


@app.route('/delete/<file_id>', methods=['DELETE'])
@require_auth
def delete_file(file_id, user_id, username):
    """File deletion endpoint"""
    try:
        print(f"🗑️ Delete request from user: {username} for file: {file_id}")
        
        result, status_code = file_manager.delete_file(file_id, user_id)
        return jsonify(result), status_code
        
    except Exception as e:
        print(f"❌ Deletion error: {e}")
        return jsonify({'error': 'Deletion failed'}), 500

@app.route('/audit', methods=['GET'])
@require_auth
def get_audit_logs(user_id, username):
    """Get user's audit logs"""
    try:
        print(f"🔍 Audit logs request from user: {username}")
        
        logs = db_manager.get_audit_logs(user_id)
        
        # Convert datetime objects to strings for JSON serialization
        for log in logs:
            if hasattr(log, 'get'):
                if log.get('timestamp') and hasattr(log['timestamp'], 'isoformat'):
                    log['timestamp'] = log['timestamp'].isoformat()
                if '_id' in log:
                    log['_id'] = str(log['_id'])
        
        return jsonify({'logs': logs})
        
    except Exception as e:
        print(f"❌ Audit logs error: {e}")
        return jsonify({'error': 'Failed to get audit logs'}), 500

if __name__ == '__main__':
    print("\n🎯 Starting Flask API server...")
    print("📡 API will be available at: http://localhost:5002")
    print("🔗 Health check: http://localhost:5002/health")
    print("📖 Available endpoints:")
    print("   POST /register - User registration")
    print("   POST /login - User authentication")
    print("   POST /upload - File upload")
    print("   GET /retrieve/<file_id> - File download")
    print("   GET /files - List user files")
    print("   DELETE /delete/<file_id> - Delete file")
    print("   GET /audit - Get audit logs")
    print("\n🚀 Server starting...")
    
    app.run(debug=True, host='0.0.0.0', port=5002)
