from flask import Blueprint, jsonify, redirect, url_for, render_template, flash, request, send_file
from flask_login import login_required, current_user
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.user_dashboard'))

    try:
        import database
        total_predictions = database.get_total_predictions_count()
    except Exception as e:
        logger.debug(f"Could not get predictions: {e}")
        total_predictions = 0

    return jsonify({
        'message': 'WESAD Stress Detection API - Advanced Edition',
        'status': 'running',
        'version': '2.0',
        'total_predictions': total_predictions,
        'authenticated': current_user.is_authenticated,
        'endpoints': {
            'login': '/auth/login',
            'register': '/auth/register',
            'dashboard': '/dashboard',
            'profile': '/profile',
            'api_docs': '/api/health'
        }
    })


@main_bp.route('/dashboard')
@login_required
def user_dashboard():
    """Main dashboard route"""
    try:
        import database
        user_stats = database.get_user_stats(str(current_user.id))

        import services
        is_monitoring = str(current_user.id) in services.active_monitors

        return render_template('dashboard.html',
                               user_stats=user_stats,
                               is_monitoring=is_monitoring,
                               current_user=current_user)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash("Error loading dashboard", "error")
        return redirect(url_for('main.index'))


@main_bp.route('/start-realtime')
@login_required
def start_realtime():
    """Start real-time monitoring"""
    try:
        user_id = str(current_user.id)
        import services

        if user_id in services.active_monitors:
            return jsonify({'status': 'already_active', 'message': 'Monitoring already active'})

        monitor = services.RealTimeStressMonitor(current_user, services.ml_service, None)
        services.active_monitors[user_id] = monitor
        monitor.start_monitoring()

        logger.info(f"Real-time monitoring started for user {current_user.username}")
        return jsonify({
            'status': 'success',
            'message': 'Real-time monitoring started successfully!',
            'user_id': user_id
        })
    except Exception as exc:
        logger.error(f"Failed to start real-time monitoring: {exc}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@main_bp.route('/stop-realtime')
@login_required
def stop_realtime():
    """Stop real-time monitoring"""
    try:
        user_id = str(current_user.id)
        import services

        if user_id in services.active_monitors:
            monitor = services.active_monitors.pop(user_id)
            monitor.stop_monitoring()
            logger.info(f"Real-time monitoring stopped for user {current_user.username}")
            return jsonify({'status': 'success', 'message': 'Monitoring stopped successfully'})
        else:
            return jsonify({'status': 'not_active', 'message': 'Monitoring was not active'})
    except Exception as exc:
        logger.error(f"Failed to stop real-time monitoring: {exc}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@main_bp.route('/monitoring-status')
@login_required
def monitoring_status():
    """Check current monitoring status"""
    try:
        user_id = str(current_user.id)
        import services

        if user_id in services.active_monitors:
            monitor = services.active_monitors[user_id]
            latest_data = monitor.get_latest_data()

            return jsonify({
                'status': 'active',
                'monitoring': True,
                'latest_data': latest_data,
                'message': 'Monitoring is active'
            })
        else:
            return jsonify({
                'status': 'inactive',
                'monitoring': False,
                'message': 'Monitoring is not active'
            })
    except Exception as exc:
        logger.error(f"Status check error: {exc}")
        return jsonify({
            'status': 'error',
            'monitoring': False,
            'message': str(exc)
        }), 500


@main_bp.route('/generate-test-data')
@login_required
def generate_test_data():
    """Generate test data for demonstration"""
    try:
        user_id = str(current_user.id)
        import database
        import random

        for i in range(10):
            stress_level = random.choice(['baseline', 'stress', 'amusement'])
            confidence = random.uniform(0.6, 0.95)
            features = {
                'heart_rate': random.randint(60, 100),
                'eda': random.uniform(0.1, 1.0),
                'temperature': random.uniform(36.0, 37.5)
            }

            database.store_prediction(
                stress_level,
                confidence,
                features,
                user_id,
                'ANN',
                []
            )

        flash("✅ Generated 10 test data points!", "success")
        return jsonify({'status': 'success', 'message': 'Test data generated'})
    except Exception as exc:
        logger.error(f"Test data generation error: {exc}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    """User profile management with Fitbit integration"""
    from models import db

    if request.method == 'POST':
        try:
            # Update user profile fields
            current_user.age = int(request.form.get('age', 0)) if request.form.get('age') else None
            current_user.gender = request.form.get('gender', '')
            current_user.height = float(request.form.get('height', 0)) if request.form.get('height') else None
            current_user.weight = float(request.form.get('weight', 0)) if request.form.get('weight') else None
            current_user.activity_level = request.form.get('activity_level', '')
            current_user.stress_threshold = float(request.form.get('stress_threshold', 0.7))

            db.session.commit()
            flash('✅ Profile updated successfully!', 'success')
            logger.info(f"Profile updated for user {current_user.username}")
            return redirect(url_for('main.user_profile'))

        except Exception as exc:
            db.session.rollback()
            logger.error(f'Profile update error: {exc}')
            flash('❌ Failed to update profile. Please try again.', 'error')

    # Check if Fitbit package is available
    FITBIT_AVAILABLE = False
    try:
        import fitbit
        FITBIT_AVAILABLE = True
    except ImportError:
        FITBIT_AVAILABLE = False

    return render_template('profile.html',
                           current_user=current_user,
                           FITBIT_AVAILABLE=FITBIT_AVAILABLE)


@main_bp.route('/connect-fitbit')
@login_required
def connect_fitbit():
    """Initiate Fitbit OAuth connection"""
    try:
        import fitbit
        from config import Config

        # Check if Fitbit credentials are configured
        if not hasattr(Config, 'FITBIT_CLIENT_ID') or not hasattr(Config, 'FITBIT_CLIENT_SECRET'):
            flash('⚠️ Fitbit integration not configured. Add FITBIT_CLIENT_ID and FITBIT_CLIENT_SECRET to your .env file.', 'error')
            return redirect(url_for('main.user_profile'))

        if not Config.FITBIT_CLIENT_ID or not Config.FITBIT_CLIENT_SECRET:
            flash('⚠️ Fitbit credentials not set in .env file', 'error')
            return redirect(url_for('main.user_profile'))

        # Create Fitbit OAuth2 client
        server = fitbit.Fitbit(
            Config.FITBIT_CLIENT_ID,
            Config.FITBIT_CLIENT_SECRET,
            redirect_uri=Config.FITBIT_REDIRECT_URI,
            timeout=10
        )

        # Get authorization URL
        url, _ = server.client.authorize_token_url()
        logger.info(f"Redirecting to Fitbit authorization: {url}")
        return redirect(url)

    except ImportError:
        flash('⚠️ python-fitbit package not installed. Run: pip install fitbit', 'error')
        return redirect(url_for('main.user_profile'))
    except Exception as exc:
        logger.error(f'Fitbit connection error: {exc}')
        flash(f'❌ Error connecting to Fitbit: {str(exc)}', 'error')
        return redirect(url_for('main.user_profile'))


@main_bp.route('/fitbit-callback')
@login_required
def fitbit_callback():
    """Handle Fitbit OAuth callback"""
    try:
        import fitbit
        from config import Config
        from models import db

        code = request.args.get('code')
        if not code:
            error = request.args.get('error', 'Unknown error')
            flash(f'❌ Fitbit authorization failed: {error}', 'error')
            return redirect(url_for('main.user_profile'))

        # Exchange code for access token
        server = fitbit.Fitbit(
            Config.FITBIT_CLIENT_ID,
            Config.FITBIT_CLIENT_SECRET,
            redirect_uri=Config.FITBIT_REDIRECT_URI
        )

        server.client.fetch_access_token(code)

        # Store Fitbit credentials
        current_user.fitbit_connected = True
        current_user.fitbit_access_token = server.client.session.token['access_token']
        current_user.fitbit_refresh_token = server.client.session.token['refresh_token']

        db.session.commit()

        flash('✅ Fitbit connected successfully!', 'success')
        logger.info(f"Fitbit connected for user {current_user.username}")
        return redirect(url_for('main.user_profile'))

    except Exception as exc:
        logger.error(f'Fitbit callback error: {exc}')
        flash(f'❌ Error connecting Fitbit: {str(exc)}', 'error')
        return redirect(url_for('main.user_profile'))


@main_bp.route('/disconnect-fitbit')
@login_required
def disconnect_fitbit():
    """Disconnect Fitbit integration"""
    try:
        from models import db

        current_user.fitbit_connected = False
        current_user.fitbit_access_token = None
        current_user.fitbit_refresh_token = None

        db.session.commit()

        flash('✅ Fitbit disconnected successfully', 'success')
        logger.info(f"Fitbit disconnected for user {current_user.username}")
        return redirect(url_for('main.user_profile'))

    except Exception as exc:
        logger.error(f'Fitbit disconnect error: {exc}')
        flash('❌ Error disconnecting Fitbit', 'error')
        return redirect(url_for('main.user_profile'))


@main_bp.route('/api/fitbit-data')
@login_required
def get_fitbit_data():
    """Endpoint to fetch live Fitbit data"""
    try:
        # Check if Fitbit is connected
        if not current_user.fitbit_connected:
            return jsonify({
                'error': 'Fitbit not connected',
                'message': 'Please connect your Fitbit account from the Profile page',
                'connected': False
            }), 400

        # Import Fitbit service
        from services.fitbit_service import FitbitDataService

        # Create Fitbit service instance
        fitbit_service = FitbitDataService(current_user)

        # Get physiological data
        data = fitbit_service.stream_physiological_data()

        if not data:
            return jsonify({
                'error': 'Failed to fetch Fitbit data',
                'message': 'Unable to retrieve data from Fitbit API'
            }), 500

        return jsonify({
            'status': 'success',
            'data': data,
            'connected': True,
            'message': 'Live Fitbit data retrieved successfully'
        })

    except ImportError as e:
        logger.error(f"Fitbit service import error: {e}")
        return jsonify({
            'error': 'Fitbit service not available',
            'message': 'Please install python-fitbit: pip install fitbit'
        }), 500

    except Exception as e:
        logger.error(f"Fitbit data endpoint error: {e}")
        return jsonify({
            'error': str(e),
            'message': 'An error occurred while fetching Fitbit data'
        }), 500


@main_bp.route('/test-email')
@login_required
def test_email():
    """Test email notification system"""
    try:
        from services.notifications import send_stress_alert_email

        success = send_stress_alert_email(
            current_user.email,
            'stress',
            0.85
        )

        if success:
            flash('✅ Test email sent successfully! Check your inbox.', 'success')
        else:
            flash('❌ Failed to send test email. Check email configuration in .env file.', 'error')

        return redirect(url_for('main.user_profile'))

    except Exception as e:
        logger.error(f"Test email error: {e}")
        flash(f'❌ Email test failed: {str(e)}', 'error')
        return redirect(url_for('main.user_profile'))


@main_bp.route('/research/dashboard')
@login_required
def research_dashboard():
    """Research dashboard with advanced analytics"""
    try:
        import database
        user_stats = database.get_user_stats(str(current_user.id))

        return render_template('research_dashboard.html',
                               user_stats=user_stats,
                               current_user=current_user)
    except Exception as e:
        logger.error(f"Research dashboard error: {e}")
        # Fallback to JSON if template not found
        return jsonify({
            'message': 'Research dashboard data',
            'user': current_user.username,
            'error': str(e)
        })


@main_bp.route('/export-report')
@login_required
def export_report():
    """Generate and download weekly report - redirect to API"""
    return redirect(url_for('api.weekly_report_pdf'))


@main_bp.route('/export-data')
@login_required
def export_data():
    """Export user data as CSV - redirect to API"""
    return redirect(url_for('api.export_data'))


@main_bp.route('/health-check')
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'WESAD Main Routes',
            'version': '2.0',
            'timestamp': datetime.now().isoformat(),
            'routes': [
                '/dashboard',
                '/profile',
                '/connect-fitbit',
                '/api/fitbit-data',
                '/test-email',
                '/research/dashboard'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
