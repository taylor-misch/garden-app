#!/usr/bin/env python3
"""
Database Schema Fix for Garden Activity Logger
This fixes the missing garden_id columns in harvests, plants, and plant_journals tables.
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the existing database"""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_schema_fix.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    return None

def fix_schema(db_path):
    """Fix the database schema by adding garden_id to harvests, plants, and plant_journals"""
    print("🔧 Starting schema fix...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Disable foreign keys during migration
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Get the default garden ID
        cursor.execute("SELECT id FROM gardens LIMIT 1")
        default_garden_id = cursor.fetchone()
        if not default_garden_id:
            print("❌ No gardens found in database!")
            return False
        default_garden_id = default_garden_id[0]
        print(f"📝 Using default garden ID: {default_garden_id}")

        # Fix harvests table
        print("📝 Fixing harvests table...")
        cursor.execute("PRAGMA table_info(harvests)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'garden_id' not in columns:
            # Create new harvests table with garden_id
            cursor.execute('''
                CREATE TABLE harvests_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    garden_id INTEGER NOT NULL,
                    plant_type_id INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    harvest_date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE,
                    FOREIGN KEY (plant_type_id) REFERENCES plant_types (id) ON DELETE CASCADE
                )
            ''')

            # Copy data with default garden_id
            cursor.execute(f'''
                INSERT INTO harvests_new (id, garden_id, plant_type_id, quantity, unit, harvest_date, notes, created_at)
                SELECT id, {default_garden_id}, plant_type_id, quantity, unit, harvest_date, notes, created_at 
                FROM harvests
            ''')

            cursor.execute("DROP TABLE harvests")
            cursor.execute("ALTER TABLE harvests_new RENAME TO harvests")
            print("✅ Harvests table fixed")
        else:
            print("ℹ️ Harvests table already has garden_id")

        # Fix plants table
        print("📝 Fixing plants table...")
        cursor.execute("PRAGMA table_info(plants)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'garden_id' not in columns:
            cursor.execute('''
                CREATE TABLE plants_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    garden_id INTEGER NOT NULL,
                    plant_type_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    planted_date DATE,
                    location TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE,
                    FOREIGN KEY (plant_type_id) REFERENCES plant_types (id) ON DELETE CASCADE
                )
            ''')

            cursor.execute(f'''
                INSERT INTO plants_new (id, garden_id, plant_type_id, name, planted_date, location, status, created_at)
                SELECT id, {default_garden_id}, plant_type_id, name, planted_date, location, status, created_at 
                FROM plants
            ''')

            cursor.execute("DROP TABLE plants")
            cursor.execute("ALTER TABLE plants_new RENAME TO plants")
            print("✅ Plants table fixed")
        else:
            print("ℹ️ Plants table already has garden_id")

        # Fix plant_journals table
        print("📝 Fixing plant_journals table...")
        cursor.execute("PRAGMA table_info(plant_journals)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'garden_id' not in columns:
            cursor.execute('''
                CREATE TABLE plant_journals_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    garden_id INTEGER NOT NULL,
                    plant_id INTEGER NOT NULL,
                    entry_date DATE NOT NULL,
                    notes TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE,
                    FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
                )
            ''')

            cursor.execute(f'''
                INSERT INTO plant_journals_new (id, garden_id, plant_id, entry_date, notes, created_at)
                SELECT id, {default_garden_id}, plant_id, entry_date, notes, created_at 
                FROM plant_journals
            ''')

            cursor.execute("DROP TABLE plant_journals")
            cursor.execute("ALTER TABLE plant_journals_new RENAME TO plant_journals")
            print("✅ Plant journals table fixed")
        else:
            print("ℹ️ Plant journals table already has garden_id")

        # Re-enable foreign keys and commit
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()

        # Verify the fix
        print("📝 Verifying schema fix...")
        cursor.execute("SELECT COUNT(*) FROM harvests WHERE garden_id = ?", (default_garden_id,))
        harvests_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM plants WHERE garden_id = ?", (default_garden_id,))
        plants_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM plant_journals WHERE garden_id = ?", (default_garden_id,))
        journals_count = cursor.fetchone()[0]

        print(f"✅ Schema fix completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Harvests with garden_id: {harvests_count}")
        print(f"   - Plants with garden_id: {plants_count}")  
        print(f"   - Journal entries with garden_id: {journals_count}")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"❌ Schema fix failed: {e}")
        conn.rollback()
        conn.close()
        return False

def main():
    """Main function"""
    db_path = "../garden.db"

    print("🔧 Garden Activity Logger - Database Schema Fix")
    print("=" * 50)

    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return

    # Create backup
    backup_path = backup_database(db_path)

    # Confirm fix
    response = input("\n🤔 Do you want to proceed with the schema fix? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Schema fix cancelled by user")
        return

    # Run fix
    success = fix_schema(db_path)

    if success:
        print("\n🎉 Schema fix completed successfully!")
        print("💡 Your database now has proper garden_id relationships!")
        if backup_path:
            print(f"📄 Original database backed up at: {backup_path}")
    else:
        print("\n❌ Schema fix failed!")
        if backup_path:
            print(f"💡 You can restore from backup: {backup_path}")

if __name__ == "__main__":
    main()
