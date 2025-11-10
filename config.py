import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///wesad.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Fitbit Configuration
    FITBIT_CLIENT_ID = os.getenv('FITBIT_CLIENT_ID')
    FITBIT_CLIENT_SECRET = os.getenv('FITBIT_CLIENT_SECRET')
    FITBIT_REDIRECT_URI = os.getenv('FITBIT_REDIRECT_URI', 'http://127.0.0.1:5000/fitbit-callback')

    # Email Configuration (Flask-Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # Optional Twilio Configuration (for SMS alerts)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

    # Session Configuration
    SESSION_COOKIE_SECURE = False  # Set True for HTTPS in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    @staticmethod
    def validate_config():
        """Validate critical configuration keys"""
        issues = []

        if not Config.FITBIT_CLIENT_ID:
            issues.append("⚠️ FITBIT_CLIENT_ID not set")
        else:
            print(f"✅ Fitbit Client ID: {Config.FITBIT_CLIENT_ID[:6]}...")

        if not Config.FITBIT_CLIENT_SECRET:
            issues.append("⚠️ FITBIT_CLIENT_SECRET not set")
        else:
            print(f"✅ Fitbit Client Secret: {'*' * 20}")

        print(f"✅ Fitbit Redirect URI: {Config.FITBIT_REDIRECT_URI}")

        if not Config.MAIL_USERNAME:
            issues.append("⚠️ MAIL_USERNAME not set")
        else:
            print(f"✅ Email Username: {Config.MAIL_USERNAME}")

        if not Config.MAIL_PASSWORD:
            issues.append("⚠️ MAIL_PASSWORD not set")
        else:
            print(f"✅ Email Password: {'*' * 15}")

        if issues:
            print("\n⚠️ Configuration Issues:")
            for issue in issues:
                print(f"   {issue}")
            return False

        print("\n✅ All critical configuration valid!")
        return True
