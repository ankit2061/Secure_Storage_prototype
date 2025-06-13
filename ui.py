import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import os

# Configure Streamlit page
st.set_page_config(
    page_title="🔐 Heal AI - Secure Document Storage",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-zone {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9ff;
    }
    .file-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class HealAIStorageUI:
    def __init__(self):
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5001')
        print(f"🔗 Streamlit connecting to: {self.api_base_url}")
        
    def init_session_state(self):
        """Initialize session state variables"""
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'token' not in st.session_state:
            st.session_state.token = None
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'username' not in st.session_state:
            st.session_state.username = None
    
    def make_authenticated_request(self, method, endpoint, **kwargs):
        """Make authenticated API request"""
        headers = kwargs.get('headers', {})
        if st.session_state.token:
            headers['Authorization'] = f'Bearer {st.session_state.token}'
        kwargs['headers'] = headers
        
        url = f"{self.api_base_url}{endpoint}"
        
        if method.upper() == 'GET':
            return requests.get(url, **kwargs)
        elif method.upper() == 'POST':
            return requests.post(url, **kwargs)
        elif method.upper() == 'DELETE':
            return requests.delete(url, **kwargs)
    
    def test_api_connection(self):
        """Test API connection"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Connected to API server")
                return True
            else:
                st.error(f"❌ API server responded with status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API server. Please ensure Flask API is running on http://localhost:5001")
            st.code("python app.py", language="bash")
            return False
        except Exception as e:
            st.error(f"❌ API connection error: {str(e)}")
            return False
    
    def login_page(self):
        """Login and registration page"""
        st.markdown('<div class="main-header"><h1>🔐 Heal AI Secure Document Storage</h1><p>Advanced Healthcare Document Management System</p></div>', unsafe_allow_html=True)
        
        # Debug: Show API URL
        st.write(f"🔗 API URL: {self.api_base_url}")
        
        # Test connection first
        if not self.test_api_connection():
            return
        
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("Login to Your Account")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                login_button = st.form_submit_button("🚀 Login", use_container_width=True)
                
                if login_button and username and password:
                    with st.spinner("Authenticating..."):
                        try:
                            response = requests.post(
                                f"{self.api_base_url}/login",
                                json={"username": username, "password": password},
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.token = data['token']
                                st.session_state.user_id = data['user_id']
                                st.session_state.username = data['username']
                                st.session_state.logged_in = True
                                st.success("✅ Login successful!")
                                st.rerun()
                            else:
                                try:
                                    error_data = response.json()
                                    st.error(f"❌ {error_data.get('error', 'Login failed')}")
                                except:
                                    st.error(f"❌ Login failed with status: {response.status_code}")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Cannot connect to API server")
                        except Exception as e:
                            st.error(f"❌ Login error: {str(e)}")
        
        with tab2:
            with st.form("register_form"):
                st.subheader("Create New Account")
                new_username = st.text_input("Choose Username", placeholder="Enter desired username")
                new_email = st.text_input("Email (Optional)", placeholder="Enter your email")
                new_password = st.text_input("Choose Password", type="password", placeholder="Enter secure password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                register_button = st.form_submit_button("🎯 Create Account", use_container_width=True)
                
                if register_button:
                    if not new_username or not new_password:
                        st.error("❌ Username and password are required")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    else:
                        with st.spinner("Creating account..."):
                            try:
                                response = requests.post(
                                    f"{self.api_base_url}/register",
                                    json={
                                        "username": new_username,
                                        "password": new_password,
                                        "email": new_email if new_email else None
                                    },
                                    timeout=10
                                )
                                
                                if response.status_code == 201:
                                    st.success("✅ Account created successfully! Please login.")
                                else:
                                    try:
                                        error_data = response.json()
                                        st.error(f"❌ {error_data.get('error', 'Registration failed')}")
                                    except:
                                        st.error(f"❌ Registration failed with status: {response.status_code}")
                            except requests.exceptions.ConnectionError:
                                st.error("❌ Cannot connect to API server")
                            except Exception as e:
                                st.error(f"❌ Registration error: {str(e)}")
    
    def main_dashboard(self):
        """Main dashboard after login"""
        st.markdown('<div class="main-header"><h1>📁 Document Storage Dashboard</h1></div>', unsafe_allow_html=True)
        
        # Sidebar
        with st.sidebar:
            st.markdown(f"### 👤 Welcome, {st.session_state.username}")
            st.markdown(f"**User ID:** `{st.session_state.user_id[:8]}...`")
            
            if st.button("🚪 Logout", use_container_width=True):
                for key in ['token', 'user_id', 'username', 'logged_in']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        # Main content tabs
        tab1, tab2 = st.tabs(["📤 Upload Files", "📥 My Files"])
        
        with tab1:
            self.upload_interface()
        
        with tab2:
            self.files_interface()
    
    def upload_interface(self):
        """File upload interface"""
        st.header("📤 Upload Secure Documents")
        
        uploaded_file = st.file_uploader(
            "Choose a file to upload securely",
            type=['pdf', 'doc', 'docx', 'txt', 'jpg', 'png', 'jpeg', 'csv', 'xlsx'],
            help="Select a document to securely store"
        )
        
        if uploaded_file is not None:
            st.write("**File Details:**")
            st.write(f"- Name: {uploaded_file.name}")
            st.write(f"- Size: {uploaded_file.size} bytes")
            st.write(f"- Type: {uploaded_file.type}")
            
            if st.button("🔒 Upload Securely"):
                with st.spinner("Uploading file securely..."):
                    try:
                        files = {'file': uploaded_file}
                        response = self.make_authenticated_request('POST', '/upload', files=files)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ File uploaded successfully!")
                            st.json(result)
                        else:
                            try:
                                error_data = response.json()
                                st.error(f"❌ Upload failed: {error_data.get('error', 'Unknown error')}")
                            except:
                                st.error(f"❌ Upload failed with status: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Upload error: {str(e)}")
    
    def files_interface(self):
        """Files management interface"""
        st.header("📁 My Secure Files")
        
        try:
            print(f"🔗 Making request to: {self.api_base_url}/files")
            response = self.make_authenticated_request('GET', '/files')
            
            print(f"📊 Response status: {response.status_code}")
            print(f"📊 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    files_data = response.json()
                    print(f"📊 Files data: {files_data}")
                    
                    files = files_data.get('files', [])
                    
                    if not files:
                        st.info("📭 No files uploaded yet. Use the Upload tab to add files.")
                        return
                    
                    # Display files
                    for file_info in files:
                        with st.expander(f"📄 {file_info.get('filename', 'Unknown')}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                upload_time = file_info.get('upload_time', 'Unknown')
                                if len(upload_time) > 19:
                                    upload_time = upload_time[:19]
                                st.write(f"**Upload Date:** {upload_time}")
                            with col2:
                                st.write(f"**Size:** {file_info.get('file_size', 0)} bytes")
                            with col3:
                                if st.button(f"⬇️ Download", key=f"download_{file_info.get('file_id', 'unknown')}"):
                                    self.download_file(file_info.get('file_id'), file_info.get('filename'))
                except ValueError as e:
                    st.error(f"❌ Invalid JSON response: {e}")
                    st.text(f"Raw response: {response.text}")
            else:
                st.error(f"❌ Failed to load files. Status: {response.status_code}")
                try:
                    error_data = response.json()
                    st.error(f"Error details: {error_data}")
                except:
                    st.text(f"Raw response: {response.text}")
                    
        except Exception as e:
            st.error(f"❌ Error loading files: {str(e)}")
            print(f"❌ Files interface error: {e}")
            import traceback
            traceback.print_exc()

    
    def download_file(self, file_id, filename):
        """Download a file"""
        with st.spinner(f"Downloading {filename}..."):
            try:
                response = self.make_authenticated_request('GET', f'/retrieve/{file_id}')
                
                if response.status_code == 200:
                    st.download_button(
                        label=f"💾 Save {filename}",
                        data=response.content,
                        file_name=filename,
                        mime='application/octet-stream'
                    )
                    st.success(f"✅ {filename} ready for download!")
                else:
                    st.error("❌ Download failed")
            except Exception as e:
                st.error(f"❌ Download error: {str(e)}")
    
    def run(self):
        """Main application runner"""
        self.init_session_state()
        
        if not st.session_state.logged_in:
            self.login_page()
        else:
            self.main_dashboard()

# Run the application
if __name__ == "__main__":
    app = HealAIStorageUI()
    app.run()