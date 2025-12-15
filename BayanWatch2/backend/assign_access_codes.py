#!/usr/bin/env python3
"""
Script to assign access codes to existing users in BayanWatch database
"""

from db_config import DatabaseConnection

def main():
    print("=" * 60)
    print("🔑 ASSIGNING ACCESS CODES TO EXISTING USERS")
    print("=" * 60)

    db = DatabaseConnection()

    if not db.connect():
        print("❌ Failed to connect to database")
        return

    try:
        # Get all users without access codes
        users_without_codes = db.fetch_query("SELECT id, full_name, role FROM users WHERE access_code IS NULL OR access_code = ''")

        if not users_without_codes:
            print("✅ All users already have access codes!")
            return

        print(f"Found {len(users_without_codes)} users without access codes:")

        # Assign access codes based on role
        for user in users_without_codes:
            if user['role'] == 'official':
                access_code = 'ADMIN123'  # Default for officials
            else:
                # For residents, assign based on some logic (you can modify this)
                # For now, assign a default barangay code
                access_code = 'BARANGAY456'

            # Update the user with access code
            query = "UPDATE users SET access_code = ? WHERE id = ?"
            db.execute_query(query, (access_code, user['id']))

            print(f"✅ Assigned {access_code} to {user['full_name']} (ID: {user['id']})")

        print(f"\n✅ Successfully assigned access codes to {len(users_without_codes)} users!")

    except Exception as e:
        print(f"❌ Error during assignment: {e}")

    finally:
        db.disconnect()

    print("\n✨ Assignment complete!\n")

if __name__ == "__main__":
    main()
