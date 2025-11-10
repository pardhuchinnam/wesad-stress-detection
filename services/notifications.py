from flask_mail import Mail, Message
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global mail instance
mail = None
twilio_client = None


def init_notifications(app):
    """Initialize notification services"""
    global mail, twilio_client

    # Initialize Flask-Mail
    try:
        mail = Mail(app)
        logger.info("✅ Flask-Mail initialized")
    except Exception as e:
        logger.error(f"Flask-Mail initialization failed: {e}")

    # Initialize Twilio (optional)
    try:
        from twilio.rest import Client
        from config import Config

        if hasattr(Config, 'TWILIO_ACCOUNT_SID') and hasattr(Config, 'TWILIO_AUTH_TOKEN'):
            if Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
                twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
                logger.info("✅ Twilio client initialized")
    except ImportError:
        logger.warning("⚠️ Twilio not installed. SMS alerts disabled. Install with: pip install twilio")
    except Exception as e:
        logger.warning(f"⚠️ Twilio initialization skipped: {e}")


def send_stress_alert_email(user_email, stress_level, confidence):
    """Send email alert for high stress"""
    try:
        if not mail:
            logger.warning("Mail service not initialized")
            return False

        msg = Message(
            subject="🚨 High Stress Alert - WESAD",
            recipients=[user_email]
        )

        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: #E74C3C; color: white; padding: 20px; text-align: center; border-radius: 10px;">
                <h1>⚠️ High Stress Detected</h1>
            </div>
            <div style="padding: 20px; background-color: #f8f9fa; margin-top: 20px; border-radius: 10px;">
                <h2>Alert Details</h2>
                <p><strong>Stress Level:</strong> {stress_level}</p>
                <p><strong>Confidence:</strong> {confidence:.1%}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            <div style="padding: 20px; margin-top: 20px;">
                <h3>Recommended Actions:</h3>
                <ul>
                    <li>🧘 Take a 5-10 minute break</li>
                    <li>🫁 Practice deep breathing exercises</li>
                    <li>🚶 Go for a short walk</li>
                    <li>💧 Stay hydrated</li>
                    <li>👨‍⚕️ Contact support if stress persists</li>
                </ul>
            </div>
            <div style="color: #7F8C8D; font-size: 12px; margin-top: 30px; text-align: center;">
                This is an automated message from WESAD Stress Detection System.
            </div>
        </body>
        </html>
        """

        mail.send(msg)
        logger.info(f"✅ Stress alert email sent to {user_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        return False


def send_sms_alert(phone_number, message):
    """Send SMS alert via Twilio (optional)"""
    try:
        if not twilio_client:
            logger.warning("Twilio not configured - SMS disabled")
            return False

        from config import Config

        sms = twilio_client.messages.create(
            body=message,
            from_=Config.TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        logger.info(f"✅ SMS sent to {phone_number}: {sms.sid}")
        return True

    except Exception as e:
        logger.error(f"❌ SMS sending failed: {e}")
        return False


def send_weekly_summary_email(user_email, username, summary_data):
    """Send weekly summary email"""
    try:
        if not mail:
            logger.warning("Mail service not initialized")
            return False

        msg = Message(
            subject="📊 Your Weekly Wellness Summary - WESAD",
            recipients=[user_email]
        )

        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #3498DB; color: white; padding: 20px; text-align: center; border-radius: 10px;">
                <h1>📊 Weekly Wellness Summary</h1>
            </div>
            <div style="padding: 20px;">
                <p>Hi <strong>{username}</strong>,</p>
                <p>Here's your wellness summary for the past week:</p>

                <div style="background-color: #E8F8F5; padding: 15px; border-radius: 10px; margin: 20px 0;">
                    <h3>📈 Statistics</h3>
                    <p><strong>Total Readings:</strong> {summary_data.get('total_readings', 0)}</p>
                    <p><strong>Stress Episodes:</strong> {summary_data.get('stress_count', 0)}</p>
                    <p><strong>Baseline State:</strong> {summary_data.get('baseline_count', 0)}</p>
                    <p><strong>Relaxed Moments:</strong> {summary_data.get('amusement_count', 0)}</p>
                </div>

                <p>
                    <a href="http://127.0.0.1:5000/api/weekly-report-pdf" 
                       style="background-color: #2ECC71; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Download Full Report
                    </a>
                </p>

                <p style="margin-top: 30px;">Keep up the great work! 🌟</p>
            </div>
        </body>
        </html>
        """

        mail.send(msg)
        logger.info(f"✅ Weekly summary sent to {user_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Weekly summary email failed: {e}")
        return False


def check_and_send_alerts(user, prediction):
    """
    Check if alerts should be sent based on prediction

    Args:
        user: User object
        prediction: dict with stress_level and confidence
    """
    try:
        stress_level = prediction.get('stress_level', 'baseline')
        confidence = prediction.get('confidence', 0)

        # Check user's threshold
        threshold = user.stress_threshold if hasattr(user, 'stress_threshold') else 0.7

        if stress_level == 'stress' and confidence >= threshold:
            # Send email alert
            if user.email:
                send_stress_alert_email(user.email, stress_level, confidence)

            # Send SMS if phone number available and Twilio configured
            if hasattr(user, 'phone_number') and user.phone_number and twilio_client:
                sms_message = f"WESAD Alert: High stress detected ({confidence:.0%} confidence). Take a break and practice relaxation techniques."
                send_sms_alert(user.phone_number, sms_message)

            logger.info(f"✅ Stress alerts sent for user {user.username}")
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Alert check failed: {e}")
        return False
