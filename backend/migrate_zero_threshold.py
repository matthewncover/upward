#!/usr/bin/env python3
"""
Migration script to add zero_threshold column to habits table
"""
import sqlite3
from pathlib import Path

def migrate_database():
    # Database file path
    db_path = Path(__file__).parent / "upward_habits.db"
    
    if not db_path.exists():
        print("Database file not found. Creating fresh database with new schema.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if zero_threshold column already exists
        cursor.execute("PRAGMA table_info(habits)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'zero_threshold' not in columns:
            print("Adding zero_threshold column to habits table...")
            cursor.execute("ALTER TABLE habits ADD COLUMN zero_threshold REAL DEFAULT NULL")
            
            # Update Screen Time habit with zero_threshold value
            cursor.execute("""
                UPDATE habits 
                SET zero_threshold = 180 
                WHERE name = 'Screen Time (Post 9PM)' AND is_inverted = 1
            """)
            
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("zero_threshold column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()