#!/usr/bin/env python3
"""
Migration script to add barangay_backgrounds table and migrate existing background_path data
"""

import sqlite3
import os
import sys

def migrate_backgrounds():
    """Migrate background images from barangay_info to barangay_backgrounds table"""

    # Connect to database
    db_path = 'bayanwatch.db'
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🚀 Starting background migration...")

        # Check if barangay_backgrounds table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='barangay_backgrounds'")
        if cursor.fetchone():
            print("✅ barangay_backgrounds table already exists")
        else:
            # Create barangay_backgrounds table
            cursor.execute("""
                CREATE TABLE barangay_backgrounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    access_code TEXT NOT NULL UNIQUE,
                    background_path TEXT,
                    uploaded_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            print("✅ Created barangay_backgrounds table")

        # Check if background_path column exists in barangay_info and remove it if it does
        cursor.execute("PRAGMA table_info(barangay_info)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'background_path' in column_names:
            print("📋 Migrating existing background data...")

            # Get existing background data
            cursor.execute("""
                SELECT bi.user_id, bi.background_path, u.access_code
                FROM barangay_info bi
                JOIN users u ON bi.user_id = u.id
                WHERE bi.background_path IS NOT NULL AND bi.background_path != ''
            """)

            existing_backgrounds = cursor.fetchall()
            print(f"📊 Found {len(existing_backgrounds)} existing background(s) to migrate")

            # Insert into new table
            for user_id, background_path, access_code in existing_backgrounds:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO barangay_backgrounds (access_code, background_path, uploaded_by)
                        VALUES (?, ?, ?)
                    """, (access_code, background_path, user_id))
                    print(f"✅ Migrated background for {access_code}: {background_path}")
                except Exception as e:
                    print(f"❌ Error migrating background for {access_code}: {e}")

            # Remove background_path column from barangay_info
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            print("🔄 Removing background_path column from barangay_info...")

            # Get column info first
            cursor.execute("PRAGMA table_info(barangay_info)")
            columns = cursor.fetchall()
            new_columns = [col for col in columns if col[1] != 'background_path']

            # Create new table without background_path column
            column_defs = []
            for col in new_columns:
                col_def = f"{col[1]} {col[2]}"
                if col[3]:  # NOT NULL
                    col_def += " NOT NULL"
                if col[4]:  # DEFAULT
                    col_def += f" DEFAULT {col[4]}"
                if col[5]:  # PRIMARY KEY
                    col_def += " PRIMARY KEY"
                column_defs.append(col_def)

            # Add foreign key constraints
            column_defs.append("FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE")

            create_sql = f"""
                CREATE TABLE barangay_info_new (
                    {', '.join(column_defs)}
                )
            """

            cursor.execute(create_sql)

            # Copy data to new table (excluding background_path column)
            if new_columns:
                column_names = [col[1] for col in new_columns]
                placeholders = ','.join(['?' for _ in column_names])

                # Build SELECT query excluding background_path column
                select_columns = [col[1] for col in new_columns]
                select_sql = f"SELECT {', '.join(select_columns)} FROM barangay_info"

                cursor.execute(select_sql)
                filtered_data = cursor.fetchall()

                cursor.executemany(f"""
                    INSERT INTO barangay_info_new ({','.join(column_names)})
                    VALUES ({placeholders})
                """, filtered_data)

            # Replace old table
            cursor.execute("DROP TABLE barangay_info")
            cursor.execute("ALTER TABLE barangay_info_new RENAME TO barangay_info")

            print("✅ Removed background_path column from barangay_info")
        else:
            print("ℹ️  No background_path column found in barangay_info (already migrated)")

        # Insert default backgrounds for each access code if they don't exist
        default_backgrounds = {
            "ADMIN123": "/static/uploads/default_malitam.jpg",
            "BARANGAY456": "/static/uploads/default_libjo.jpg",
            "OFFICIAL789": "/static/uploads/default_sorosoro.jpg"
        }

        for access_code, default_path in default_backgrounds.items():
            cursor.execute("""
                INSERT OR IGNORE INTO barangay_backgrounds (access_code, background_path)
                VALUES (?, ?)
            """, (access_code, default_path))
            print(f"✅ Ensured default background exists for {access_code}")

        conn.commit()
        print("🎉 Migration completed successfully!")

        # Show final state
        cursor.execute("SELECT access_code, background_path FROM barangay_backgrounds")
        backgrounds = cursor.fetchall()

        print("\n📋 Current barangay backgrounds:")
        for access_code, path in backgrounds:
            print(f"   {access_code}: {path}")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("="*60)
    print("🗄️  BAYANWATCH BACKGROUND MIGRATION")
    print("="*60)

    success = migrate_backgrounds()

    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update your Flask app code to use barangay_backgrounds table")
        print("2. Test the new background system")
        print("3. Remove any old background-related code from frontend if needed")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)
