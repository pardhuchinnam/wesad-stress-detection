"""Test database functionality"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import database
from datetime import datetime, timedelta, timezone


def test_database():
    print("\n" + "=" * 60)
    print("🧪 Testing Database Module")
    print("=" * 60)

    # Test 1: Database Info
    print("\n📊 Database Information:")
    info = database.get_database_info()
    if info:
        print(f"   Path: {info['database_path']}")
        print(f"   Total Records: {info['total_records']}")
        print(f"   Unique Users: {info['unique_users']}")
        print(f"   Size: {info['size_mb']} MB")
        if info['date_range']['first']:
            print(f"   Date Range: {info['date_range']['first']} to {info['date_range']['last']}")

    # Test 2: Store Prediction
    print("\n📝 Testing store_prediction():")
    test_features = {
        'heart_rate': 85,
        'eda': 0.5,
        'temperature': 36.8
    }
    pred_id = database.store_prediction(
        stress_level='stress',
        confidence=0.85,
        features=test_features,
        user_id='test_user',
        model_used='ANN',
        factors=[]
    )
    print(f"   ✅ Stored prediction ID: {pred_id}")

    # Test 3: Get User Stats
    print("\n📈 Testing get_user_stats():")
    stats = database.get_user_stats('1')
    print(f"   Total Predictions: {stats['total_predictions']}")
    print(f"   Stress Episodes: {stats['stress_episodes']}")
    print(f"   Wellbeing Score: {stats['wellbeing_score']}%")
    print(f"   Status: {stats['wellness_status']}")

    # Test 4: Get Historical Data
    print("\n📊 Testing get_historical_data():")
    historical = database.get_historical_data(days=7, user_id='1')
    if historical:
        print(f"   ✅ Retrieved {len(historical['timestamps'])} records")
    else:
        print("   ⚠️ No historical data found")

    # Test 5: Get Emotion Distribution
    print("\n🥧 Testing get_emotion_distribution():")
    distribution = database.get_emotion_distribution('1')
    print(f"   Baseline: {distribution['baseline']}")
    print(f"   Stress: {distribution['stress']}")
    print(f"   Amusement: {distribution['amusement']}")

    # Test 6: Get Predictions Since
    print("\n📅 Testing get_user_predictions_since():")
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    predictions = database.get_user_predictions_since('1', cutoff)
    print(f"   ✅ Retrieved {len(predictions)} predictions from last 7 days")

    print("\n" + "=" * 60)
    print("✅ All Tests Completed!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    test_database()
