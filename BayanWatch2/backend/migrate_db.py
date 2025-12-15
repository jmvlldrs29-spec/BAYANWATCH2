import sqlite3

def migrate_database():
    """Migrate the existing database to add new columns and tables"""
    try:
        # Connect to SQLite database
        connection = sqlite3.connect('bayanwatch.db')
        cursor = connection.cursor()
        print("✅ Connected to SQLite database")

        # Check if access_code column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'access_code' not in column_names:
            print("📝 Adding access_code column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN access_code TEXT")
            connection.commit()
            print("✅ Successfully added access_code column!")
        else:
            print("ℹ️  access_code column already exists")

        # Check if barangay_location column exists in complaints table
        cursor.execute("PRAGMA table_info(complaints)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'barangay_location' not in column_names:
            print("📝 Adding barangay_location column to complaints table...")
            cursor.execute("ALTER TABLE complaints ADD COLUMN barangay_location TEXT")
            connection.commit()
            print("✅ Successfully added barangay_location column!")
        else:
            print("ℹ️  barangay_location column already exists")

        # Create barangay_info table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS barangay_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                barangay_location TEXT,
                barangay_hotline TEXT,
                barangay_captain TEXT,
                barangay_residents INTEGER,
                background_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        connection.commit()
        print("✅ Created barangay_info table (if it didn't exist)")

        cursor.close()
        connection.close()
        print("🔌 SQLite connection closed")

    except sqlite3.Error as e:
        print(f"❌ Error migrating database: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 BayanWatch Database Migration")
    print("="*60 + "\n")
    migrate_database()
    print("\n✨ Migration completed!\n")
