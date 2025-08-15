#!/usr/bin/env python3
"""
Test script for EPIC API simulation
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_epic_api():
    """Test the EPIC API simulation endpoints"""
    
    print("Testing EPIC API Simulation...")
    print("=" * 50)
    
    # Test 1: Get patient data
    print("\n1. Testing Patient endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/epic/Patient/MRN001")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Patient data retrieved successfully")
            print(f"  Total entries: {data.get('total', 0)}")
            if data.get('entry'):
                patient = data['entry'][0]['resource']
                print(f"  Patient name: {patient.get('name', [{}])[0].get('text', 'Unknown')}")
        else:
            print(f"✗ Failed to get patient data: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing patient endpoint: {e}")
    
    # Test 2: Get patient observations (lab results)
    print("\n2. Testing Observation endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/epic/Observation?patient=MRN001")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Observations retrieved successfully")
            print(f"  Total observations: {data.get('total', 0)}")
        else:
            print(f"✗ Failed to get observations: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing observation endpoint: {e}")
    
    # Test 3: Get patient documents
    print("\n3. Testing DocumentReference endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/epic/DocumentReference?patient=MRN001")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Documents retrieved successfully")
            print(f"  Total documents: {data.get('total', 0)}")
        else:
            print(f"✗ Failed to get documents: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing document endpoint: {e}")
    
    # Test 4: Get patient conditions
    print("\n4. Testing Condition endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/epic/Condition?patient=MRN001")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Conditions retrieved successfully")
            print(f"  Total conditions: {data.get('total', 0)}")
        else:
            print(f"✗ Failed to get conditions: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing condition endpoint: {e}")
    
    # Test 5: Get patient procedures
    print("\n5. Testing Procedure endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/epic/Procedure?patient=MRN001")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Procedures retrieved successfully")
            print(f"  Total procedures: {data.get('total', 0)}")
        else:
            print(f"✗ Failed to get procedures: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing procedure endpoint: {e}")
    
    # Test 6: Get family history
    print("\n6. Testing FamilyMemberHistory endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/epic/FamilyMemberHistory?patient=MRN001")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Family history retrieved successfully")
            print(f"  Total family members: {data.get('total', 0)}")
        else:
            print(f"✗ Failed to get family history: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing family history endpoint: {e}")
    
    # Test 7: Search patients
    print("\n7. Testing Patient search...")
    try:
        response = requests.get(f"{BASE_URL}/api/epic/Patient?name=John")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Patient search successful")
            print(f"  Total patients found: {data.get('total', 0)}")
        else:
            print(f"✗ Failed to search patients: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing patient search: {e}")
    
    # Test 8: Legacy endpoints
    print("\n8. Testing Legacy endpoints...")
    try:
        response = requests.get(f"{BASE_URL}/api/ehr/patient/MRN001")
        if response.status_code == 200:
            print(f"✓ Legacy patient endpoint works")
        else:
            print(f"✗ Legacy patient endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing legacy endpoint: {e}")
    
    print("\n" + "=" * 50)
    print("EPIC API Simulation test completed!")

def test_database_reset():
    """Test database reset functionality"""
    print("\nTesting Database Reset...")
    print("=" * 30)
    
    try:
        response = requests.post(f"{BASE_URL}/api/reset-database")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ Database reset successful")
                print(f"  Message: {data.get('message', '')}")
            else:
                print(f"✗ Database reset failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"✗ Database reset request failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing database reset: {e}")

if __name__ == "__main__":
    print("EPIC API Simulation Test Suite")
    print("Make sure the Flask app is running on http://localhost:5000")
    print()
    
    # Wait a moment for the server to be ready
    time.sleep(2)
    
    # Test database reset first
    test_database_reset()
    
    # Wait for database to be ready
    time.sleep(3)
    
    # Test EPIC API endpoints
    test_epic_api()
