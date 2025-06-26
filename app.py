# app.py

from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from io import BytesIO

from config import Config
from auth import AuthManager, require_auth
from file_manager import SecureFileManager
from database import DatabaseManager

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging to use Gunicorn's logger
# This ensures that your app's logs will appear in Render's log stream.
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# The following print statements will show in Render's logs during deployment
app.logger.info("🚀 Starting Heal AI Secure Storage API Server")
app.logger.info("=" * 50)

# Validate configuration
Config.validate_config()

# Initialize managers
auth_manager = AuthManager()
file_manager = SecureFileManager()
db_manager = DatabaseManager()

app.logger.info("✅ All managers initialized successfully")
app.logger.info("🌐 API Server ready to accept requests")

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
        app.logger.info(f"📝 Registration request for username: {username}")
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        result = auth_manager.register_user(username, password, email)
        if 'error' in result:
            return jsonify(result), 400
        app.logger.info(f"✅ User registered successfully: {username}")
        return jsonify(result), 201
    except Exception as e:
        app.logger.error(f"❌ Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        app.logger.info(f"🔑 Login request for username: {username}")
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        result = auth_manager.authenticate_user(username, password)
        if 'error' in result:
            app.logger.warning(f"❌ Login failed for: {username}")
            return jsonify(result), 401
        app.logger.info(f"✅ Login successful for: {username}")
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"❌ Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/upload', methods=['POST'])
@require_auth
def upload_file(user_id, username):
    """File upload endpoint"""
    try:
        app.logger.info(f"📤 Upload request from user: {username} ({user_id})")
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        result, status_code = file_manager.upload_file(file, user_id)
        if status_code == 200:
            app.logger.info(f"✅ Upload successful for user: {username}")
        else:
            app.logger.warning(f"❌ Upload failed for user: {username}")
        return jsonify(result), status_code
    except Exception as e:
        app.logger.error(f"❌ Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

# CORRECTED ROUTE: Captures the 'file_id' from the URL
@app.route('/retrieve/<string:file_id>', methods=['GET'])
@require_auth
def retrieve_file(user_id, username, file_id):
    """File retrieval endpoint"""
    try:
        app.logger.info(f"📥 Retrieve request from user: {username} for file: {file_id}")
        result, status_code = file_manager.retrieve_file(file_id, user_id)
        if status_code != 200:
            app.logger.warning(f"❌ Retrieve failed for user: {username}")
            return jsonify(result), status_code
        file_data = result['file_data']
        filename = result['filename']
        app.logger.info(f"✅ File retrieved successfully: {filename}")
        return send_file(
            BytesIO(file_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        app.logger.error(f"❌ Retrieval error: {e}")
        return jsonify({'error': 'Retrieval failed'}), 500

@app.route('/files', methods=['GET'])
@require_auth
def get_user_files(user_id, username):
    """Get user's files list"""
    try:
        app.logger.info(f"📋 File list request from user: {username}")
        result, status_code = file_manager.get_user_files_list(user_id)
        return jsonify(result), status_code
    except Exception as e:
        app.logger.error(f"❌ Get files error: {e}")
        return jsonify({'error': 'Failed to get files', 'details': str(e)}), 500

# CORRECTED ROUTE: Captures the 'file_id' from the URL
@app.route('/delete/<string:file_id>', methods=['DELETE'])
@require_auth
def delete_file(user_id, username, file_id):
    """File deletion endpoint"""
    try:
        app.logger.info(f"🗑️ Delete request from user: {username} for file: {file_id}")
        result, status_code = file_manager.delete_file(file_id, user_id)
        return jsonify(result), status_code
    except Exception as e:
        app.logger.error(f"❌ Deletion error: {e}")
        return jsonify({'error': 'Deletion failed'}), 500

@app.route('/audit', methods=['GET'])
@require_auth
def get_audit_logs(user_id, username):
    """Get user's audit logs"""
    try:
        app.logger.info(f"🔍 Audit logs request from user: {username}")
        logs = db_manager.get_audit_logs(user_id)
        for log in logs:
            if log.get('timestamp'):
                log['timestamp'] = log['timestamp'].isoformat()
            if '_id' in log:
                log['_id'] = str(log['_id'])
        return jsonify({'logs': logs})
    except Exception as e:
        app.logger.error(f"❌ Audit logs error: {e}")
        return jsonify({'error': 'Failed to get audit logs'}), 500

# The `if __name__ == '__main__':` block is removed.
# Gunicorn will be used as the production WSGI server to run the 'app' object.
