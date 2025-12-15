#!/usr/bin/env python3
"""
Test script to verify per-access-code background functionality
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from db_config import get_barangay_background, set_barangay_background, get_all_barangay_backgrounds

def test_per_access_code_backgrounds():
    """Test the new per-access-code background functionality"""

    print("🧪 Testing Per-Access-Code Background Functionality")
    print("="*60)

    # Test 1: Get backgrounds for different access codes
    print("\n📋 Test 1: Getting backgrounds for different access codes")

    access_codes = ["ADMIN123", "BARANGAY456", "OFFICIAL789", "INVALID123"]

    for access_code in access_codes:
        background = get_barangay_background(access_code)
        if background:
            print(f"✅ {access_code}: {background}")
        else:
            print(f"❌ {access_code}: No background found")

    # Test 2: Set new background for an access code
    print("\n📤 Test 2: Setting new background for BARANGAY456")

    test_path = "/static/uploads/test_barangay456_background.jpg"
    result = set_barangay_background("BARANGAY456", test_path, uploaded_by=1)

    if result:
        print(f"✅ Successfully set background for BARANGAY456: {test_path}")

        # Verify it was set
        background = get_barangay_background("BARANGAY456")
        if background == test_path:
            print("✅ Background verified successfully")
        else:
            print(f"❌ Background verification failed. Expected: {test_path}, Got: {background}")
    else:
        print("❌ Failed to set background")

    # Test 3: Update existing background
    print("\n🔄 Test 3: Updating existing background for BARANGAY456")

    updated_path = "/static/uploads/updated_barangay456_background.jpg"
    result = set_barangay_background("BARANGAY456", updated_path, uploaded_by=2)

    if result:
        print(f"✅ Successfully updated background for BARANGAY456: {updated_path}")

        # Verify it was updated
        background = get_barangay_background("BARANGAY456")
        if background == updated_path:
            print("✅ Background update verified successfully")
        else:
            print(f"❌ Background update verification failed. Expected: {updated_path}, Got: {background}")
    else:
        print("❌ Failed to update background")

    # Test 4: Get all barangay backgrounds
    print("\n📊 Test 4: Getting all barangay backgrounds")

    all_backgrounds = get_all_barangay_backgrounds()
    print(f"📋 Found {len(all_backgrounds)} barangay background(s):")

    for bg in all_backgrounds:
        print(f"   {bg['access_code']}: {bg['background_path']}")

    # Test 5: Test that different access codes have different backgrounds
    print("\n🔍 Test 5: Verifying different access codes have different backgrounds")

    admin_bg = get_barangay_background("ADMIN123")
    barangay_bg = get_barangay_background("BARANGAY456")
    official_bg = get_barangay_background("OFFICIAL789")

    if admin_bg and barangay_bg and official_bg:
        if admin_bg != barangay_bg and barangay_bg != official_bg and admin_bg != official_bg:
            print("✅ All access codes have different backgrounds")
        else:
            print("⚠️  Some access codes share the same background (this may be intentional)")
            print(f"   ADMIN123: {admin_bg}")
            print(f"   BARANGAY456: {barangay_bg}")
            print(f"   OFFICIAL789: {official_bg}")
    else:
        print("❌ Some access codes don't have backgrounds")

    print("\n" + "="*60)
    print("🎉 Per-access-code background testing completed!")

    return True

if __name__ == "__main__":
    test_per_access_code_backgrounds()
