"""Generate 7 days of realistic test data"""
import random
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import database


def generate_timeline_data(user_id='test_user', days=7):
    """Generate realistic timeline data"""
    print(f"🔄 Generating {days} days of test data for user: {user_id}")

    # Initialize database
    database.init_database()

    emotions = ['baseline', 'stress', 'amusement']
    emotion_weights = [0.6, 0.3, 0.1]  # More baseline, some stress, less amusement

    total_generated = 0

    # Generate data for each day
    for day in range(days):
        date = datetime.now(timezone.utc) - timedelta(days=days - day)

        # Generate 10-20 readings per day
        readings_per_day = random.randint(10, 20)

        for reading in range(readings_per_day):
            # Spread throughout the day
            hour = random.randint(6, 23)
            minute = random.randint(0, 59)

            timestamp = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Select emotion with weighted probability
            emotion = random.choices(emotions, weights=emotion_weights)[0]

            # Confidence varies by emotion
            if emotion == 'stress':
                confidence = random.uniform(0.65, 0.95)
            elif emotion == 'baseline':
                confidence = random.uniform(0.70, 0.90)
            else:
                confidence = random.uniform(0.60, 0.85)

            # Generate realistic features
            features = {
                'heart_rate': random.randint(60, 100) if emotion != 'stress' else random.randint(85, 120),
                'eda': random.uniform(0.1, 1.0),
                'temperature': random.uniform(36.0, 37.5),
                'respiration': random.uniform(12, 20),
                'ACC_x': random.uniform(-2, 2),
                'ACC_y': random.uniform(-2, 2),
                'ACC_z': random.uniform(-2, 2)
            }

            # Store directly in database
            import sqlite3
            import json

            conn = sqlite3.connect(database.DB_PATH)
            c = conn.cursor()

            c.execute('''
                INSERT INTO predictions 
                (timestamp, prediction, probability, user_id, features, model_used, 
                 explanation_factors, heart_rate, stress_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp.isoformat(),
                emotion,
                confidence,
                user_id,
                json.dumps(features),
                'ANN',
                '[]',
                features['heart_rate'],
                confidence if emotion == 'stress' else (1 - confidence)
            ))

            conn.commit()
            conn.close()

            total_generated += 1

    print(f"✅ Generated {total_generated} test predictions across {days} days")
    print(f"📊 Data spread: Baseline ~60%, Stress ~30%, Amusement ~10%")

    # Show summary
    stats = database.get_user_stats(user_id)
    print(f"\n📈 User Stats:")
    print(f"   Total Predictions: {stats['total_predictions']}")
    print(f"   Stress Episodes: {stats['stress_episodes']}")
    print(f"   Baseline Count: {stats['baseline_count']}")
    print(f"   Amusement Count: {stats['amusement_count']}")
    print(f"   Wellbeing Score: {stats['wellbeing_score']}%")
    print(f"   Status: {stats['wellness_status']}")


if __name__ == '__main__':
    # Get user ID from command line or use default
    user_id = sys.argv[1] if len(sys.argv) > 1 else '1'  # Use your actual user ID
    generate_timeline_data(user_id=user_id, days=7)
