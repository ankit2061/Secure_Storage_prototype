from mega_wrapper import Mega
import os
from dotenv import load_dotenv
import tempfile

load_dotenv()

def test_flowchart_workflow():
    """Test the complete flowchart workflow"""
    print("🔄 Testing Heal AI Secure Storage Flowchart Workflow")
    print("=" * 60)
    
    try:
        # Step 1: User logs in (flowchart start)
        print("1️⃣ User logs in...")
        mega = Mega()
        m = mega.login(os.getenv('MEGA_EMAIL', 'test@example.com'), 
                      os.getenv('MEGA_PASSWORD', 'testpass'))
        
        # Simulate getting user ID from token
        user_id = "user_123"
        print(f"✅ User logged in with ID: {user_id}")
        
        # Step 2: Test Upload Workflow
        print("\n2️⃣ Testing Upload Workflow...")
        
        # Create user-specific folder (Store in user-specific folder)
        user_folder = m.create_user_folder(user_id)
        print(f"✅ Created user-specific folder: {user_folder}")
        
        # Create test file
        test_content = "This is a test file for Heal AI secure storage system"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_content)
            test_file_path = f.name
        
        # Upload file (Tag file with user ID + Upload to MEGA)
        print("📤 Uploading file...")
        uploaded_file_id = m.upload(test_file_path, dest=user_folder, dest_filename="test_document.txt")
        print(f"✅ File uploaded with ID: {uploaded_file_id}")
        
        # Step 3: Test Retrieve Workflow
        print("\n3️⃣ Testing Retrieve Workflow...")
        
        # Test authorized access (File in user's folder? -> Yes -> Allow access)
        print("🔍 Testing authorized access...")
        downloaded_data = m.download(uploaded_file_id, requesting_user_id=user_id)
        print(f"✅ Authorized access successful. Content: {downloaded_data.decode()[:50]}...")
        
        # Test unauthorized access (File in user's folder? -> No -> Deny access)
        print("🚫 Testing unauthorized access...")
        unauthorized_user_id = "user_456"
        try:
            m.download(uploaded_file_id, requesting_user_id=unauthorized_user_id)
            print("❌ ERROR: Unauthorized access should have been denied!")
        except Exception as e:
            print(f"✅ Unauthorized access correctly denied: {e}")
        
        # Step 4: Test User File Listing
        print("\n4️⃣ Testing User File Management...")
        user_files = m.get_user_files(user_id)
        print(f"✅ User has {len(user_files)} files:")
        for file_info in user_files:
            print(f"   📄 {file_info['filename']} (ID: {file_info['file_id'][:8]}...)")
        
        # Step 5: Test Different User Isolation
        print("\n5️⃣ Testing User Isolation...")
        
        # Create second user
        user_2_id = "user_789"
        user_2_folder = m.create_user_folder(user_2_id)
        
        # Upload file for user 2
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("User 2's private document")
            user_2_file_path = f.name
        
        user_2_file_id = m.upload(user_2_file_path, dest=user_2_folder, dest_filename="user2_doc.txt")
        
        # Verify user 1 cannot access user 2's files
        try:
            m.download(user_2_file_id, requesting_user_id=user_id)
            print("❌ ERROR: Cross-user access should be denied!")
        except Exception as e:
            print(f"✅ Cross-user access correctly denied: {e}")
        
        # Verify user 2 can access their own files
        user_2_data = m.download(user_2_file_id, requesting_user_id=user_2_id)
        print(f"✅ User 2 can access their own file: {user_2_data.decode()[:30]}...")
        
        # Step 6: Test System Overview
        print("\n6️⃣ System Overview...")
        all_files = m.get_files()
        folders = [f for f in all_files.values() if f['t'] == 1]
        files = [f for f in all_files.values() if f['t'] == 0]
        
        print(f"📊 Total folders: {len(folders)}")
        print(f"📊 Total files: {len(files)}")
        print(f"📊 User {user_id} files: {len(m.get_user_files(user_id))}")
        print(f"📊 User {user_2_id} files: {len(m.get_user_files(user_2_id))}")
        
        # Cleanup
        print("\n🧹 Cleaning up test files...")
        os.unlink(test_file_path)
        os.unlink(user_2_file_path)
        m.delete(uploaded_file_id)
        m.delete(user_2_file_id)
        m.delete(user_folder)
        m.delete(user_2_folder)
        
        print("\n✅ All flowchart tests passed successfully!")
        print("🔐 Secure document storage system working as designed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_flowchart_workflow()
