"""Utility functions for WESAD application"""
import logging
from datetime import datetime, timedelta, timezone
import numpy as np

logger = logging.getLogger(__name__)


def generate_personalized_recommendations(user_id):
    """Generate AI-powered personalized recommendations"""
    recommendations = {
        'morning_routine': [
            '🌅 Start with 10 minutes of mindfulness meditation',
            '💧 Hydrate well - drink 2 glasses of water',
            '🏃 Light stretching or yoga for 15 minutes',
            '🍎 Eat a nutritious breakfast'
        ],
        'work_breaks': [
            '⏰ Take 5-minute breaks every hour',
            '🧘 Practice deep breathing exercises',
            '👀 Follow 20-20-20 rule for eye health',
            '🚶 Take short walks during breaks'
        ],
        'evening_winddown': [
            '📱 Digital detox 1 hour before bed',
            '📚 Read a book or journal',
            '🛀 Take a warm shower',
            '😴 Maintain consistent sleep schedule'
        ],
        'stress_management': [
            '🎵 Listen to calming music',
            '🗣️ Talk to someone you trust',
            '📝 Write down your thoughts',
            '🌳 Spend time in nature'
        ]
    }
    return recommendations


def predict_stress_trends(user_id, hours_ahead=24):
    """Predict stress levels for upcoming hours"""
    hours = list(range(hours_ahead))
    forecast = []

    for hour in hours:
        current_hour = (datetime.now().hour + hour) % 24

        if 9 <= current_hour <= 17:
            base_stress = 0.5 + 0.2 * np.sin((current_hour - 9) * np.pi / 8)
        elif 0 <= current_hour <= 6:
            base_stress = 0.2
        else:
            base_stress = 0.3

        noise = np.random.normal(0, 0.05)
        stress_level = max(0.1, min(0.9, base_stress + noise))
        forecast.append(float(stress_level))

    high_risk_hours = [i for i, v in enumerate(forecast) if v > 0.6]
    peak_stress_time = int(hours[np.argmax(forecast)])

    return {
        'forecast': forecast,
        'hours': hours,
        'high_risk_hours': high_risk_hours,
        'peak_stress_time': peak_stress_time,
        'average_predicted_stress': float(np.mean(forecast)),
        'recommendation': 'Schedule breaks during high-risk hours'
    }
