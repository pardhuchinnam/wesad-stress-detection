"""Migrate old database to new schema - FIXED VERSION"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / 'stress_data.db'


def migrate_database():
    """Add missing columns to existing database WITHOUT deleting data"""
    print("\n" + "=" * 60)
    print("🔧 WESAD Database Migration Tool")
    print("=" * 60)
    print(f"📁 Database: {DB_PATH}")

    if not DB_PATH.exists():
        print("❌ Database not found!")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
        if not c.fetchone():
            print("❌ No predictions table found!")
            conn.close()
            return False

        # Get current record count
        c.execute("SELECT COUNT(*) FROM predictions")
        record_count = c.fetchone()[0]
        print(f"📊 Current records: {record_count}")

        # Get existing columns
        c.execute("PRAGMA table_info(predictions)")
        existing_columns = {row[1]: row[2] for row in c.fetchall()}
        print(f"📋 Existing columns: {list(existing_columns.keys())}")

        # Columns to add - FIXED: Remove CURRENT_TIMESTAMP default
        new_columns = {
            'heart_rate': 'REAL',
            'stress_score': 'REAL',
            'created_at': 'TEXT'  # ✅ FIXED: No default value for ALTER TABLE
        }

        columns_added = 0
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    print(f"   Adding column: {column_name} ({column_type})...", end=" ")
                    c.execute(f'ALTER TABLE predictions ADD COLUMN {column_name} {column_type}')
                    print("✅")
                    columns_added += 1
                except sqlite3.OperationalError as e:
                    if 'duplicate column name' in str(e).lower():
                        print("⏭️ (already exists)")
                    else:
                        print(f"❌ Error: {e}")
                        raise
            else:
                print(f"   Column {column_name}: ✅ (already exists)")

        # Update existing records with calculated values
        print("\n🔄 Updating existing records...")

        # Calculate stress_score for existing records
        c.execute('''
            UPDATE predictions 
            SET stress_score = CASE 
                WHEN prediction = 'stress' THEN probability 
                ELSE (1 - probability) 
            END
            WHERE stress_score IS NULL
        ''')
        updated_stress = c.rowcount
        if updated_stress > 0:
            print(f"   ✅ Updated stress_score for {updated_stress} records")

        # Set default heart_rate if features contain it
        c.execute('''
            UPDATE predictions 
            SET heart_rate = 75.0
            WHERE heart_rate IS NULL
        ''')
        updated_hr = c.rowcount
        if updated_hr > 0:
            print(f"   ✅ Set default heart_rate for {updated_hr} records")

        # Set created_at to timestamp for existing records
        c.execute('''
            UPDATE predictions 
            SET created_at = timestamp
            WHERE created_at IS NULL
        ''')
        updated_created = c.rowcount
        if updated_created > 0:
            print(f"   ✅ Set created_at for {updated_created} records")

        conn.commit()

        # Verify migration
        c.execute("PRAGMA table_info(predictions)")
        final_columns = [row[1] for row in c.fetchall()]

        c.execute("SELECT COUNT(*) FROM predictions")
        final_count = c.fetchone()[0]

        conn.close()

        print("\n✅ Migration Summary:")
        print(f"   Columns added: {columns_added}")
        print(f"   Final columns: {len(final_columns)}")
        print(f"   Records before: {record_count}")
        print(f"   Records after: {final_count}")
        print(f"   Data preserved: {'✅ YES' if record_count == final_count else '❌ NO'}")

        if record_count != final_count:
            print("\n⚠️ WARNING: Record count mismatch! Data may be lost.")
            return False

        print("\n🎉 Migration completed successfully!")
        print("=" * 60 + "\n")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_schema():
    """Verify the database schema is correct"""
    print("\n🔍 Verifying Database Schema...")

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Get table info
        c.execute("PRAGMA table_info(predictions)")
        columns = {row[1]: row[2] for row in c.fetchall()}

        required_columns = {
            'id': 'INTEGER',
            'timestamp': 'TEXT',
            'prediction': 'TEXT',
            'probability': 'REAL',
            'user_id': 'TEXT',
            'features': 'TEXT',
            'model_used': 'TEXT',
            'explanation_factors': 'TEXT',
            'heart_rate': 'REAL',
            'stress_score': 'REAL',
            'created_at': 'TEXT'
        }

        print("\n📋 Schema Check:")
        all_good = True
        missing = []
        for col_name, col_type in required_columns.items():
            if col_name in columns:
                print(f"   ✅ {col_name} ({columns[col_name]})")
            else:
                print(f"   ❌ {col_name} - MISSING")
                all_good = False
                missing.append(col_name)

        # Check for data
        c.execute("SELECT COUNT(*) FROM predictions")
        count = c.fetchone()[0]
        print(f"\n📊 Total records: {count}")

        # Sample a few records to verify data
        if count > 0:
            c.execute("SELECT timestamp, prediction, probability, heart_rate, stress_score FROM predictions LIMIT 3")
            print("\n📝 Sample records:")
            for row in c.fetchall():
                print(f"   {row[0][:19]} | {row[1]:10s} | prob={row[2]:.2f} | hr={row[3]} | stress={row[4]}")

        conn.close()

        if all_good:
            print("\n✅ Schema is correct!")
        else:
            print(f"\n❌ Schema has missing columns: {missing}")

        return all_good

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == '__main__':
    success = migrate_database()

    if success:
        verify_schema()
        print("\n✅ You can now run:")
        print("   1. python test_database.py  (to test)")
        print("   2. python generate_test_timeline.py 1  (to add more data)")
        print("   3. python app.py  (to start the application)")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
