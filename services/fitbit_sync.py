"""Background Fitbit data sync"""
import threading
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FitbitSyncService:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.thread = None

    def start_sync(self, user_id, access_token, refresh_token):
        """Start background sync for a user"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._sync_loop,
            args=(user_id, access_token, refresh_token)
        )
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"✅ Started Fitbit sync for user {user_id}")

    def stop_sync(self):
        """Stop background sync"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⏹️ Stopped Fitbit sync")

    def _sync_loop(self, user_id, access_token, refresh_token):
        """Continuous sync loop (every 60 seconds)"""
        from services.fitbit_service import FitbitService
        import database

        fitbit = FitbitService(access_token, refresh_token)

        while self.running:
            try:
                # Fetch latest data
                hr_data = fitbit.get_heart_rate_intraday()

                if hr_data:
                    latest_hr = hr_data[-1]['value']

                    # Store as prediction (simplified)
                    features = {'heart_rate': latest_hr}
                    database.store_prediction(
                        stress_level='baseline',  # Placeholder
                        confidence=0.5,
                        features=features,
                        user_id=user_id,
                        model_used='Fitbit_Sync',
                        factors=[]
                    )

                    logger.info(f"📊 Synced HR: {latest_hr} for user {user_id}")

                # Sleep for 60 seconds
                time.sleep(60)

            except Exception as e:
                logger.error(f"Sync error: {e}")
                time.sleep(60)
