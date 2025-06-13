import os
import json
import uuid
import logging
from datetime import datetime
from cryptography.fernet import Fernet
from pathlib import Path

class MegaWrapper:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.folders = {}  # Store folder structure
        self.files = {}    # Store file metadata
        self.user_folders = {}  # Track user-specific folders
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Create local storage directory
        self.storage_path = Path("./mega_storage")
        self.storage_path.mkdir(exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        
    def login(self, email, password):
        """Login simulation following flowchart 'User logs in' step"""
        logging.info(f"✅ User logged in: {email}")
        return self
    
    def get_user(self):
        """Get user information"""
        return {
            "email": self.email,
            "storage_used": f"{len(self.files) * 0.5:.1f} MB",
            "storage_quota": "50 GB",
            "folders": len(self.folders),
            "files": len(self.files)
        }
    
    def create_user_folder(self, user_id):
        """Create user-specific folder following flowchart logic"""
        folder_name = f"heal_ai_user_{user_id}"
        
        # Check if user folder already exists
        for folder_id, folder_info in self.folders.items():
            if folder_info['name'] == folder_name:
                logging.info(f"✅ User folder already exists: {folder_name}")
                return folder_id
        
        # Create new user-specific folder
        folder_id = f"folder_{uuid.uuid4()}"
        folder_path = self.storage_path / folder_name
        folder_path.mkdir(exist_ok=True)
        
        self.folders[folder_id] = {
            'name': folder_name,
            'path': str(folder_path),
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'files': []
        }
        
        self.user_folders[user_id] = folder_id
        logging.info(f"✅ Created user-specific folder: {folder_name} (ID: {folder_id})")
        return folder_id
    
    def create_folder(self, folder_name, user_id=None):
        """Create folder - implements 'Store in user-specific folder' from flowchart"""
        if user_id:
            return self.create_user_folder(user_id)
        
        folder_id = f"folder_{uuid.uuid4()}"
        folder_path = self.storage_path / folder_name
        folder_path.mkdir(exist_ok=True)
        
        self.folders[folder_id] = {
            'name': folder_name,
            'path': str(folder_path),
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'files': []
        }
        
        logging.info(f"✅ Created folder: {folder_name} (ID: {folder_id})")
        return folder_id
    
    def tag_file_with_user_id(self, file_data, user_id, filename):
        """Tag file with user ID - implements 'Tag file with user ID' from flowchart"""
        file_metadata = {
            'user_id': user_id,
            'filename': filename,
            'upload_time': datetime.now().isoformat(),
            'size': len(file_data),
            'encrypted': True
        }
        
        # Encrypt file data
        encrypted_data = self.cipher.encrypt(file_data)
        
        return encrypted_data, file_metadata

    def upload(self, file_input, dest=None, dest_filename=None):
        """Upload file following complete flowchart workflow"""
        try:
            print(f"🔄 MEGA wrapper upload started")
            
            # Handle different file input types
            if hasattr(file_input, 'read'):
                # File-like object (Streamlit uploaded file)
                file_input.seek(0)  # Ensure we start from beginning
                file_data = file_input.read()
                filename = dest_filename or getattr(file_input, 'name', 'uploaded_file')
                print(f"📄 Read file-like object: {len(file_data)} bytes")
            elif isinstance(file_input, str):
                # File path
                with open(file_input, 'rb') as f:
                    file_data = f.read()
                filename = dest_filename or os.path.basename(file_input)
                print(f"📄 Read file from path: {len(file_data)} bytes")
            else:
                # Raw bytes
                file_data = file_input
                filename = dest_filename or 'uploaded_file'
                print(f"📄 Using raw bytes: {len(file_data)} bytes")
            
            if len(file_data) == 0:
                raise Exception("File data is empty")
            
            # Generate unique file ID
            file_id = f"file_{uuid.uuid4()}"
            
            # Get user ID from destination folder
            user_id = None
            if dest and dest in self.folders:
                user_id = self.folders[dest].get('user_id')
            
            # Tag file with user ID and encrypt
            encrypted_data, file_metadata = self.tag_file_with_user_id(file_data, user_id, filename)
            
            # Store file in user-specific folder
            if dest:
                folder_info = self.folders.get(dest)
                if folder_info:
                    file_path = Path(folder_info['path']) / f"{file_id}_{filename}"
                    folder_info['files'].append(file_id)
                else:
                    file_path = self.storage_path / f"{file_id}_{filename}"
            else:
                file_path = self.storage_path / f"{file_id}_{filename}"
            
            # Write encrypted file to storage
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Store file metadata
            self.files[file_id] = {
                **file_metadata,
                'file_id': file_id,
                'folder_id': dest,
                'file_path': str(file_path),
                'access_count': 0
            }
            
            print(f"✅ MEGA upload completed: {filename} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            print(f"❌ MEGA upload failed: {e}")
            import traceback
            traceback.print_exc()
            raise e

    
    def check_file_in_user_folder(self, file_id, requesting_user_id):
        """Check if file is in user's folder - implements flowchart decision logic"""
        if file_id not in self.files:
            return False
        
        file_info = self.files[file_id]
        file_user_id = file_info.get('user_id')
        
        # Check if file belongs to requesting user
        if file_user_id == requesting_user_id:
            logging.info(f"✅ Access granted: File {file_id} belongs to user {requesting_user_id}")
            return True
        else:
            logging.warning(f"❌ Access denied: File {file_id} does not belong to user {requesting_user_id}")
            return False
    
    def download(self, file_id, dest_path=None, requesting_user_id=None):
        """Download file with access control - implements 'Retrieve file' flowchart logic"""
        if file_id not in self.files:
            raise Exception(f"File {file_id} not found")
        
        # Check if file is in user's folder (flowchart decision)
        if requesting_user_id and not self.check_file_in_user_folder(file_id, requesting_user_id):
            raise Exception("Access denied - File not in user's folder")
        
        # Allow access (flowchart step)
        file_info = self.files[file_id]
        
        # Read encrypted file
        with open(file_info['file_path'], 'rb') as f:
            encrypted_data = f.read()
        
        # Decrypt file data
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
        except Exception as e:
            logging.error(f"❌ Decryption failed for file {file_id}: {e}")
            raise Exception("File decryption failed")
        
        # Update access count
        self.files[file_id]['access_count'] += 1
        self.files[file_id]['last_accessed'] = datetime.now().isoformat()
        
        # Save to destination if specified
        if dest_path:
            with open(dest_path, 'wb') as f:
                f.write(decrypted_data)
            logging.info(f"✅ Downloaded file to: {dest_path}")
        
        logging.info(f"✅ File {file_id} accessed by user {requesting_user_id}")
        return decrypted_data
    
    def delete(self, item_id):
        """Delete file or folder"""
        if item_id in self.files:
            file_info = self.files[item_id]
            # Delete physical file
            if os.path.exists(file_info['file_path']):
                os.remove(file_info['file_path'])
            # Remove from metadata
            del self.files[item_id]
            logging.info(f"✅ Deleted file: {item_id}")
            
        elif item_id in self.folders:
            folder_info = self.folders[item_id]
            # Delete all files in folder first
            for file_id in folder_info.get('files', []):
                if file_id in self.files:
                    self.delete(file_id)
            # Delete folder
            if os.path.exists(folder_info['path']):
                os.rmdir(folder_info['path'])
            del self.folders[item_id]
            logging.info(f"✅ Deleted folder: {item_id}")
            
        return True
    
    def get_files(self):
        """Get all files and folders - simulate MEGA API response"""
        result = {}
        
        # Add folders
        for folder_id, folder_info in self.folders.items():
            result[folder_id] = {
                'a': {'n': folder_info['name']},
                't': 1,  # 1 = folder
                'p': None,  # parent folder
                'user_id': folder_info.get('user_id')
            }
        
        # Add files
        for file_id, file_info in self.files.items():
            result[file_id] = {
                'a': {'n': file_info['filename']},
                't': 0,  # 0 = file
                'p': file_info.get('folder_id'),  # parent folder
                's': file_info['size'],
                'user_id': file_info.get('user_id'),
                'access_count': file_info.get('access_count', 0)
            }
        
        return result
    
    def get_user_files(self, user_id):
        """Get files belonging to specific user"""
        user_files = []
        for file_id, file_info in self.files.items():
            if file_info.get('user_id') == user_id:
                user_files.append({
                    'file_id': file_id,
                    'filename': file_info['filename'],
                    'size': file_info['size'],
                    'upload_time': file_info['upload_time'],
                    'access_count': file_info.get('access_count', 0)
                })
        return user_files

class Mega:
    """Main Mega class to match original API"""
    def __init__(self):
        pass
    
    def login(self, email, password):
        """Return MegaWrapper instance"""
        return MegaWrapper(email, password)