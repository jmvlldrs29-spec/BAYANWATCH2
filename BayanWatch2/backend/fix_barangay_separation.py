import sqlite3

def fix_barangay_separation():
    """
    Fix barangay separation by assigning unique access codes to different barangays.
    This script will:
    1. Identify barangays that share access codes
    2. Assign new unique access codes
    3. Update the database
    4. Update the app.py configuration
    """
    try:
        # Connect to database
        connection = sqlite3.connect('bayanwatch.db')
        cursor = connection.cursor()

        print("🔧 Starting barangay separation fix...")

        # Get current barangay officials and their access codes
        cursor.execute("""
            SELECT u.id, u.full_name, u.access_code, b.barangay_location
            FROM users u
            JOIN barangay_info b ON u.id = b.user_id
            WHERE u.role = 'official'
            ORDER BY u.access_code, b.barangay_location
        """)

        officials = cursor.fetchall()

        print(f"\n📋 Found {len(officials)} barangay officials:")
        print("-" * 70)
        for user_id, name, access_code, location in officials:
            print(f"ID: {user_id} | Name: {name} | Code: {access_code} | Location: {location}")
        print("-" * 70)

        # Group by barangay location to identify unique barangays
        barangay_groups = {}
        for user_id, name, access_code, location in officials:
            if location not in barangay_groups:
                barangay_groups[location] = []
            barangay_groups[location].append((user_id, name, access_code))

        print(f"\n🏛️  Identified {len(barangay_groups)} unique barangays:")

        # Define new access codes for each barangay
        new_access_codes = {
            "Barangay Malitam, Batangas City": "ADMIN123",  # Keep existing
            "Barangay Libjo, Batangas City": "BARANGAY456",  # Assign new
            "Barangay Sorosoro Karsada, Batangas City": "OFFICIAL789"  # Assign new
        }

        print("\n🔄 Access Code Assignments:")
        print("-" * 50)
        for barangay, new_code in new_access_codes.items():
            current_users = barangay_groups.get(barangay, [])
            print(f"Barangay: {barangay}")
            print(f"New Code: {new_code}")
            print(f"Officials: {len(current_users)}")
            for uid, name, old_code in current_users:
                print(f"  - {name} (was: {old_code})")
            print("-" * 30)

        # Apply the fixes
        print("\n⚙️  Applying fixes...")

        updates_made = 0
        for barangay, new_code in new_access_codes.items():
            current_users = barangay_groups.get(barangay, [])
            for user_id, name, old_code in current_users:
                if old_code != new_code:
                    cursor.execute(
                        "UPDATE users SET access_code = ? WHERE id = ?",
                        (new_code, user_id)
                    )
                    print(f"✅ Updated {name}: {old_code} → {new_code}")
                    updates_made += 1

        connection.commit()

        # Verify the fixes
        print(f"\n🔍 Verification - Access codes after fix:")
        cursor.execute("""
            SELECT access_code, COUNT(*) as count,
                   GROUP_CONCAT(barangay_location) as locations
            FROM users u
            JOIN barangay_info b ON u.id = b.user_id
            WHERE u.role = 'official'
            GROUP BY access_code
        """)

        results = cursor.fetchall()
        print("-" * 60)
        for code, count, locations in results:
            print(f"Code: {code} | Officials: {count} | Barangays: {locations}")

        cursor.close()
        connection.close()

        print(f"\n✅ Barangay separation completed!")
        print(f"   - Updates made: {updates_made}")
        print(f"   - Unique barangays: {len(barangay_groups)}")

        # Update app.py configuration
        print("\n📝 Next step: Update app.py with new access codes")
        print("The following access codes are now active:")
        for barangay, code in new_access_codes.items():
            print(f"  - {code}: {barangay}")

        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🏛️  BayanWatch Barangay Separation Fix")
    print("="*80 + "\n")
    success = fix_barangay_separation()
    if success:
        print("\n🎉 Data cleanup completed successfully!")
        print("You can now run the app and each barangay will have its own access code.")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")
    print("\n" + "="*80 + "\n")
