"""
Database module for Garden Activity Logger
Handles all database operations using SQLite with proper error handling and logging.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

class Database:
    """
    Database class for managing all garden-related data operations.
    Uses SQLite as the backend database with proper connection management.
    """

    def __init__(self, db_path: str = "garden.db"):
        """
        Initialize database connection and create tables if needed.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_db()
        logger.info(f"Database initialized at {db_path}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections with automatic cleanup.
        Ensures connections are properly closed even if errors occur.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            conn.close()

    def init_db(self):
        """Initialize the database with all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if this is a new database or needs migration
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gardens'")
            gardens_exists = cursor.fetchone() is not None

            # Gardens table - top level organization
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

            # For existing databases without gardens, create the tables as they were originally
            # and let the migration script handle the foreign keys
            if not gardens_exists:
                # This is either a new database or an old one without gardens
                cursor.execute("SELECT COUNT(*) FROM gardens")
                garden_count = cursor.fetchone()[0]
                if garden_count == 0:
                    cursor.execute(
                        "INSERT INTO gardens (name, description, year) VALUES (?, ?, ?)",
                        ("My Garden", "Default garden", datetime.now().year)
                    )

            # Check if plant_types has garden_id column
            cursor.execute("PRAGMA table_info(plant_types)")
            plant_types_columns = [column[1] for column in cursor.fetchall()]
            has_garden_id = 'garden_id' in plant_types_columns

            if has_garden_id:
                # New schema with garden support
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plant_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        garden_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS garden_activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        garden_id INTEGER NOT NULL,
                        activity_type TEXT NOT NULL CHECK (activity_type IN ('watering', 'fertilizing')),
                        activity_date DATE NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE
                    )
                ''')
            else:
                # Old schema - create tables as they were originally
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plant_types (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS garden_activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_type TEXT NOT NULL CHECK (activity_type IN ('watering', 'fertilizing')),
                        activity_date DATE NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # These tables always have the same structure
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS harvests (
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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plants (
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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plant_journals (
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

            conn.commit()

    # Garden CRUD methods
    def add_garden(self, name: str, description: str = "", year: int = None, location: str = "") -> int:
        """
        Add a new garden to the database.

        Args:
            name: Garden name (required)
            description: Optional garden description
            year: Garden year (defaults to current year)
            location: Optional garden location

        Returns:
            int: ID of the newly created garden
        """
        if year is None:
            year = datetime.now().year

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO gardens (name, description, year, location) VALUES (?, ?, ?, ?)",
                (name, description, year, location)
            )
            garden_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added garden: {name} (ID: {garden_id})")
            return garden_id

    def get_gardens(self) -> List[Dict[str, Any]]:
        """
        Retrieve all gardens ordered by year (descending) and name.

        Returns:
            List of garden dictionaries with id, name, description, year, location
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, year, location FROM gardens ORDER BY year DESC, name")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_garden_by_id(self, garden_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, year, location FROM gardens WHERE id = ?", (garden_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "description": row[2], "year": row[3], "location": row[4]}
            return None

    def update_garden(self, garden_id: int, name: str, description: str = "", year: int = None, location: str = "") -> bool:
        if year is None:
            year = datetime.now().year
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE gardens SET name = ?, description = ?, year = ?, location = ? WHERE id = ?",
                (name, description, year, location, garden_id)
            )
            success = cursor.rowcount > 0
            conn.commit()
            return success

    def delete_garden(self, garden_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gardens WHERE id = ?", (garden_id,))
            success = cursor.rowcount > 0
            conn.commit()
            return success

    # Plant types CRUD methods
    def add_plant_type(self, garden_id: int, name: str, description: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO plant_types (garden_id, name, description) VALUES (?, ?, ?)", (garden_id, name, description))
            plant_type_id = cursor.lastrowid
            conn.commit()
            return plant_type_id

    def get_plant_types(self, garden_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description FROM plant_types WHERE garden_id = ? ORDER BY name", (garden_id,))
            rows = cursor.fetchall()
            return [{"id": row[0], "name": row[1], "description": row[2]} for row in rows]

    def get_plant_type_by_id(self, plant_type_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, garden_id, name, description FROM plant_types WHERE id = ?", (plant_type_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "garden_id": row[1], "name": row[2], "description": row[3]}
            return None

    def update_plant_type(self, plant_type_id: int, name: str, description: str = "") -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE plant_types SET name = ?, description = ? WHERE id = ?", (name, description, plant_type_id))
            success = cursor.rowcount > 0
            conn.commit()
            return success

    def delete_plant_type(self, plant_type_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM plant_types WHERE id = ?", (plant_type_id,))
            success = cursor.rowcount > 0
            conn.commit()
            return success

    # Harvest CRUD methods
    def add_harvest(self, garden_id: int, plant_type_id: int, quantity: float, unit: str, harvest_date: str, notes: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO harvests (garden_id, plant_type_id, quantity, unit, harvest_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (garden_id, plant_type_id, quantity, unit, harvest_date, notes)
            )
            harvest_id = cursor.lastrowid
            conn.commit()
            return harvest_id

    def get_harvests(self, garden_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT h.id, pt.name as plant_name, h.quantity, h.unit, h.harvest_date, h.notes
                FROM harvests h
                JOIN plant_types pt ON h.plant_type_id = pt.id
                WHERE h.garden_id = ?
                ORDER BY h.harvest_date DESC, pt.name ASC
            ''', (garden_id,))
            rows = cursor.fetchall()

            # Group harvests by date
            grouped_harvests = {}
            for row in rows:
                harvest_date = row[4]
                harvest_data = {
                    "id": row[0], 
                    "plant_name": row[1], 
                    "quantity": row[2], 
                    "unit": row[3], 
                    "harvest_date": row[4], 
                    "notes": row[5]
                }

                if harvest_date not in grouped_harvests:
                    grouped_harvests[harvest_date] = []
                grouped_harvests[harvest_date].append(harvest_data)

            # Convert to list of date groups, maintaining order
            result = []
            for date in sorted(grouped_harvests.keys(), reverse=True):
                result.append({
                    "date": date,
                    "harvests": grouped_harvests[date]
                })

            return result

    def get_harvest_by_id(self, harvest_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT h.id, h.plant_type_id, pt.name as plant_name, h.quantity, h.unit, h.harvest_date, h.notes
                FROM harvests h
                JOIN plant_types pt ON h.plant_type_id = pt.id
                WHERE h.id = ?
            ''', (harvest_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], "plant_type_id": row[1], "plant_name": row[2], 
                    "quantity": row[3], "unit": row[4], "harvest_date": row[5], "notes": row[6]
                }
            return None

    def update_harvest(self, harvest_id: int, plant_type_id: int, quantity: float, unit: str, harvest_date: str, notes: str = "") -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE harvests SET plant_type_id = ?, quantity = ?, unit = ?, harvest_date = ?, notes = ? WHERE id = ?",
                (plant_type_id, quantity, unit, harvest_date, notes, harvest_id)
            )
            success = cursor.rowcount > 0
            conn.commit()
            return success

    def delete_harvest(self, harvest_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM harvests WHERE id = ?", (harvest_id,))
            success = cursor.rowcount > 0
            conn.commit()
            return success

    def get_harvest_summary(self, garden_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pt.name, h.unit, SUM(h.quantity) as total_quantity
                FROM harvests h
                JOIN plant_types pt ON h.plant_type_id = pt.id
                WHERE pt.garden_id = ?
                GROUP BY pt.name, h.unit
                ORDER BY pt.name
            ''', (garden_id,))
            rows = cursor.fetchall()
            return [{"plant_name": row[0], "unit": row[1], "total_quantity": row[2]} for row in rows]

    # Garden activities CRUD methods
    def add_garden_activity(self, garden_id: int, activity_type: str, activity_date: str, notes: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO garden_activities (garden_id, activity_type, activity_date, notes) VALUES (?, ?, ?, ?)",
                (garden_id, activity_type, activity_date, notes)
            )
            activity_id = cursor.lastrowid
            conn.commit()
            return activity_id

    def get_garden_activities(self, garden_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, activity_type, activity_date, notes FROM garden_activities WHERE garden_id = ? ORDER BY activity_date DESC", (garden_id,))
            rows = cursor.fetchall()
            return [{"id": row[0], "activity_type": row[1], "activity_date": row[2], "notes": row[3]} for row in rows]

    def get_garden_activity_by_id(self, activity_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, garden_id, activity_type, activity_date, notes FROM garden_activities WHERE id = ?", (activity_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "garden_id": row[1], "activity_type": row[2], "activity_date": row[3], "notes": row[4]}
            return None

    def update_garden_activity(self, activity_id: int, activity_type: str, activity_date: str, notes: str = "") -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE garden_activities SET activity_type = ?, activity_date = ?, notes = ? WHERE id = ?",
                (activity_type, activity_date, notes, activity_id)
            )
            success = cursor.rowcount > 0
            conn.commit()
            return success

    def delete_garden_activity(self, activity_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM garden_activities WHERE id = ?", (activity_id,))
            success = cursor.rowcount > 0
            conn.commit()
            return success

    # Individual plants CRUD methods
    def add_plant(self, plant_type_id: int, name: str, planted_date: str = "", location: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO plants (plant_type_id, name, planted_date, location) VALUES (?, ?, ?, ?)",
                (plant_type_id, name, planted_date, location)
            )
            plant_id = cursor.lastrowid
            conn.commit()
            return plant_id

    def get_plants(self, garden_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, pt.name as plant_type, p.name, p.planted_date, p.location, p.status
                FROM plants p
                JOIN plant_types pt ON p.plant_type_id = pt.id
                WHERE pt.garden_id = ?
                ORDER BY p.name
            ''', (garden_id,))
            rows = cursor.fetchall()
            return [{"id": row[0], "plant_type": row[1], "name": row[2], 
                    "planted_date": row[3], "location": row[4], "status": row[5]} for row in rows]

    def get_plant_by_id(self, plant_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.id, p.plant_type_id, pt.name as plant_type, p.name, p.planted_date, p.location, p.status
                FROM plants p
                JOIN plant_types pt ON p.plant_type_id = pt.id
                WHERE p.id = ?
            ''', (plant_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "plant_type_id": row[1], "plant_type": row[2], "name": row[3], 
                       "planted_date": row[4], "location": row[5], "status": row[6]}
            return None

    def update_plant(self, plant_id: int, plant_type_id: int, name: str, planted_date: str = "", location: str = "", status: str = "active") -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE plants SET plant_type_id = ?, name = ?, planted_date = ?, location = ?, status = ? WHERE id = ?",
                (plant_type_id, name, planted_date, location, status, plant_id)
            )
            success = cursor.rowcount > 0
            conn.commit()
            return success

    def delete_plant(self, plant_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
            success = cursor.rowcount > 0
            conn.commit()
            return success

    # Journal CRUD methods
    def add_journal_entry(self, plant_id: int, entry_date: str, notes: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO plant_journals (plant_id, entry_date, notes) VALUES (?, ?, ?)",
                (plant_id, entry_date, notes)
            )
            journal_id = cursor.lastrowid
            conn.commit()
            return journal_id

    def get_plant_journal_entries(self, plant_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, entry_date, notes FROM plant_journals WHERE plant_id = ? ORDER BY entry_date DESC",
                (plant_id,)
            )
            rows = cursor.fetchall()
            return [{"id": row[0], "entry_date": row[1], "notes": row[2]} for row in rows]

    def get_journal_entry_by_id(self, journal_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, plant_id, entry_date, notes FROM plant_journals WHERE id = ?", (journal_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "plant_id": row[1], "entry_date": row[2], "notes": row[3]}
            return None

    def update_journal_entry(self, journal_id: int, entry_date: str, notes: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE plant_journals SET entry_date = ?, notes = ? WHERE id = ?",
                (entry_date, notes, journal_id)
            )
            success = cursor.rowcount > 0
            conn.commit()
            return success

    def delete_journal_entry(self, journal_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM plant_journals WHERE id = ?", (journal_id,))
            success = cursor.rowcount > 0
            conn.commit()
            return success
