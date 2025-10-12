#!/usr/bin/env python
"""
Test User Registration Script for Pola API
This script demonstrates how to register all 6 user types
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/authentication"

# Sample registration data for all user types
REGISTRATION_DATA = {
    "citizen": {
        "email": "citizen@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-15",
        "agreed_to_Terms": True,
        "user_role": 6,
        "gender": "M",
        "phone_number": "+255712345678",
        "id_number": "19900115-12345-00001-12"
    },
    "advocate": {
        "email": "advocate@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1985-05-20",
        "agreed_to_Terms": True,
        "user_role": 2,
        "gender": "F",
        "roll_number": "ADV-2010-12345",
        "practice_status": "practising",
        "year_established": 2010,
        "phone_number": "+255712345679",
        "website": "https://janesmith-advocate.co.tz",
        "region": 1,
        "district": 2,
        "office_address": "123 Legal Street, Ilala, Dar es Salaam",
        "operating_regions": [1, 2],
        "specializations": [1, 2, 3]
    },
    "lawyer": {
        "email": "lawyer@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "Michael",
        "last_name": "Johnson",
        "date_of_birth": "1988-03-10",
        "agreed_to_Terms": True,
        "user_role": 1,
        "gender": "M",
        "bar_membership_number": "BAR-2015-67890",
        "years_of_experience": 8,
        "place_of_work": 1,
        "phone_number": "+255712345680",
        "region": 1,
        "district": 2,
        "office_address": "456 Corporate Plaza, Kinondoni, Dar es Salaam",
        "operating_regions": [1, 2],
        "operating_districts": [2, 3, 4],
        "specializations": [1, 4, 7]
    },
    "paralegal": {
        "email": "paralegal@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "Sarah",
        "last_name": "Williams",
        "date_of_birth": "1992-07-15",
        "agreed_to_Terms": True,
        "user_role": 3,
        "gender": "F",
        "years_of_experience": 5,
        "place_of_work": 2,
        "phone_number": "+255712345681",
        "region": 1,
        "district": 2,
        "office_address": "789 Legal Aid Center, Temeke, Dar es Salaam",
        "operating_regions": [1],
        "operating_districts": [2, 3]
    },
    "law_firm": {
        "email": "info@smithlawfirm.co.tz",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "agreed_to_Terms": True,
        "user_role": 5,
        "firm_name": "Smith & Associates Law Firm",
        "number_of_lawyers": 15,
        "year_established": 2000,
        "phone_number": "+255712345682",
        "website": "https://smithlaw.co.tz",
        "region": 1,
        "district": 2,
        "office_address": "456 Corporate Plaza, 5th Floor, Kinondoni, Dar es Salaam",
        "specializations": [1, 2, 3, 4, 5]
    },
    "law_student": {
        "email": "student@udsm.ac.tz",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "Alice",
        "last_name": "Brown",
        "date_of_birth": "2000-08-15",
        "agreed_to_Terms": True,
        "user_role": 4,
        "gender": "F",
        "university_name": "University of Dar es Salaam",
        "academic_role": 1,
        "year_of_study": 3,
        "phone_number": "+255712345683"
    }
}


def register_user(user_type, data):
    """Register a user with the given data"""
    print(f"\n{'='*50}")
    print(f"Registering {user_type.upper()}...")
    print(f"{'='*50}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/register/",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✓ SUCCESS: {user_type.capitalize()} registered")
            print(f"  Email: {result['user']['email']}")
            print(f"  Name: {result['user']['first_name']} {result['user']['last_name']}")
            print(f"  Role: {result['user']['user_role']}")
            print(f"  ID: {result['user']['id']}")
            return True
        else:
            print(f"✗ FAILED: {user_type.capitalize()} registration failed")
            print(f"  Status Code: {response.status_code}")
            print(f"  Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False


def main():
    print("\n" + "="*50)
    print("POLA API - User Registration Test Script")
    print("="*50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/roles/")
        if response.status_code != 200:
            print("\n⚠ WARNING: API server may not be running properly")
            print(f"Please ensure the server is running at {BASE_URL}")
            return
    except requests.exceptions.ConnectionError:
        print(f"\n✗ ERROR: Cannot connect to {BASE_URL}")
        print("Please ensure the Django server is running:")
        print("  python manage.py runserver")
        return
    
    # Register all user types
    results = {}
    for user_type, data in REGISTRATION_DATA.items():
        results[user_type] = register_user(user_type, data)
    
    # Summary
    print("\n" + "="*50)
    print("REGISTRATION SUMMARY")
    print("="*50)
    
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    
    for user_type, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {user_type.capitalize()}")
    
    print(f"\nTotal: {successful}/{total} successful registrations")
    
    if successful == total:
        print("\n✓ All user types registered successfully!")
        print("\nNext steps:")
        print(f"1. Login: POST {BASE_URL}/login/")
        print(f"2. View profile: GET {BASE_URL}/profile/ (with Bearer token)")
        print("3. Access Swagger UI: http://localhost:8000/swagger/")
    else:
        print("\n⚠ Some registrations failed. Check the errors above.")


if __name__ == "__main__":
    main()
