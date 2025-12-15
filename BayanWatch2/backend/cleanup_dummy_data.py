import sqlite3

def cleanup_dummy_data():
    """Remove dummy accounts and their associated data from the database"""
    try:
        # Connect to database
        connection = sqlite3.connect('bayanwatch.db')
        cursor = connection.cursor()

        print("Starting cleanup of dummy data...")

        # Find dummy users (Juan Dela Cruz and Maria Santos)
        dummy_users = ['Juan Dela Cruz', 'Maria Santos']

        for dummy_name in dummy_users:
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE full_name = ?", (dummy_name,))
            user_result = cursor.fetchone()

            if user_result:
                user_id = user_result[0]
                print(f"Removing dummy user: {dummy_name} (ID: {user_id})")

                # Delete associated barangay info
                cursor.execute("DELETE FROM barangay_info WHERE user_id = ?", (user_id,))

                # Delete associated complaints
                cursor.execute("DELETE FROM complaints WHERE user_id = ?", (user_id,))

                # Delete the user
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

                print(f"Removed {dummy_name} and all associated data")
            else:
                print(f"Dummy user {dummy_name} not found in database")

        # Commit changes
        connection.commit()

        # Get remaining data counts
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints")
        complaint_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM barangay_info")
        barangay_count = cursor.fetchone()[0]

        print("Database after cleanup:")
        print(f"   Users: {user_count}")
        print(f"   Complaints: {complaint_count}")
        print(f"   Barangay Info: {barangay_count}")

        cursor.close()
        connection.close()

        print("Dummy data cleanup completed successfully!")

    except sqlite3.Error as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("BayanWatch Dummy Data Cleanup")
    print("="*60 + "\n")
    cleanup_dummy_data()
    print("\nCleanup completed!\n")
