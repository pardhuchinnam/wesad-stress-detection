import os
import sqlite3
from pathlib import Path

# Search for database in multiple locations
possible_locations = [
    'wesad_users.db',
    '../wesad_users.db',
    'instance/wesad_users.db',
    '../instance/wesad_users.db',
]

db_found = False
for db_path in possible_locations:
    if os.path.exists(db_path):
        print(f"🔍 Found database at: {db_path}")

        # Drop the users table using raw SQL
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS users")
            conn.commit()
            conn.close()
            print(f"✅ Dropped 'users' table from {db_path}")
            db_found = True
            break
        except Exception as e:
            print(f"❌ Error dropping table: {e}")
            # Try to delete the file completely
            try:
                os.remove(db_path)
                print(f"✅ Deleted database file: {db_path}")
                db_found = True
                break
            except Exception as e2:
                print(f"❌ Error deleting database: {e2}")

if not db_found:
    print("⚠️ No existing database found - will create new one")

# Now create fresh database with correct schema
print("\n🔧 Creating new database with profile fields...")

from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    # Drop all tables and recreate
    db.drop_all()
    db.create_all()

    # Create test user
    user = User(username='testuser', email='test@example.com')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    print("\n✅ Database recreated successfully!")
    print("✅ Test user created!")
    print("\n" + "=" * 50)
    print("🎉 You can now login with:")
    print("=" * 50)
    print("Username: testuser")
    print("Password: testpassword")
    print("=" * 50)
