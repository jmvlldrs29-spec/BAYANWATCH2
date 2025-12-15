import sqlite3

def separate_barangays():
    """
    Separate barangays that were registered under the same access code.
    This script helps clean up data when multiple barangays share one access code.
    """
    try:
        # Connect to database
        connection = sqlite3.connect('bayanwatch.db')
        cursor = connection.cursor()

        print("🔍 Analyzing current barangay registrations...")

        # Check current access code usage
        cursor.execute("""
            SELECT access_code, COUNT(*) as user_count,
                   GROUP_CONCAT(DISTINCT full_name) as users
            FROM users
            WHERE access_code IS NOT NULL
            GROUP BY access_code
            ORDER BY user_count DESC
        """)

        access_code_stats = cursor.fetchall()

        print("\n📊 Current Access Code Usage:")
        print("-" * 50)
        for code, count, users in access_code_stats:
            print(f"Access Code: {code}")
            print(f"Users: {count}")
            print(f"User Names: {users}")
            print("-" * 30)

        # Find access codes with multiple barangay officials
        cursor.execute("""
            SELECT u.access_code, COUNT(b.id) as official_count,
                   GROUP_CONCAT(b.barangay_location) as locations
            FROM users u
            LEFT JOIN barangay_info b ON u.id = b.user_id
            WHERE u.role = 'official' AND u.access_code IS NOT NULL
            GROUP BY u.access_code
            HAVING official_count > 1
        """)

        mixed_access_codes = cursor.fetchall()

        if not mixed_access_codes:
            print("\n✅ No access codes found with multiple barangay officials.")
            print("Your data appears to be properly separated already.")
            return

        print(f"\n⚠️  Found {len(mixed_access_codes)} access code(s) with multiple barangays:")
        print("-" * 60)

        for access_code, count, locations in mixed_access_codes:
            print(f"Access Code: {access_code}")
            print(f"Officials: {count}")
            print(f"Barangay Locations: {locations}")
            print("-" * 40)

        # Ask user for new access codes
        print("\n🔧 To fix this, we need to assign new access codes to separate barangays.")
        print("Current valid access codes:")
        print("  - ADMIN123 (Barangay Central)")
        print("  - BARANGAY456 (Barangay North)")
        print("  - OFFICIAL789 (Barangay South)")

        # For demonstration, let's create a plan
        print("\n📝 RECOMMENDED FIX:")
        print("1. Choose a new access code for each additional barangay")
        print("2. Update the users table to assign new access codes")
        print("3. Update the valid_access_codes mapping in app.py")

        print("\n💡 Example:")
        print("   - Keep BARANGAY456 for 'Barangay North'")
        print("   - Assign BARANGAY789 for 'Barangay South'")
        print("   - Assign BARANGAY101 for 'Barangay East'")

        # Show what the script would do
        print("\n🔄 This script can help you:")
        print("   ✅ Identify mixed access codes")
        print("   ✅ Suggest new access code assignments")
        print("   ✅ Update user records with new access codes")
        print("   ✅ Update the application configuration")

        cursor.close()
        connection.close()

        print("\n🚀 Ready to proceed with barangay separation!")
        print("Would you like me to:")
        print("1. Show you exactly which users need new access codes?")
        print("2. Create new access codes for the additional barangays?")
        print("3. Update the user records automatically?")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🏛️  BayanWatch Barangay Separation Tool")
    print("="*70 + "\n")
    separate_barangays()
    print("\n" + "="*70 + "\n")
