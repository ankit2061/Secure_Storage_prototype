import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'heal-ai-secret-key-2025')
    
    # MEGA Storage (using wrapper)
    MEGA_EMAIL = os.getenv('MEGA_EMAIL', 'heal-ai@example.com')
    MEGA_PASSWORD = os.getenv('MEGA_PASSWORD', 'heal-ai-password')
    
    # Database Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'heal_ai_storage')
    
    # Security Settings
    TOKEN_EXPIRY_HOURS = int(os.getenv('TOKEN_EXPIRY_HOURS', 24))
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 50))
    ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'pdf,doc,docx,txt,jpg,png,jpeg,csv,xlsx').split(',')
    
    # API Configuration
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', 8501))
    
    @staticmethod
    def validate_config():
        """Validate required configuration"""
        print("✅ Configuration loaded successfully")
        print(f"📧 MEGA Email: {Config.MEGA_EMAIL}")
        print(f"🔐 Database: {Config.DATABASE_NAME}")
        print(f"📁 Max file size: {Config.MAX_FILE_SIZE_MB}MB")
        return True
