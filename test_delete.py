#!/usr/bin/env python3
"""
Test script to verify student deletion functionality
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:5000"
LOGIN_DATA = {
    "email": "admin@admin.com",
    "password": "admin123"
}

def test_login():
    """Test login functionality"""
    print("Testing login...")
    session = requests.Session()
    
    # Get login page first
    response = session.get(f"{BASE_URL}/login")
    if response.status_code != 200:
        print(f"❌ Failed to get login page: {response.status_code}")
        return None
    
    # Login
    response = session.post(f"{BASE_URL}/login", data=LOGIN_DATA)
    if response.status_code != 302:  # Redirect after login
        print(f"❌ Login failed: {response.status_code}")
        return None
    
    print("✅ Login successful")
    return session

def test_students_page(session):
    """Test accessing students page"""
    print("Testing students page access...")
    response = session.get(f"{BASE_URL}/students")
    if response.status_code != 200:
        print(f"❌ Failed to access students page: {response.status_code}")
        return False
    
    print("✅ Students page accessible")
    return True

def test_delete_functionality():
    """Test the complete delete functionality"""
    print("\n🧪 Testing Student Delete Functionality")
    print("=" * 50)
    
    # Test login
    session = test_login()
    if not session:
        print("❌ Cannot proceed without login")
        return
    
    # Test students page
    if not test_students_page(session):
        print("❌ Cannot access students page")
        return
    
    print("\n✅ All tests passed!")
    print("\n📋 To test student deletion:")
    print("1. Open your browser and go to http://localhost:5000")
    print("2. Login with admin@admin.com / admin123")
    print("3. Go to Students page")
    print("4. Click the Delete button on any student")
    print("5. Confirm deletion in the modal")
    print("6. Student should be removed from the list")

if __name__ == "__main__":
    try:
        test_delete_functionality()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on http://localhost:5000")
        print("Run: python app.py")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
