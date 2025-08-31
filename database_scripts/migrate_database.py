#!/usr/bin/env python3
"""
Database Migration Script for Garden Activity Logger
Run this script to migrate an existing database to support the Gardens feature.
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the existing database"""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    return None

def check_migration_needed(db_path):
    """Check if migration is needed"""
    if not os.path.exists(db_path):
        print("ℹ️ No existing database found. New database will be created with proper schema.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if gardens table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gardens'")
        gardens_exists = cursor.fetchone() is not None

        if not gardens_exists:
            print("🔄 Migration needed: Gardens table missing")
            conn.close()
            return True

        # Check if plant_types has garden_id column
        cursor.execute("PRAGMA table_info(plant_types)")
        columns = [column[1] for column in cursor.fetchall()]
        has_garden_id = 'garden_id' in columns

        if not has_garden_id:
            print("🔄 Migration needed: plant_types missing garden_id column")
            conn.close()
            return True

        # Check if garden_activities has garden_id column
        cursor.execute("PRAGMA table_info(garden_activities)")
        columns = [column[1] for column in cursor.fetchall()]
        has_garden_id = 'garden_id' in columns

        if not has_garden_id:
            print("🔄 Migration needed: garden_activities missing garden_id column")
            conn.close()
            return True

        print("✅ Database is already up to date!")
        conn.close()
        return False

    except sqlite3.Error as e:
        print(f"❌ Error checking database: {e}")
        conn.close()
        return False

def run_migration(db_path):
    """Run the database migration"""
    print("🚀 Starting database migration...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Disable foreign keys during migration to avoid constraint issues
        cursor.execute("PRAGMA foreign_keys = OFF")

        print("📝 Step 1: Creating gardens table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gardens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                year INTEGER,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        print("📝 Step 2: Creating default garden...")
        cursor.execute("INSERT OR IGNORE INTO gardens (id, name, description, year) VALUES (1, 'My Garden', 'Default garden', ?)", (datetime.now().year,))

        print("📝 Step 3: Checking if plant_types migration is needed...")
        cursor.execute("PRAGMA table_info(plant_types)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'garden_id' not in columns:
            print("📝 Step 4: Migrating plant_types table...")

            # Create new table with proper constraints first
            cursor.execute('''
                CREATE TABLE plant_types_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    garden_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE
                )
            ''')

            # Copy data with default garden_id
            cursor.execute('''
                INSERT INTO plant_types_new (id, garden_id, name, description, created_at)
                SELECT id, 1, name, description, created_at FROM plant_types
            ''')

            # Replace old table
            cursor.execute("DROP TABLE plant_types")
            cursor.execute("ALTER TABLE plant_types_new RENAME TO plant_types")
            print("✅ plant_types table migrated successfully")
        else:
            print("ℹ️ plant_types table already has garden_id column")

        print("📝 Step 5: Checking if garden_activities migration is needed...")
        cursor.execute("PRAGMA table_info(garden_activities)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'garden_id' not in columns:
            print("📝 Step 6: Migrating garden_activities table...")

            # Create new table with proper constraints
            cursor.execute('''
                CREATE TABLE garden_activities_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    garden_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL CHECK (activity_type IN ('watering', 'fertilizing')),
                    activity_date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE
                )
            ''')

            # Copy data with default garden_id
            cursor.execute('''
                INSERT INTO garden_activities_new (id, garden_id, activity_type, activity_date, notes, created_at)
                SELECT id, 1, activity_type, activity_date, notes, created_at FROM garden_activities
            ''')

            # Replace old table
            cursor.execute("DROP TABLE garden_activities")
            cursor.execute("ALTER TABLE garden_activities_new RENAME TO garden_activities")
            print("✅ garden_activities table migrated successfully")
        else:
            print("ℹ️ garden_activities table already has garden_id column")

        print("📝 Step 7: Updating other tables with proper foreign key constraints...")

        # Update harvests table
        cursor.execute('''
            CREATE TABLE harvests_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_type_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                harvest_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plant_type_id) REFERENCES plant_types (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            INSERT INTO harvests_new (id, plant_type_id, quantity, unit, harvest_date, notes, created_at)
            SELECT id, plant_type_id, quantity, unit, harvest_date, notes, created_at FROM harvests
        ''')

        cursor.execute("DROP TABLE harvests")
        cursor.execute("ALTER TABLE harvests_new RENAME TO harvests")

        # Update plants table
        cursor.execute('''
            CREATE TABLE plants_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_type_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                planted_date DATE,
                location TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plant_type_id) REFERENCES plant_types (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            INSERT INTO plants_new (id, plant_type_id, name, planted_date, location, status, created_at)
            SELECT id, plant_type_id, name, planted_date, location, status, created_at FROM plants
        ''')

        cursor.execute("DROP TABLE plants")
        cursor.execute("ALTER TABLE plants_new RENAME TO plants")

        # Update plant_journals table
        cursor.execute('''
            CREATE TABLE plant_journals_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL,
                entry_date DATE NOT NULL,
                notes TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            INSERT INTO plant_journals_new (id, plant_id, entry_date, notes, created_at)
            SELECT id, plant_id, entry_date, notes, created_at FROM plant_journals
        ''')

        cursor.execute("DROP TABLE plant_journals")
        cursor.execute("ALTER TABLE plant_journals_new RENAME TO plant_journals")

        # Re-enable foreign keys and check integrity
        print("📝 Step 8: Enabling foreign keys and checking integrity...")
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA foreign_key_check")

        fk_violations = cursor.fetchall()
        if fk_violations:
            print(f"⚠️ Found {len(fk_violations)} foreign key violations:")
            for violation in fk_violations[:5]:  # Show first 5
                print(f"   - {violation}")
            if len(fk_violations) > 5:
                print(f"   - ... and {len(fk_violations) - 5} more")
            print("❌ Migration cannot proceed due to data integrity issues")
            conn.rollback()
            conn.close()
            return False

        conn.commit()

        # Verify migration
        print("📝 Step 9: Verifying migration...")
        cursor.execute("SELECT COUNT(*) FROM gardens")
        gardens_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM plant_types WHERE garden_id IS NOT NULL")
        plant_types_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM garden_activities WHERE garden_id IS NOT NULL")
        activities_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM harvests")
        harvests_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM plants")
        plants_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM plant_journals")
        journals_count = cursor.fetchone()[0]

        print(f"✅ Migration completed successfully!")
        print(f"📊 Migration Summary:")
        print(f"   - Gardens: {gardens_count}")
        print(f"   - Plant types with garden_id: {plant_types_count}")
        print(f"   - Garden activities with garden_id: {activities_count}")
        print(f"   - Harvests: {harvests_count}")
        print(f"   - Plants: {plants_count}")
        print(f"   - Journal entries: {journals_count}")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        conn.close()
        return False

def main():
    """Main migration function"""
    db_path = "../garden.db"

    print("🌱 Garden Activity Logger - Database Migration")
    print("=" * 50)

    if not check_migration_needed(db_path):
        return

    # Create backup
    backup_path = backup_database(db_path)

    # Confirm migration
    response = input("\n🤔 Do you want to proceed with the migration? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Migration cancelled by user")
        return

    # Run migration
    success = run_migration(db_path)

    if success:
        print("\n🎉 Migration completed successfully!")
        print("💡 You can now start using the new Garden features!")
        if backup_path:
            print(f"📄 Your original database is backed up at: {backup_path}")
    else:
        print("\n❌ Migration failed!")
        if backup_path:
            print(f"💡 You can restore from backup: {backup_path}")

if __name__ == "__main__":
    main()
