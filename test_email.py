"""Test email configuration"""
import os
from dotenv import load_dotenv
from flask_mail import Mail, Message
from flask import Flask

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

print("📧 Testing Email Configuration...")
print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
print(f"MAIL_PASSWORD: {'*' * 15} (set: {bool(app.config['MAIL_PASSWORD'])})")

with app.app_context():
    try:
        msg = Message(
            subject="🧪 WESAD Test Email",
            recipients=[os.getenv('MAIL_USERNAME')],
            html="""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #28a745;">✅ Email Configuration Successful!</h2>
                <p>Your WESAD application can now send emails.</p>
                <p><strong>Configuration Details:</strong></p>
                <ul>
                    <li>SMTP Server: smtp.gmail.com</li>
                    <li>Port: 587</li>
                    <li>TLS: Enabled</li>
                </ul>
                <p>This confirms your Gmail App Password is working correctly.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Sent from WESAD Stress Detection System<br>
                    Monday, November 10, 2025
                </p>
            </body>
            </html>
            """
        )

        mail.send(msg)
        print("\n✅ SUCCESS! Test email sent.")
        print(f"📬 Check your inbox at: {os.getenv('MAIL_USERNAME')}")

    except Exception as e:
        print(f"\n❌ ERROR: Email failed to send")
        print(f"Error details: {e}")
        import traceback

        traceback.print_exc()
