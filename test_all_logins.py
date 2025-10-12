#!/usr/bin/env python
"""
Test Login for All User Roles
This script demonstrates logging in and accessing profiles for all 6 user types
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/authentication"

# Test credentials for all user types
USER_CREDENTIALS = {
    "citizen": {
        "email": "citizen@example.com",
        "password": "SecurePass123!"
    },
    "advocate": {
        "email": "advocate@example.com",
        "password": "SecurePass123!"
    },
    "lawyer": {
        "email": "lawyer@example.com",
        "password": "SecurePass123!"
    },
    "paralegal": {
        "email": "paralegal@example.com",
        "password": "SecurePass123!"
    },
    "law_firm": {
        "email": "info@smithlawfirm.co.tz",
        "password": "SecurePass123!"
    },
    "law_student": {
        "email": "student@udsm.ac.tz",
        "password": "SecurePass123!"
    }
}


def login(email, password):
    """Login and return access token"""
    try:
        response = requests.post(
            f"{BASE_URL}/login/",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            return tokens['access'], tokens['refresh']
        else:
            print(f"  ✗ Login failed: {response.json()}")
            return None, None
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return None, None


def get_profile(access_token):
    """Get user profile using access token"""
    try:
        response = requests.get(
            f"{BASE_URL}/profile/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ✗ Failed to get profile: {response.json()}")
            return None
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return None


def display_profile_summary(profile, role_name):
    """Display a summary of the profile based on role"""
    print(f"\n  Profile Summary for {role_name.upper()}:")
    print(f"  {'='*50}")
    
    # Common fields
    print(f"  ID: {profile.get('id')}")
    print(f"  Email: {profile.get('email')}")
    
    # Role-specific fields
    if role_name == 'law_firm':
        print(f"  Firm Name: {profile.get('firm_name')}")
        print(f"  Number of Lawyers: {profile.get('number_of_lawyers')}")
        print(f"  Year Established: {profile.get('year_established')}")
    else:
        print(f"  Name: {profile.get('first_name')} {profile.get('last_name')}")
        if profile.get('date_of_birth'):
            print(f"  Date of Birth: {profile.get('date_of_birth')}")
    
    # User role
    user_role = profile.get('user_role', {})
    print(f"  Role: {user_role.get('get_role_display', 'N/A')}")
    
    # Status
    print(f"  Active: {profile.get('is_active')}")
    print(f"  Verified: {profile.get('is_verified')}")
    
    # Role-specific additional info
    if role_name == 'advocate':
        print(f"  Roll Number: {profile.get('roll_number')}")
        print(f"  Practice Status: {profile.get('practice_status')}")
        print(f"  Specializations: {len(profile.get('specializations', []))} areas")
    elif role_name == 'lawyer':
        print(f"  Bar Number: {profile.get('bar_membership_number')}")
        print(f"  Experience: {profile.get('years_of_experience')} years")
        place_of_work = profile.get('place_of_work', {})
        print(f"  Place of Work: {place_of_work.get('name_en', 'N/A')}")
    elif role_name == 'paralegal':
        print(f"  Experience: {profile.get('years_of_experience')} years")
        place_of_work = profile.get('place_of_work', {})
        print(f"  Place of Work: {place_of_work.get('name_en', 'N/A')}")
    elif role_name == 'law_student':
        print(f"  University: {profile.get('university_name')}")
        academic_role = profile.get('academic_role', {})
        print(f"  Academic Role: {academic_role.get('name_en', 'N/A')}")
        if profile.get('year_of_study'):
            print(f"  Year of Study: {profile.get('year_of_study')}")
    elif role_name == 'citizen':
        if profile.get('id_number'):
            print(f"  ID Number: {profile.get('id_number')}")
    
    print(f"  {'='*50}")


def test_login_for_role(role_name, credentials):
    """Test login and profile retrieval for a specific role"""
    print(f"\n{'='*60}")
    print(f"Testing {role_name.upper()} Login")
    print(f"{'='*60}")
    print(f"Email: {credentials['email']}")
    
    # Step 1: Login
    print("\n1. Logging in...")
    access_token, refresh_token = login(credentials['email'], credentials['password'])
    
    if not access_token:
        print(f"  ✗ Login failed for {role_name}")
        return False
    
    print(f"  ✓ Login successful")
    print(f"  Access Token: {access_token[:50]}...")
    
    # Step 2: Get Profile
    print("\n2. Fetching profile...")
    profile = get_profile(access_token)
    
    if not profile:
        print(f"  ✗ Failed to get profile for {role_name}")
        return False
    
    print(f"  ✓ Profile retrieved successfully")
    
    # Step 3: Display Summary
    display_profile_summary(profile, role_name)
    
    return True


def main():
    print("\n" + "="*60)
    print("POLA API - Login Test for All User Roles")
    print("="*60)
    
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
    
    # Test all user roles
    results = {}
    for role_name, credentials in USER_CREDENTIALS.items():
        results[role_name] = test_login_for_role(role_name, credentials)
    
    # Summary
    print("\n" + "="*60)
    print("LOGIN TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    
    for role_name, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {role_name.replace('_', ' ').title()}")
    
    print(f"\nTotal: {successful}/{total} successful logins")
    
    if successful == total:
        print("\n✓ All user roles can login and access their profiles!")
        print("\nNext steps:")
        print("1. Test token refresh: POST /api/v1/authentication/token/refresh/")
        print("2. Test profile updates: PATCH /api/v1/authentication/profile/")
        print("3. Access Swagger UI: http://localhost:8000/swagger/")
    else:
        print("\n⚠ Some logins failed. Possible reasons:")
        print("1. Users not registered - Run: python test_registrations.py")
        print("2. Incorrect credentials")
        print("3. Server not running properly")


if __name__ == "__main__":
    main()
