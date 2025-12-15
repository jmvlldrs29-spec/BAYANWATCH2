#!/usr/bin/env python3
"""
Simple test to verify per-access-code background functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db_config import get_barangay_background

print("🧪 Testing Per-Access-Code Background Functionality")
print("="*60)

# Test background retrieval for different access codes
access_codes = ["ADMIN123", "BARANGAY456", "OFFICIAL789", "INVALID123"]

for access_code in access_codes:
    background = get_barangay_background(access_code)
    status = "✅" if background else "❌"
    print(f"{status} {access_code}: {background or 'No background found'}")

print("\n" + "="*60)
print("🎉 Background functionality test completed!")
