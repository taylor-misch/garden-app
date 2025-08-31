-- Database Migration Script: Add Garden Support
-- This script adds garden_id foreign keys to existing tables and migrates existing data

-- First, ensure we have a default garden (create if it doesn't exist)
INSERT OR IGNORE INTO gardens (id, name, description, year)
VALUES (1, 'My Garden', 'Default garden', 2024);

-- Step 1: Add garden_id column to plant_types table
-- Check if column doesn't exist before adding
ALTER TABLE plant_types ADD COLUMN garden_id INTEGER;

-- Step 2: Update existing plant_types to reference default garden
UPDATE plant_types SET garden_id = 1 WHERE garden_id IS NULL;

-- Step 3: Create new plant_types table with proper constraints
CREATE TABLE plant_types_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    garden_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE
);

-- Copy data to new table
INSERT INTO plant_types_new (id, garden_id, name, description, created_at)
SELECT id, garden_id, name, description, created_at FROM plant_types;

-- Drop old table and rename new one
DROP TABLE plant_types;
ALTER TABLE plant_types_new RENAME TO plant_types;

-- Step 4: Add garden_id column to garden_activities table
ALTER TABLE garden_activities ADD COLUMN garden_id INTEGER;

-- Step 5: Update existing garden_activities to reference default garden
UPDATE garden_activities SET garden_id = 1 WHERE garden_id IS NULL;

-- Step 6: Create new garden_activities table with proper constraints
CREATE TABLE garden_activities_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    garden_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL CHECK (activity_type IN ('watering', 'fertilizing')),
    activity_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (garden_id) REFERENCES gardens (id) ON DELETE CASCADE
);

-- Copy data to new table
INSERT INTO garden_activities_new (id, garden_id, activity_type, activity_date, notes, created_at)
SELECT id, garden_id, activity_type, activity_date, notes, created_at FROM garden_activities;

-- Drop old table and rename new one
DROP TABLE garden_activities;
ALTER TABLE garden_activities_new RENAME TO garden_activities;

-- Step 7: Update harvests table to have proper cascading foreign key
CREATE TABLE harvests_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_type_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    harvest_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_type_id) REFERENCES plant_types (id) ON DELETE CASCADE
);

-- Copy data to new table
INSERT INTO harvests_new (id, plant_type_id, quantity, unit, harvest_date, notes, created_at)
SELECT id, plant_type_id, quantity, unit, harvest_date, notes, created_at FROM harvests;

-- Drop old table and rename new one
DROP TABLE harvests;
ALTER TABLE harvests_new RENAME TO harvests;

-- Step 8: Update plants table to have proper cascading foreign key
CREATE TABLE plants_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    planted_date DATE,
    location TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_type_id) REFERENCES plant_types (id) ON DELETE CASCADE
);

-- Copy data to new table
INSERT INTO plants_new (id, plant_type_id, name, planted_date, location, status, created_at)
SELECT id, plant_type_id, name, planted_date, location, status, created_at FROM plants;

-- Drop old table and rename new one
DROP TABLE plants;
ALTER TABLE plants_new RENAME TO plants;

-- Step 9: Update plant_journals table to have proper cascading foreign key
CREATE TABLE plant_journals_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    notes TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants (id) ON DELETE CASCADE
);

-- Copy data to new table
INSERT INTO plant_journals_new (id, plant_id, entry_date, notes, created_at)
SELECT id, plant_id, entry_date, notes, created_at FROM plant_journals;

-- Drop old table and rename new one
DROP TABLE plant_journals;
ALTER TABLE plant_journals_new RENAME TO plant_journals;

-- Verify the migration
SELECT 'Migration completed successfully!' as status;
SELECT 'Gardens table:' as info, COUNT(*) as count FROM gardens;
SELECT 'Plant types with garden_id:' as info, COUNT(*) as count FROM plant_types WHERE garden_id IS NOT NULL;
SELECT 'Garden activities with garden_id:' as info, COUNT(*) as count FROM garden_activities WHERE garden_id IS NOT NULL;
SELECT 'Total harvests:' as info, COUNT(*) as count FROM harvests;
SELECT 'Total plants:' as info, COUNT(*) as count FROM plants;
SELECT 'Total journal entries:' as info, COUNT(*) as count FROM plant_journals;
