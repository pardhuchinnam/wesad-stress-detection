"""Fix timeline by regenerating data for correct user"""
from app import create_app
from models import User, db
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import database
import random
import json
import sqlite3

print("\n" + "=" * 60)
print("🔧 WESAD Timeline Fix Tool")
print("=" * 60)

# Create app context
app = create_app()

with app.app_context():
    # Find the logged-in user
    user = User.query.filter_by(username='testuser').first()

    if not user:
        print("❌ User 'testuser' not found!")
        print("   Available users:")
        for u in User.query.all():
            print(f"   - {u.username} (ID: {u.id})")
        sys.exit(1)

    print(f"\n✅ Found user: {user.username}")
    print(f"   ID: {user.id}")
    print(f"   Email: {user.email}")

    user_id = str(user.id)

    # Check existing data
    existing = database.get_user_predictions_since(user_id, datetime.now(timezone.utc) - timedelta(days=7))
    print(f"\n📊 Existing predictions for user {user_id}: {len(existing)}")

    if len(existing) == 0:
        print("\n🔄 Generating timeline data for correct user ID...")

        emotions = ['baseline', 'stress', 'amusement']
        emotion_weights = [0.6, 0.3, 0.1]
        total_generated = 0

        for day in range(7):
            date = datetime.now(timezone.utc) - timedelta(days=6 - day)
            readings_per_day = random.randint(10, 20)

            for reading in range(readings_per_day):
                hour = random.randint(6, 23)
                minute = random.randint(0, 59)
                timestamp = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                emotion = random.choices(emotions, weights=emotion_weights)[0]
                confidence = random.uniform(0.65, 0.95)
                heart_rate = random.randint(60, 100) if emotion != 'stress' else random.randint(85, 120)

                features = {
                    'heart_rate': heart_rate,
                    'eda': round(random.uniform(0.1, 1.0), 3),
                    'temperature': round(random.uniform(36.0, 37.5), 2)
                }

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
                    user_id,  # Correct user ID!
                    json.dumps(features),
                    'ANN',
                    '[]',
                    heart_rate,
                    confidence if emotion == 'stress' else (1 - confidence)
                ))

                conn.commit()
                conn.close()
                total_generated += 1

        print(f"✅ Generated {total_generated} records for user {user_id}")
    else:
        print(f"✅ Data already exists - should work now!")

    # Verify
    final_check = database.get_user_predictions_since(user_id, datetime.now(timezone.utc) - timedelta(days=7))
    print(f"\n📈 Final count: {len(final_check)} predictions")

    if final_check:
        print("\n✅ Timeline should now work! Refresh your dashboard.")
    else:
        print("\n❌ Still no data - check user_id mismatch")

print("=" * 60 + "\n")
