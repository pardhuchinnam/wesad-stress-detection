"""Enhanced Fitbit Real-time Data Service with Eventlet-Compatible Background Sync"""
import logging
import eventlet
import time
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class FitbitDataService:
    """Service for fetching real-time data from Fitbit API with caching"""

    def __init__(self, user):
        """
        Args:
            user: User object with Fitbit credentials
        """
        self.user = user
        self.client = None
        self.cache = {}
        self.cache_timeout = 60  # Cache for 60 seconds
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Fitbit OAuth2 client"""
        try:
            if not self.user.fitbit_connected:
                logger.warning(f"Fitbit not connected for user {self.user.username}")
                return False

            # Import fitbit
            try:
                import fitbit
            except ImportError:
                logger.error("fitbit not installed. Install with: pip install fitbit")
                return False

            from config import Config

            self.client = fitbit.Fitbit(
                Config.FITBIT_CLIENT_ID,
                Config.FITBIT_CLIENT_SECRET,
                access_token=self.user.fitbit_access_token,
                refresh_token=self.user.fitbit_refresh_token,
                refresh_cb=self._token_refresh_callback
            )

            logger.info(f"✅ Fitbit client initialized for {self.user.username}")
            return True

        except Exception as e:
            logger.error(f"❌ Fitbit client initialization failed: {e}")
            return False

    def _token_refresh_callback(self, token):
        """Callback to update tokens when refreshed"""
        try:
            from models import db

            self.user.fitbit_access_token = token['access_token']
            self.user.fitbit_refresh_token = token['refresh_token']
            db.session.commit()
            logger.info("✅ Fitbit tokens refreshed and saved")
        except Exception as e:
            logger.error(f"❌ Token refresh callback failed: {e}")

    def _get_cached_or_fetch(self, cache_key, fetch_function):
        """Get data from cache or fetch new data"""
        current_time = time.time()

        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if current_time - cached_time < self.cache_timeout:
                logger.debug(f"✅ Returning cached data for {cache_key}")
                return cached_data

        # Fetch new data (blocking call wrapped safely)
        data = fetch_function()
        self.cache[cache_key] = (data, current_time)
        return data

    def get_heart_rate_intraday(self, date=None):
        """
        Get intraday heart rate data with 1-minute resolution

        Returns:
            list of {'time': ..., 'value': ...}
        """
        try:
            if not self.client:
                logger.warning("Fitbit client not initialized")
                return None

            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            def fetch():
                data = self.client.intraday_time_series(
                    'activities/heart',
                    base_date=date,
                    detail_level='1min'
                )
                hr_data = data.get('activities-heart-intraday', {}).get('dataset', [])
                logger.info(f"✅ Fetched {len(hr_data)} heart rate readings")
                return hr_data

            return self._get_cached_or_fetch(f'hr_intraday_{date}', fetch)

        except Exception as e:
            logger.error(f"❌ Heart rate fetch failed: {e}")
            return None

    def get_current_heart_rate(self):
        """Get most recent heart rate reading"""
        try:
            hr_data = self.get_heart_rate_intraday()
            if hr_data and len(hr_data) > 0:
                return hr_data[-1]['value']  # Most recent reading
            return None
        except Exception as e:
            logger.error(f"❌ Current HR fetch failed: {e}")
            return None

    def get_heart_rate_variability(self, date=None):
        """
        Get HRV (Heart Rate Variability) data

        Returns:
            dict with HRV metrics
        """
        try:
            if not self.client:
                return None

            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            data = self.client.get_hrv(date=date)

            if data.get('hrv'):
                hrv_data = data['hrv'][0]
                return {
                    'daily_rmssd': hrv_data.get('value', {}).get('dailyRmssd', 0),
                    'deep_rmssd': hrv_data.get('value', {}).get('deepRmssd', 0)
                }

            return None

        except Exception as e:
            logger.error(f"❌ HRV fetch failed: {e}")
            return None

    def get_activity_summary(self, date=None):
        """Get daily activity summary with detailed metrics"""
        try:
            if not self.client:
                logger.warning("Fitbit client not initialized")
                return None

            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            def fetch():
                data = self.client.activities(date=date)
                summary = {
                    'steps': data['summary'].get('steps', 0),
                    'calories': data['summary'].get('caloriesOut', 0),
                    'distance': data['summary'].get('distances', [{}])[0].get('distance', 0),
                    'active_minutes': data['summary'].get('fairlyActiveMinutes', 0) +
                                      data['summary'].get('veryActiveMinutes', 0),
                    'sedentary_minutes': data['summary'].get('sedentaryMinutes', 0),
                    'lightly_active_minutes': data['summary'].get('lightlyActiveMinutes', 0),
                    'resting_heart_rate': data['summary'].get('restingHeartRate', 0),
                    'floors': data['summary'].get('floors', 0)
                }
                logger.info(f"✅ Activity summary fetched: {summary}")
                return summary

            return self._get_cached_or_fetch(f'activity_{date}', fetch)

        except Exception as e:
            logger.error(f"❌ Activity summary fetch failed: {e}")
            return None

    def get_sleep_data(self, date=None):
        """Get detailed sleep data"""
        try:
            if not self.client:
                return None

            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            def fetch():
                data = self.client.sleep(date=date)

                if data.get('sleep') and len(data['sleep']) > 0:
                    sleep_record = data['sleep'][0]

                    # Calculate sleep stages
                    stages = sleep_record.get('levels', {}).get('summary', {})

                    return {
                        'duration_hours': sleep_record.get('duration', 0) / (1000 * 60 * 60),
                        'efficiency': sleep_record.get('efficiency', 0),
                        'minutes_asleep': sleep_record.get('minutesAsleep', 0),
                        'minutes_awake': sleep_record.get('minutesAwake', 0),
                        'deep_sleep_minutes': stages.get('deep', {}).get('minutes', 0),
                        'light_sleep_minutes': stages.get('light', {}).get('minutes', 0),
                        'rem_sleep_minutes': stages.get('rem', {}).get('minutes', 0),
                        'wake_count': sleep_record.get('awakeCount', 0),
                        'start_time': sleep_record.get('startTime', ''),
                        'end_time': sleep_record.get('endTime', '')
                    }

                return None

            return self._get_cached_or_fetch(f'sleep_{date}', fetch)

        except Exception as e:
            logger.error(f"❌ Sleep data fetch failed: {e}")
            return None

    def stream_physiological_data(self):
        """
        Stream comprehensive physiological data

        Returns:
            dict with multiple physiological signals
        """
        try:
            if not self.client:
                logger.warning("Fitbit client not initialized - returning simulated data")
                return self._get_simulated_data()

            # Fetch current data from multiple sources
            hr_data = self.get_heart_rate_intraday()
            activity = self.get_activity_summary()
            hrv = self.get_heart_rate_variability()

            # Get latest readings
            latest_hr = hr_data[-1]['value'] if hr_data and len(hr_data) > 0 else 70

            physiological_data = {
                'heart_rate': latest_hr,
                'hrv_rmssd': hrv.get('daily_rmssd', 0) if hrv else 0,
                'steps': activity.get('steps', 0) if activity else 0,
                'calories': activity.get('calories', 0) if activity else 0,
                'distance_km': activity.get('distance', 0) if activity else 0,
                'active_minutes': activity.get('active_minutes', 0) if activity else 0,
                'sedentary_minutes': activity.get('sedentary_minutes', 0) if activity else 0,
                'resting_heart_rate': activity.get('resting_heart_rate', 0) if activity else 0,
                'floors': activity.get('floors', 0) if activity else 0,
                'timestamp': datetime.now().isoformat(),
                'source': 'fitbit',
                'user_id': self.user.id
            }

            logger.info(f"✅ Physiological data streamed: HR={latest_hr}, Steps={activity.get('steps', 0)}")
            return physiological_data

        except Exception as e:
            logger.error(f"❌ Data streaming failed: {e}")
            return self._get_simulated_data(error=str(e))

    def _get_simulated_data(self, error=None):
        """Return simulated data when Fitbit is unavailable"""
        import random

        return {
            'heart_rate': random.randint(60, 90),
            'hrv_rmssd': random.randint(20, 80),
            'steps': random.randint(0, 500),
            'calories': random.randint(1500, 2000),
            'distance_km': round(random.uniform(0, 5), 2),
            'active_minutes': random.randint(0, 30),
            'sedentary_minutes': random.randint(300, 600),
            'resting_heart_rate': random.randint(55, 75),
            'floors': random.randint(0, 10),
            'timestamp': datetime.now().isoformat(),
            'source': 'simulated',
            'user_id': self.user.id,
            'error': error
        }

    def get_stress_score_from_hrv(self):
        """
        Calculate stress score from HRV data
        Higher HRV = Lower stress

        Returns:
            float: stress score (0-1)
        """
        try:
            hrv_data = self.get_heart_rate_variability()

            if not hrv_data:
                return 0.5  # Neutral score

            rmssd = hrv_data.get('daily_rmssd', 50)

            # Normalize RMSSD to stress score
            # Typical RMSSD range: 20-100 ms
            # Lower RMSSD = Higher stress
            if rmssd < 20:
                stress_score = 0.8
            elif rmssd < 40:
                stress_score = 0.6
            elif rmssd < 60:
                stress_score = 0.4
            elif rmssd < 80:
                stress_score = 0.2
            else:
                stress_score = 0.1

            logger.info(f"✅ Calculated stress score from HRV: {stress_score} (RMSSD: {rmssd})")
            return stress_score

        except Exception as e:
            logger.error(f"❌ Stress score calculation failed: {e}")
            return 0.5


class FitbitBackgroundSync:
    """Background service for continuous Fitbit data synchronization using eventlet"""

    def __init__(self, app):
        self.app = app
        self.running = False
        self.greenthread = None
        self.sync_interval = 60  # Sync every 60 seconds

    def start_sync(self, user):
        """Start background sync for a user using eventlet greenthread"""
        if self.running:
            logger.warning("Sync already running")
            return

        self.running = True
        # Use eventlet.spawn instead of threading.Thread
        self.greenthread = eventlet.spawn(self._sync_loop, user)
        logger.info(f"✅ Started Fitbit background sync for user {user.username}")

    def stop_sync(self):
        """Stop background sync"""
        self.running = False
        if self.greenthread:
            self.greenthread.kill()
        logger.info("⏹️ Stopped Fitbit background sync")

    def _sync_loop(self, user):
        """Continuous sync loop using eventlet-friendly sleep"""
        fitbit_service = FitbitDataService(user)

        while self.running:
            try:
                with self.app.app_context():
                    # Fetch latest data
                    phys_data = fitbit_service.stream_physiological_data()

                    if phys_data and phys_data['source'] == 'fitbit':
                        # Store in database
                        import database

                        features = {
                            'heart_rate': phys_data['heart_rate'],
                            'hrv_rmssd': phys_data.get('hrv_rmssd', 0),
                            'steps': phys_data['steps'],
                            'calories': phys_data['calories']
                        }

                        # Calculate stress from HRV
                        stress_score = fitbit_service.get_stress_score_from_hrv()
                        stress_level = 'stress' if stress_score > 0.6 else 'baseline'

                        database.store_prediction(
                            stress_level=stress_level,
                            confidence=stress_score,
                            features=features,
                            user_id=str(user.id),
                            model_used='Fitbit_Sync',
                            factors={'source': 'HRV-based'}
                        )

                        logger.info(f"📊 Synced: HR={phys_data['heart_rate']}, Stress={stress_score:.2f}")

                # Use eventlet.sleep instead of time.sleep (non-blocking)
                eventlet.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"❌ Sync error: {e}")
                eventlet.sleep(self.sync_interval)


# Global sync service instance
fitbit_sync_service = None


def init_fitbit_sync(app):
    """Initialize Fitbit sync service"""
    global fitbit_sync_service
    fitbit_sync_service = FitbitBackgroundSync(app)
    return fitbit_sync_service
