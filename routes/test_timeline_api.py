"""Test timeline API directly"""
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import database

print("\n" + "=" * 60)
print("🔍 Testing Timeline Data")
print("=" * 60)

# Test getting predictions
user_id = '1'  # Your test user ID
cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

print(f"\nUser ID: {user_id}")
print(f"Cutoff Date: {cutoff_date}")

# Get predictions
predictions = database.get_user_predictions_since(user_id, cutoff_date)

print(f"\n✅ Found {len(predictions)} predictions")

if predictions:
    print("\n📊 Sample Records:")
    for i, pred in enumerate(predictions[:5]):
        print(f"   {i + 1}. {pred['timestamp']} | {pred['stress_level']} | {pred['confidence']:.2f}")

    print("\n" + "=" * 60)
    print("✅ Timeline data exists - API should work!")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("❌ No data found - Problem with database query")
    print("=" * 60)

    # Check if data exists at all
    stats = database.get_user_stats(user_id)
    print(f"\nUser Stats:")
    print(f"   Total Predictions: {stats['total_predictions']}")
    print(f"   Stress Episodes: {stats['stress_episodes']}")

    if stats['total_predictions'] > 0:
        print("\n⚠️ Data exists but get_user_predictions_since() is not returning it")
        print("   This could be a user_id mismatch issue")

        # Check what user IDs exist
        import sqlite3

        conn = sqlite3.connect(database.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT DISTINCT user_id FROM predictions LIMIT 10")
        user_ids = [row[0] for row in c.fetchall()]
        conn.close()

        print(f"\n   User IDs in database: {user_ids}")
        print(f"   Looking for user_id: '{user_id}'")
