"""Initialize database and create tables"""
import sys
from pathlib import Path

# Ensure backend is in path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from models import db, User

def init_all():
    """Initialize database and create test user"""
    print("🚀 Initializing WESAD Backend...")

    app = create_app()

    with app.app_context():
        # Create SQLAlchemy tables
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created")

        # Create test user
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('test123456')
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created: testuser / test123456")
        else:
            print("✅ Test user already exists")

        print("\n✨ Initialization complete!")
        print("🚀 Run: python app.py")

if __name__ == '__main__':
    init_all()
