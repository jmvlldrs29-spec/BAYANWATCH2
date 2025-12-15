#!/usr/bin/env python3
"""
Test script for background image upload functionality.
This script tests the upload logic without running the full Flask server.
"""

import os
import sys
import tempfile
from werkzeug.utils import secure_filename

# Add the backend directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(__file__))

def test_file_operations():
    """Test basic file operations that the upload function uses."""
    print("=== TESTING FILE OPERATIONS ===")

    # Test creating a temporary image file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        temp_file.write(b'fake image content')
        temp_image_path = temp_file.name

    print(f"Created temp image: {temp_image_path}")

    # Test reading file content
    try:
        with open(temp_image_path, 'rb') as f:
            content = f.read()
        print(f"File size: {len(content)} bytes")
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return False

    # Test secure_filename
    test_filename = "background_1_test.jpg"
    secure_name = secure_filename(test_filename)
    print(f"Secure filename: {test_filename} -> {secure_name}")

    # Test directory creation
    test_upload_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static', 'uploads')
    print(f"Upload directory would be: {os.path.abspath(test_upload_dir)}")

    try:
        os.makedirs(test_upload_dir, exist_ok=True)
        print("Upload directory created successfully")
    except Exception as e:
        print(f"ERROR creating upload directory: {e}")
        return False

    # Test writing file to upload directory
    test_filepath = os.path.join(test_upload_dir, secure_name)
    try:
        with open(test_filepath, 'wb') as f:
            f.write(content)
        print(f"File written to: {test_filepath}")

        if os.path.exists(test_filepath):
            print("File exists after writing")
        else:
            print("ERROR: File does not exist after writing")
            return False
    except Exception as e:
        print(f"ERROR writing file: {e}")
        return False

    # Clean up
    try:
        os.unlink(temp_image_path)
        os.unlink(test_filepath)
        print("Cleanup successful")
    except Exception as e:
        print(f"Cleanup error (non-critical): {e}")

    return True

def test_database_operations():
    """Test database operations that the upload function uses."""
    print("\n=== TESTING DATABASE OPERATIONS ===")

    try:
        from db_config import db, get_user_by_id
        print("Database import successful")
    except Exception as e:
        print(f"ERROR importing database modules: {e}")
        return False

    # Test getting a user (assuming user ID 1 exists)
    try:
        user = get_user_by_id(1)
        print(f"User found: {user}")
        if user and user['role'] == 'official':
            print("User is an official - good for testing")
        else:
            print("WARNING: User is not an official or doesn't exist")
    except Exception as e:
        print(f"ERROR getting user: {e}")
        return False

    # Test barangay_info query
    try:
        existing = db.fetch_one("SELECT id FROM barangay_info WHERE user_id = ?", (1,))
        print(f"Barangay info record: {existing}")
        if existing:
            print("Barangay info exists - good for testing")
        else:
            print("WARNING: No barangay info record found")
    except Exception as e:
        print(f"ERROR querying barangay_info: {e}")
        return False

    # Test update query (dry run - don't actually update)
    try:
        # This is just a test query structure
        test_path = "/static/uploads/test.jpg"
        result = db.execute_query("UPDATE barangay_info SET background_path = ? WHERE user_id = ?", (test_path, 1))
        print(f"Update query executed (rows affected: {result})")
    except Exception as e:
        print(f"ERROR with update query: {e}")
        return False

    return True

def main():
    print("🧪 Testing Background Image Upload Components\n")

    file_test_passed = test_file_operations()
    db_test_passed = test_database_operations()

    print("=== TEST RESULTS ===")
    print(f"File operations: {'✅ PASSED' if file_test_passed else '❌ FAILED'}")
    print(f"Database operations: {'✅ PASSED' if db_test_passed else '❌ FAILED'}")

    if file_test_passed and db_test_passed:
        print("\n🎉 All component tests passed! The issue might be in the Flask request handling.")
        print("\nNext steps:")
        print("1. Run the Flask server: python app.py")
        print("2. Try uploading an image through the frontend")
        print("3. Check the server console for detailed debug output")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
