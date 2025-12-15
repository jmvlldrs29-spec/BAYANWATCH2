#!/usr/bin/env python3
"""
Test script to diagnose Flask import issues
"""

print("Testing Flask import...")

try:
    import flask
    print(f"✅ Flask imported successfully: {flask.__version__}")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")
    print("Please install Flask with: pip install flask")

print("\nTesting other imports...")

try:
    import mysql.connector
    print(f"✅ mysql-connector imported successfully: {mysql.connector.__version__}")
except ImportError as e:
    print(f"❌ mysql-connector import failed: {e}")

try:
    import bcrypt
    print(f"✅ bcrypt imported successfully: {bcrypt.__version__}")
except ImportError as e:
    print(f"❌ bcrypt import failed: {e}")

print("\nTesting app.py imports...")

try:
    from app import app
    print("✅ app.py imported successfully")
except ImportError as e:
    print(f"❌ app.py import failed: {e}")

print("\nDone.")
