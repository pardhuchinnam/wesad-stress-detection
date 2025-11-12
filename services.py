from datetime import datetime, timezone
import logging
import threading
import time
import numpy as np

# import database  # <--- CRITICAL: REMOVE THIS TOP-LEVEL IMPORT

logger = logging.getLogger(__name__)

# Active monitoring sessions dictionary — must be global and accessible
active_monitors = {}
print("active_monitors dict initialized")  # For debugging


class MLService:
    """Machine Learning service for predictions"""

    def __init__(self):
        logger.info("✅ ML Service initialized")

    def predict_emotion(self, features, model='ensemble'):
        """Make emotion prediction"""
        return {
            'emotion': 'neutral',
            'confidence': 0.75,
            'model_used': model,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def predict_stress(self, sensor_data, model='RandomForest'):
        """Predict stress level from sensor data"""
        try:
            hr = sensor_data.get('heart_rate', 70)
            eda = sensor_data.get('eda', 0.3)

            if hr > 90 or eda > 0.7:
                stress_level = 'stress'
                confidence = 0.85
            elif hr > 75 or eda > 0.5:
                stress_level = 'amusement'
                confidence = 0.70
            else:
                stress_level = 'baseline'
                confidence = 0.75

            return {
                'stress_level': stress_level,
                'confidence': confidence,
                'model_used': model,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'factors': [f'Heart Rate: {hr}', f'EDA: {eda:.2f}']
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'stress_level': 'baseline',
                'confidence': 0.5,
                'model_used': 'fallback',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'factors': []
            }


class RealTimeStressMonitor:
    """Real-time stress monitoring for users"""

    def __init__(self, user, ml_service_instance, socketio_instance):
        self.user = user
        self.ml_service = ml_service_instance
        self.socketio = socketio_instance
        self.active = False
        self.monitoring_thread = None
        self.latest_sensor_data = {}
        logger.info(f"Monitor created for user {user.username}")

        # ✅ FIX: Import database here to break the circular import
        try:
            import database
            self.database = database
        except ImportError:
            self.database = None
            logger.error("Database module failed to load in RealTimeStressMonitor.")
        # End of FIX

    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.active:
            self.active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            logger.info(f"✅ Monitoring started for user {self.user.username}")

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.active = False
        logger.info(f"⏹️ Monitoring stopped for user {self.user.username}")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.active:
            try:
                sensor_data = self._get_live_sensor_data()
                self.latest_sensor_data = sensor_data

                if self.ml_service and self.database:  # Check for imported database
                    prediction = self.ml_service.predict_stress(sensor_data)

                    try:
                        self.database.store_prediction(
                            stress_level=prediction['stress_level'],
                            confidence=prediction['confidence'],
                            features=sensor_data,
                            user_id=str(self.user.id),
                            model_used=prediction['model_used'],
                            factors=prediction.get('factors', [])
                        )
                    except Exception as e:
                        logger.debug(f"Could not store prediction: {e}")

                    if self.socketio:
                        try:
                            self.socketio.emit('real_time_update', {
                                'stress_level': prediction['stress_level'],
                                'confidence': prediction['confidence'],
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'sensor_data': sensor_data,
                                'factors': prediction.get('factors', [])
                            }, room=f'user_{self.user.id}')
                        except Exception as e:
                            logger.debug(f"SocketIO emit failed: {e}")

                time.sleep(3)

            except Exception as exc:
                logger.error(f"Monitoring error: {exc}")
                time.sleep(5)

    def _get_live_sensor_data(self):
        """Generate realistic sensor data"""
        current_time = datetime.now(timezone.utc)
        hour = current_time.hour

        if 9 <= hour <= 17:
            base_hr = 75 + np.random.normal(0, 8)
            base_eda = 0.6 + np.random.normal(0, 0.3)
        else:
            base_hr = 65 + np.random.normal(0, 6)
            base_eda = 0.3 + np.random.normal(0, 0.2)

        return {
            'heart_rate': max(50, min(140, base_hr)),
            'eda': max(0.01, base_eda),
            'temperature': 32.0 + np.random.normal(0, 0.3),
            'respiration': 16 + np.random.normal(0, 3),
            'accel_x': np.random.normal(0, 0.05),
            'accel_y': np.random.normal(0, 0.05),
            'accel_z': np.random.normal(0, 0.05),
            'timestamp': current_time.isoformat(),
            'source': 'simulated'
        }

    def get_latest_data(self):
        """Get the latest sensor data"""
        if not self.latest_sensor_data:
            return {
                'stress_level': 'baseline',
                'confidence': 0.4,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'No data yet'
            }

        try:
            if self.ml_service:
                prediction = self.ml_service.predict_stress(self.latest_sensor_data)
            else:
                prediction = {
                    'stress_level': 'baseline',
                    'confidence': 0.4,
                    'model_used': 'fallback'
                }

            return {
                'stress_level': prediction['stress_level'],
                'confidence': prediction['confidence'],
                'timestamp': self.latest_sensor_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'status': 'Active',
                'source': self.latest_sensor_data.get('source', 'simulated')
            }
        except Exception as exc:
            logger.error(f"Error getting latest data: {exc}")
            return {
                'stress_level': 'baseline',
                'confidence': 0.4,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'Error'
            }


# Initialize ML service globally
ml_service = MLService()

logger.info("✅ Services module loaded successfully")