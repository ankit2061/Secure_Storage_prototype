from mega_wrapper import Mega
import uuid
import logging
from datetime import datetime
from config import Config
from database import DatabaseManager

class SecureFileManager:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.mega = Mega()
        self.m = self.mega.login(self.config.MEGA_EMAIL, self.config.MEGA_PASSWORD)
        print("🔐 Secure File Manager initialized")

    def validate_file(self, file):
        """Validate uploaded file following security best practices"""
        if not file:
            return {'error': 'No file provided'}

        # Check if file has a filename
        if not hasattr(file, 'filename') or not file.filename:
            return {'error': 'No file selected'}

        if file.filename == '':
            return {'error': 'No file selected'}

        # Check file extension
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in self.config.ALLOWED_EXTENSIONS:
            return {'error': f'File type not allowed. Allowed: {", ".join(self.config.ALLOWED_EXTENSIONS)}'}

        # Check file size by reading the content
        try:
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning

            if file_size == 0:
                return {'error': 'File is empty'}

            max_size = self.config.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size:
                return {'error': f'File too large. Maximum size: {self.config.MAX_FILE_SIZE_MB}MB'}
        except Exception as e:
            return {'error': f'Could not read file: {str(e)}'}

        print(f"✅ File validation passed: {file.filename} ({file_size} bytes)")
        return {'valid': True, 'size': file_size, 'extension': file_ext}


    def upload_file(self, file, user_id):
        """Complete upload workflow following flowchart"""
        try:
            print(f"📤 Starting upload workflow for user: {user_id}")
            print(f"📄 File details: {file.filename if hasattr(file, 'filename') else 'No filename'}")

            # Step 1: Validate file
            validation = self.validate_file(file)
            if 'error' in validation:
                print(f"❌ Validation failed: {validation['error']}")
                return validation, 400

            # Step 2: Generate unique file ID
            file_id = str(uuid.uuid4())
            print(f"🆔 Generated file ID: {file_id}")

            # Step 3: Create/get user-specific folder
            user_folder = self.m.create_user_folder(user_id)
            print(f"📁 User folder: {user_folder}")

            # Step 4: Read file content before upload
            file.seek(0)  # Ensure we're at the beginning
            file_content = file.read()
            print(f"📊 Read {len(file_content)} bytes from file")

            # Reset file pointer for MEGA upload
            file.seek(0)

            # Step 5: Upload to MEGA
            mega_file_id = self.m.upload(file, dest=user_folder, dest_filename=f"{file_id}_{file.filename}")
            print(f"☁️ Uploaded to MEGA: {mega_file_id}")

            # Step 6: Store metadata in database
            success = self.db.store_file_metadata(
                file_id=file_id,
                user_id=user_id,
                filename=file.filename,
                file_size=validation['size'],
                file_type=validation['extension'],
                mega_file_id=mega_file_id
            )

            if success:
                # Log upload activity
                self.db.log_activity(
                    user_id,
                    'file_upload',
                    file_id=file_id,
                    details={'filename': file.filename, 'size': validation['size']}
                )

                print(f"✅ Upload completed successfully: {file.filename}")
                return {
                    'success': True,
                    'file_id': file_id,
                    'filename': file.filename,
                    'message': 'File uploaded successfully to user-specific folder'
                }, 200
            else:
                print("❌ Failed to store file metadata")
                return {'error': 'Failed to store file metadata'}, 500

        except Exception as e:
            print(f"❌ Upload failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Upload failed: {str(e)}'}, 500


    def retrieve_file(self, file_id, user_id):
        """Complete retrieve workflow following flowchart"""
        try:
            print(f"📥 Starting retrieve workflow for file: {file_id}, user: {user_id}")

            # Step 1: Get file metadata
            file_info = self.db.get_file_metadata(file_id)
            if not file_info:
                print(f"❌ File not found: {file_id}")
                return {'error': 'File not found'}, 404

            # Step 2: Check if file is in user's folder (flowchart decision)
            if not self.m.check_file_in_user_folder(file_info['mega_file_id'], user_id):
                # Deny access (flowchart path)
                print(f"🚫 Access denied for user {user_id} to file {file_id}")
                self.db.log_activity(
                    user_id,
                    'unauthorized_access_attempt',
                    file_id=file_id
                )
                return {'error': 'Access denied - File not in user folder'}, 403

            # Step 3: Allow access (flowchart path)
            print(f"✅ Access granted for user {user_id} to file {file_id}")
            file_data = self.m.download(file_info['mega_file_id'], requesting_user_id=user_id)

            # Update access tracking
            self.db.update_file_access_count(file_id)
            self.db.log_activity(
                user_id,
                'file_download',
                file_id=file_id,
                details={'filename': file_info['filename']}
            )

            print(f"📁 File retrieved successfully: {file_info['filename']}")
            return {
                'success': True,
                'file_data': file_data,
                'filename': file_info['filename'],
                'file_type': file_info['file_type']
            }

        except Exception as e:
            print(f"❌ Retrieval failed: {e}")
            return {'error': f'Retrieval failed: {str(e)}'}, 500

    def delete_file(self, file_id, user_id):
        """Delete file with access control"""
        try:
            print(f"🗑️ Delete request for file: {file_id}, user: {user_id}")

            # Get file metadata
            file_info = self.db.get_file_metadata(file_id)
            if not file_info:
                return {'error': 'File not found'}, 404

            # Check access permissions
            if file_info['user_id'] != user_id:
                print(f"🚫 Delete access denied for user {user_id}")
                return {'error': 'Access denied'}, 403

            # Delete from MEGA
            self.m.delete(file_info['mega_file_id'])

            # Mark as deleted in database (soft delete)
            if hasattr(self.db, 'use_memory'):
                self.db.memory_files[file_id]['is_active'] = False
            else:
                self.db.files.update_one(
                    {'file_id': file_id},
                    {'$set': {'is_active': False, 'deleted_at': datetime.utcnow()}}
                )

            # Log deletion
            self.db.log_activity(
                user_id,
                'file_delete',
                file_id=file_id,
                details={'filename': file_info['filename']}
            )

            print(f"✅ File deleted successfully: {file_info['filename']}")
            return {'success': True, 'message': 'File deleted successfully'}

        except Exception as e:
            print(f"❌ Deletion failed: {e}")
            return {'error': f'Deletion failed: {str(e)}'}, 500

    def get_user_files_list(self, user_id):
        """Get list of user's files (maintains user isolation)"""
        try:
            print(f"📋 Getting file list for user: {user_id}")
            
            # Get files from database
            files = self.db.get_user_files(user_id)
            file_list = []
            
            for file_info in files:
                try:
                    # Safely handle datetime conversion
                    upload_time = file_info.get('upload_time')
                    if upload_time:
                        if hasattr(upload_time, 'isoformat'):
                            upload_time_str = upload_time.isoformat()
                        else:
                            upload_time_str = str(upload_time)
                    else:
                        upload_time_str = datetime.now().isoformat()
                    
                    file_list.append({
                        'file_id': file_info.get('file_id', ''),
                        'filename': file_info.get('filename', 'Unknown'),
                        'file_size': file_info.get('file_size', 0),
                        'file_type': file_info.get('file_type', 'unknown'),
                        'upload_time': upload_time_str,
                        'access_count': file_info.get('access_count', 0)
                    })
                except Exception as e:
                    print(f"⚠️ Error processing file info: {e}")
                    continue
            
            print(f"📊 Found {len(file_list)} files for user {user_id}")
            return {'success': True, 'files': file_list}
            
        except Exception as e:
            print(f"❌ Failed to get file list: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Failed to get file list: {str(e)}'}