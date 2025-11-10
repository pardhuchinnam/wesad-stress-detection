"""Enhanced Database operations for stress predictions"""
import sqlite3
import logging
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# Use absolute path for database
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / 'stress_data.db'

# Ensure database directory exists
os.makedirs(DB_DIR, exist_ok=True)


def init_database():
    """Initialize database with all required tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Create predictions table with enhanced schema
        c.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prediction TEXT NOT NULL,
                probability REAL NOT NULL,
                user_id TEXT NOT NULL,
                features TEXT,
                model_used TEXT,
                explanation_factors TEXT,
                heart_rate REAL,
                stress_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index for faster queries
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_timestamp 
            ON predictions(user_id, timestamp)
        ''')

        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_prediction 
            ON predictions(prediction)
        ''')

        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_prediction 
            ON predictions(user_id, prediction)
        ''')

        conn.commit()
        conn.close()
        logger.info(f"✅ Database initialized at {DB_PATH}")
        return True

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False


def store_prediction(stress_level, confidence, features, user_id, model_used, factors):
    """Store a stress prediction with enhanced data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Extract heart rate from features if available
        heart_rate = None
        if isinstance(features, dict):
            heart_rate = features.get('heart_rate', features.get('HR', None))
            features_json = json.dumps(features)
        else:
            features_json = str(features)

        # Calculate stress score
        stress_score = confidence if stress_level == 'stress' else (1 - confidence)

        c.execute('''
            INSERT INTO predictions 
            (timestamp, prediction, probability, user_id, features, model_used, 
             explanation_factors, heart_rate, stress_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(timezone.utc).isoformat(),
            stress_level,
            confidence,
            str(user_id),  # Ensure string
            features_json,
            model_used,
            str(factors) if factors else '[]',
            heart_rate,
            stress_score
        ))

        conn.commit()
        prediction_id = c.lastrowid
        conn.close()

        logger.info(f"✅ Prediction stored: ID={prediction_id}, Level={stress_level}, Confidence={confidence:.2f}")
        return prediction_id

    except Exception as e:
        logger.error(f"❌ Error storing prediction: {e}")
        return None


def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        user_id = str(user_id)  # Ensure string

        # Total predictions
        c.execute('SELECT COUNT(*) FROM predictions WHERE user_id = ?', (user_id,))
        total_predictions = c.fetchone()[0]

        # Stress episodes
        c.execute(
            'SELECT COUNT(*) FROM predictions WHERE user_id = ? AND prediction = "stress"',
            (user_id,)
        )
        stress_episodes = c.fetchone()[0]

        # Baseline count
        c.execute(
            'SELECT COUNT(*) FROM predictions WHERE user_id = ? AND prediction = "baseline"',
            (user_id,)
        )
        baseline_count = c.fetchone()[0]

        # Amusement count
        c.execute(
            'SELECT COUNT(*) FROM predictions WHERE user_id = ? AND prediction = "amusement"',
            (user_id,)
        )
        amusement_count = c.fetchone()[0]

        # Average stress score
        c.execute(
            'SELECT AVG(stress_score) FROM predictions WHERE user_id = ?',
            (user_id,)
        )
        avg_stress = c.fetchone()[0] or 0

        # Recent 24h stress count
        cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        c.execute(
            'SELECT COUNT(*) FROM predictions WHERE user_id = ? AND timestamp > ? AND prediction = "stress"',
            (user_id, cutoff_24h)
        )
        stress_24h = c.fetchone()[0]

        conn.close()

        # Calculate wellbeing score (0-100)
        if total_predictions > 0:
            stress_ratio = stress_episodes / total_predictions
            wellbeing_score = int(max(0, min(100, 100 - (stress_ratio * 100))))
        else:
            wellbeing_score = 85
            stress_ratio = 0

        # Determine wellness status
        if wellbeing_score >= 90:
            wellness_status = 'Excellent 🌟'
        elif wellbeing_score >= 75:
            wellness_status = 'Very Good 😊'
        elif wellbeing_score >= 60:
            wellness_status = 'Good 👍'
        elif wellbeing_score >= 40:
            wellness_status = 'Fair 😐'
        else:
            wellness_status = 'Needs Attention ⚠️'

        return {
            'total_predictions': total_predictions,
            'stress_episodes': stress_episodes,
            'baseline_count': baseline_count,
            'amusement_count': amusement_count,
            'wellbeing_score': wellbeing_score,
            'wellness_status': wellness_status,
            'avg_stress_score': round(avg_stress, 3),
            'stress_24h': stress_24h,
            'stress_ratio': round(stress_ratio * 100, 1)
        }

    except Exception as e:
        logger.error(f"❌ Error getting user stats: {e}")
        return {
            'total_predictions': 0,
            'stress_episodes': 0,
            'baseline_count': 0,
            'amusement_count': 0,
            'wellbeing_score': 85,
            'wellness_status': 'Getting Started',
            'avg_stress_score': 0,
            'stress_24h': 0,
            'stress_ratio': 0
        }


def get_historical_data(days=7, user_id=None):
    """Get historical stress data for charts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        if user_id:
            c.execute('''
                SELECT timestamp, prediction, probability, stress_score 
                FROM predictions 
                WHERE user_id = ? AND timestamp > ? 
                ORDER BY timestamp ASC
            ''', (str(user_id), cutoff))
        else:
            c.execute('''
                SELECT timestamp, prediction, probability, stress_score 
                FROM predictions 
                WHERE timestamp > ? 
                ORDER BY timestamp ASC
            ''', (cutoff,))

        rows = c.fetchall()
        conn.close()

        if not rows:
            logger.warning(f"⚠️ No historical data found for user {user_id} in last {days} days")
            return None

        timestamps = [row[0] for row in rows]
        stress_levels = [row[2] if row[1] == 'stress' else 0.3 for row in rows]
        emotions = [row[1] for row in rows]
        stress_scores = [row[3] for row in rows]

        logger.info(f"✅ Retrieved {len(rows)} historical records for user {user_id}")

        return {
            'timestamps': timestamps,
            'stress_levels': stress_levels,
            'emotions': emotions,
            'stress_scores': stress_scores
        }

    except Exception as e:
        logger.error(f"❌ Error getting historical data: {e}")
        return None


def get_user_predictions(user_id, limit=100):
    """Get user's recent predictions with full details"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('''
            SELECT 
                id, timestamp, prediction as stress_level, 
                probability as confidence, features, model_used,
                heart_rate, stress_score
            FROM predictions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (str(user_id), limit))

        rows = c.fetchall()
        conn.close()

        predictions = []
        for row in rows:
            pred = dict(row)
            # Parse features JSON
            try:
                pred['features'] = json.loads(pred['features']) if pred['features'] else {}
            except:
                pred['features'] = {}
            predictions.append(pred)

        logger.info(f"✅ Retrieved {len(predictions)} predictions for user {user_id}")
        return predictions

    except Exception as e:
        logger.error(f"❌ Error getting user predictions: {e}")
        return []


def get_user_predictions_since(user_id, cutoff_date):
    """Get predictions since a specific date - for timeline"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('''
            SELECT 
                timestamp, prediction as stress_level, 
                probability as confidence, features, heart_rate
            FROM predictions
            WHERE user_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        ''', (str(user_id), cutoff_date.isoformat()))

        rows = c.fetchall()
        conn.close()

        predictions = []
        for row in rows:
            pred = dict(row)
            try:
                pred['features'] = json.loads(pred['features']) if pred['features'] else {}
            except:
                pred['features'] = {}
            predictions.append(pred)

        logger.info(f"✅ Retrieved {len(predictions)} predictions since {cutoff_date} for user {user_id}")
        return predictions

    except Exception as e:
        logger.error(f"❌ Error fetching predictions since date: {e}")
        return []


def get_total_predictions_count():
    """Get total predictions count across all users"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM predictions')
        count = c.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error(f"❌ Error getting total predictions: {e}")
        return 0


def get_emotion_distribution(user_id):
    """Get emotion distribution for pie chart"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute('''
            SELECT prediction, COUNT(*) as count
            FROM predictions
            WHERE user_id = ?
            GROUP BY prediction
        ''', (str(user_id),))

        rows = c.fetchall()
        conn.close()

        distribution = {
            'baseline': 0,
            'stress': 0,
            'amusement': 0
        }

        for row in rows:
            emotion, count = row
            if emotion in distribution:
                distribution[emotion] = count

        logger.info(f"✅ Emotion distribution for user {user_id}: {distribution}")
        return distribution

    except Exception as e:
        logger.error(f"❌ Error getting emotion distribution: {e}")
        return {'baseline': 0, 'stress': 0, 'amusement': 0}


def get_stress_timeline(user_id, hours=24):
    """Get stress timeline for last N hours"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        c.execute('''
            SELECT 
                strftime('%Y-%m-%d %H:00', timestamp) as hour,
                AVG(CASE WHEN prediction = 'stress' THEN 1 ELSE 0 END) as stress_ratio,
                COUNT(*) as count
            FROM predictions
            WHERE user_id = ? AND timestamp > ?
            GROUP BY hour
            ORDER BY hour ASC
        ''', (str(user_id), cutoff))

        rows = c.fetchall()
        conn.close()

        timeline = [{
            'hour': row[0],
            'stress_ratio': round(row[1], 2),
            'count': row[2]
        } for row in rows]

        return timeline

    except Exception as e:
        logger.error(f"❌ Error getting stress timeline: {e}")
        return []


def clean_old_predictions(days=30):
    """Clean predictions older than specified days"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        c.execute('DELETE FROM predictions WHERE timestamp < ?', (cutoff,))
        deleted = c.rowcount

        conn.commit()
        conn.close()

        logger.info(f"✅ Cleaned {deleted} old predictions (>{days} days)")
        return deleted

    except Exception as e:
        logger.error(f"❌ Error cleaning old predictions: {e}")
        return 0


def vacuum_database():
    """Optimize database by reclaiming unused space"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('VACUUM')
        conn.close()
        logger.info("✅ Database optimized (VACUUM completed)")
        return True
    except Exception as e:
        logger.error(f"❌ Error optimizing database: {e}")
        return False


def get_database_info():
    """Get database statistics and information"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Get total records
        c.execute('SELECT COUNT(*) FROM predictions')
        total_records = c.fetchone()[0]

        # Get unique users
        c.execute('SELECT COUNT(DISTINCT user_id) FROM predictions')
        unique_users = c.fetchone()[0]

        # Get date range
        c.execute('SELECT MIN(timestamp), MAX(timestamp) FROM predictions')
        date_range = c.fetchone()

        # Get database file size
        db_size_bytes = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        db_size_mb = round(db_size_bytes / (1024 * 1024), 2)

        conn.close()

        return {
            'database_path': str(DB_PATH),
            'total_records': total_records,
            'unique_users': unique_users,
            'date_range': {
                'first': date_range[0],
                'last': date_range[1]
            },
            'size_mb': db_size_mb
        }

    except Exception as e:
        logger.error(f"❌ Error getting database info: {e}")
        return None


# Initialize database on module import
if __name__ != '__main__':
    init_database()
    logger.info(f"📊 Database module loaded: {DB_PATH}")
