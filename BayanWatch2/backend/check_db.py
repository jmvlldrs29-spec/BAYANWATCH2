#!/usr/bin/env python3
"""
Simple script to check database contents for BayanWatch
"""

from db_config import DatabaseConnection

def main():
    print("=" * 60)
    print("🔍 BAYANWATCH DATABASE INSPECTION")
    print("=" * 60)

    db = DatabaseConnection()

    if not db.connect():
        print("❌ Failed to connect to database")
        return

    try:
        # Check users table
        print("\n👥 USERS TABLE:")
        print("-" * 40)
        users = db.fetch_query("SELECT id, full_name, role, access_code FROM users ORDER BY id")
        if users:
            for user in users:
                print(f"ID: {user['id']}, Name: {user['full_name']}, Role: {user['role']}, Access Code: {user['access_code'] or 'None'}")
        else:
            print("No users found")

        # Check complaints table
        print("\n📝 COMPLAINTS TABLE:")
        print("-" * 40)
        complaints = db.fetch_query("SELECT id, user_id, title, status, created_at FROM complaints ORDER BY created_at DESC")
        if complaints:
            for complaint in complaints:
                print(f"ID: {complaint['id']}, User ID: {complaint['user_id']}, Title: {complaint['title'][:50]}..., Status: {complaint['status']}, Created: {complaint['created_at']}")
        else:
            print("No complaints found")

        # Summary stats
        print("\n📊 SUMMARY:")
        print("-" * 40)
        user_count = db.fetch_one("SELECT COUNT(*) as count FROM users")['count']
        complaint_count = db.fetch_one("SELECT COUNT(*) as count FROM complaints")['count']
        print(f"Total Users: {user_count}")
        print(f"Total Complaints: {complaint_count}")

    except Exception as e:
        print(f"❌ Error during inspection: {e}")

    finally:
        db.disconnect()

    print("\n✨ Inspection complete!\n")

if __name__ == "__main__":
    main()
