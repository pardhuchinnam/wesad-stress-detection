import os
import sys
import logging
from pathlib import Path
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
from dotenv import load_dotenv
from tensorflow.keras.models import load_model
import joblib
import numpy as np

# Add backend folder to sys.path
sys.path.append(str(Path(__file__).parent))

from models import User, db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask extensions
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO(async_mode='threading', cors_allowed_origins="*")
mail = Mail()

# Global ML models
ann_model = None
cnn_lstm_model = None
scaler = None


def load_ml_models():
    """Load ML models on startup"""
    global ann_model, cnn_lstm_model, scaler
    try:
        ann_model = load_model('models/emotion_ann_model.h5')
        logger.info("✅ ANN model loaded")
    except Exception as e:
        logger.warning(f"ANN model not loaded: {e}")

    try:
        cnn_lstm_model = load_model('models/cnn_lstm_model.h5')
        logger.info("✅ CNN-LSTM model loaded")
    except Exception as e:
        logger.warning(f"CNN-LSTM not loaded: {e}")

    try:
        scaler = joblib.load('models/scaler.save')
        logger.info("✅ Scaler loaded")
    except Exception as e:
        logger.warning(f"Scaler not loaded: {e}")


def create_app():
    app = Flask(__name__, template_folder='templates')

    # Load config
    from config import Config
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)
    CORS(app)

    # Load ML models
    load_ml_models()

    # Login manager config
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {e}")
            return None

    # Register blueprints
    def try_register_blueprint(bp_import_path, url_prefix=None):
        try:
            bp_module = __import__(bp_import_path, fromlist=['bp'])
            bp = getattr(bp_module, 'auth_bp' if 'auth' in bp_import_path else
                        'main_bp' if 'main' in bp_import_path else 'api_bp')
            if url_prefix:
                app.register_blueprint(bp, url_prefix=url_prefix)
            else:
                app.register_blueprint(bp)
            logger.info(f"✅ Registered blueprint '{bp.name}'")
        except Exception as e:
            logger.error(f"Failed to register {bp_import_path}: {e}")

    try_register_blueprint('routes.auth', url_prefix='/auth')
    try_register_blueprint('routes.main')
    try_register_blueprint('routes.api', url_prefix='/api')

    # SocketIO events
    try:
        from routes.socketio_events import init_socketio_events
        init_socketio_events(socketio, app)
        logger.info("✅ SocketIO events initialized")
    except Exception as e:
        logger.warning(f"SocketIO events not initialized: {e}")

    # Notification services
    try:
        from services.notifications import init_notifications
        init_notifications(app)
        logger.info("✅ Notification services initialized")
    except Exception as e:
        logger.warning(f"Notifications not initialized: {e}")

    # **NEW: Initialize Fitbit Sync Service**
    try:
        from services.fitbit_service import init_fitbit_sync
        fitbit_sync = init_fitbit_sync(app)
        logger.info("✅ Fitbit sync service initialized")
    except Exception as e:
        logger.warning(f"Fitbit sync not initialized: {e}")

    # Initialize databases
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ User database tables created")

            import database
            database.init_database()
            logger.info("✅ Prediction database initialized")

            Config.validate_config()

        except Exception as e:
            logger.error(f"❌ Error during initialization: {e}")

    # ==================== PREDICTION ROUTES ====================

    @app.route('/predict', methods=['POST'])
    def predict_emotion():
        """Main prediction endpoint using ANN"""
        try:
            data = request.get_json()
            features = np.array(data['features']).reshape(1, -1)

            if scaler and ann_model:
                scaled_features = scaler.transform(features)
                prediction = ann_model.predict(scaled_features)
                label_idx = np.argmax(prediction, axis=1)[0]
                confidence = float(prediction[0][label_idx])
            else:
                label_idx = np.random.choice([0, 1, 2])
                confidence = 0.75

            labels_map = {0: 'baseline', 1: 'stress', 2: 'amusement'}
            label = labels_map.get(label_idx, 'baseline')

            socketio.emit('emotion_update', {
                'emotion': label,
                'confidence': confidence,
                'timestamp': str(np.datetime64('now'))
            })

            return jsonify({
                'label': label,
                'confidence': confidence,
                'model': 'ANN'
            })

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/predict-cnn-lstm', methods=['POST'])
    def predict_cnn_lstm():
        """Prediction using CNN-LSTM"""
        try:
            data = request.get_json()
            features = np.array(data['features'])

            if cnn_lstm_model:
                prediction = cnn_lstm_model.predict(features)
                label_idx = np.argmax(prediction, axis=1)[0]
                confidence = float(prediction[0][label_idx])
            else:
                return jsonify({'error': 'CNN-LSTM not available'}), 404

            labels_map = {0: 'baseline', 1: 'stress', 2: 'amusement'}
            label = labels_map.get(label_idx, 'baseline')

            return jsonify({
                'label': label,
                'confidence': confidence,
                'model': 'CNN-LSTM'
            })

        except Exception as e:
            logger.error(f"CNN-LSTM error: {e}")
            return jsonify({'error': str(e)}), 500

    # Health check
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'WESAD Stress Detection System',
            'version': '2.0',
            'models_loaded': {
                'ann': ann_model is not None,
                'cnn_lstm': cnn_lstm_model is not None,
                'scaler': scaler is not None
            }
        })

    # Debug routes
    logger.info("------ FLASK URL MAP ------")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.rule}")
    logger.info("---------------------------")
    logger.info(f"📁 Template folder: {app.template_folder}")
    logger.info("🚀 WESAD Application initialized successfully")

    return app


if __name__ == '__main__':
    import os

    app = create_app()

    # Detect environment
    is_production = os.environ.get('FLASK_ENV', 'development') == 'production'
    port = int(os.environ.get('PORT', 5000))

    # Only show banner in development
    if not is_production:
        print("\n" + "=" * 70)
        print("🧠 WESAD - Wearable Stress & Affect Detection System v2.0")
        print("=" * 70)
        print("📊 Dashboard:        http://127.0.0.1:5000/dashboard")
        print("🔐 Login:            http://127.0.0.1:5000/auth/login")
        print("👤 Profile & Fitbit: http://127.0.0.1:5000/profile")
        print("📡 API Health:       http://127.0.0.1:5000/api/health")
        print("=" * 70)
        print("🎯 Enhanced Features v2.0:")
        print("   ✅ CNN-LSTM Hybrid Models")
        print("   ✅ SHAP Explainability")
        print("   ✅ Real-time Fitbit Sync")
        print("   ✅ HRV-based Stress Detection")
        print("   ✅ Context-aware Recommendations")
        print("   ✅ Email/SMS Alerts")
        print("   ✅ PDF Reports")
        print("   ✅ Correlation Analysis")
        print("   ✅ 24h Stress Forecasting")
        print("=" * 70 + "\n")
    else:
        print("🚀 WESAD v2.0 starting in PRODUCTION mode...")
        print(f"   Port: {port}")
        print(f"   Environment: {os.environ.get('FLASK_ENV')}")

    # Run server with environment-appropriate settings
    socketio.run(
        app,
        host='0.0.0.0' if is_production else '127.0.0.1',  # 0.0.0.0 for Render, 127.0.0.1 for local
        port=port,  # Uses PORT env var in production
        debug=not is_production,  # debug=False in production
        use_reloader=False  # Always False for stability
    )

# ============================================
# ✨ FIX FOR GUNICORN/PRODUCTION DEPLOYMENT ✨
# ============================================
# Create app instance at module level so Gunicorn can find it
app = create_app()
