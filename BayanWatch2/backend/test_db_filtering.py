#!/usr/bin/env python3
"""
Simple test for database access code filtering
"""

from db_config import get_all_complaints

print("Testing database access code filtering...")
print("All complaints:", len(get_all_complaints()))
print("ADMIN123 complaints:", len(get_all_complaints('ADMIN123')))
print("BARANGAY456 complaints:", len(get_all_complaints('BARANGAY456')))
print("INVALID complaints:", len(get_all_complaints('INVALID')))
print("✅ Database filtering test completed!")
