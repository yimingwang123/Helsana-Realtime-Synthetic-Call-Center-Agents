"""
Test script for Identity Verification and Authentication API

This script tests all three endpoints:
1. POST /api/identity/verifyCustomer
2. GET /api/identity/security-questions
3. POST /api/identity/security-answers

Run this script after starting the backend server:
    python test_identity_verification.py
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_response(response: requests.Response):
    """Pretty print API response."""
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_verify_customer():
    """Test customer verification endpoint."""
    print_section("TEST 1: Customer Verification")
    
    # Test case 1: Successful verification with all fields
    print("🔹 Test Case 1.1: Full verification (all fields)")
    payload = {
        "name": "Hans Müller",
        "versicherungsnummer": "CH-7601234567890",
        "geburtstag": "1985-03-15",
        "adresse": "Bahnhofstrasse 12, 8001 Zürich"
    }
    
    print(f"Request: POST {BASE_URL}/api/identity/verifyCustomer")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f"{BASE_URL}/api/identity/verifyCustomer", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        result = response.json()
        if result["verified"]:
            print(f"✅ SUCCESS: Customer verified with {result['confidence']*100:.1f}% confidence")
            customer_id = result["customerId"]
            return customer_id
        else:
            print("❌ FAILED: Customer not verified")
            return None
    else:
        print(f"❌ ERROR: HTTP {response.status_code}")
        return None
    
    # Test case 2: Partial information (insurance number only)
    print("\n🔹 Test Case 1.2: Partial verification (insurance number only)")
    payload = {
        "versicherungsnummer": "CH-7609876543210"
    }
    
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    response = requests.post(f"{BASE_URL}/api/identity/verifyCustomer", json=payload)
    print_response(response)
    
    # Test case 3: Failed verification (wrong data)
    print("\n🔹 Test Case 1.3: Failed verification (incorrect data)")
    payload = {
        "name": "Wrong Name",
        "versicherungsnummer": "CH-0000000000000"
    }
    
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    response = requests.post(f"{BASE_URL}/api/identity/verifyCustomer", json=payload)
    print_response(response)


def test_get_security_questions(customer_id: str):
    """Test security questions retrieval endpoint."""
    print_section("TEST 2: Get Security Questions")
    
    print(f"🔹 Test Case 2.1: Get 2 security questions for {customer_id}")
    url = f"{BASE_URL}/api/identity/security-questions"
    params = {"customerId": customer_id, "count": 2}
    
    print(f"Request: GET {url}")
    print(f"Params: {params}")
    
    response = requests.get(url, params=params)
    print_response(response)
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            questions = result["questions"]
            print(f"✅ SUCCESS: Retrieved {len(questions)} questions")
            return questions
        else:
            print("❌ FAILED: Could not retrieve questions")
            return []
    else:
        print(f"❌ ERROR: HTTP {response.status_code}")
        return []
    
    # Test case 2: Invalid customer ID
    print("\n🔹 Test Case 2.2: Get questions for non-existent customer")
    params = {"customerId": "INVALID_ID", "count": 2}
    print(f"Params: {params}")
    response = requests.get(url, params=params)
    print_response(response)


def test_verify_security_answers(customer_id: str, questions: list):
    """Test security answers verification endpoint."""
    print_section("TEST 3: Verify Security Answers")
    
    # For testing, we'll use known correct answers for CUST001
    # In production, these would come from user input
    correct_answers_map = {
        "SQ001": "Bern",
        "SQ002": "Fischer",
        "SQ003": "Rex"
    }
    
    # Test case 1: Correct answers
    print(f"🔹 Test Case 3.1: Verify correct answers for {customer_id}")
    
    answers = [
        {"questionId": q["questionId"], "answer": correct_answers_map.get(q["questionId"], "")}
        for q in questions
    ]
    
    payload = {
        "customerId": customer_id,
        "answers": answers
    }
    
    print(f"Request: POST {BASE_URL}/api/identity/security-answers")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f"{BASE_URL}/api/identity/security-answers", json=payload)
    print_response(response)
    
    if response.status_code == 200:
        result = response.json()
        if result["authenticated"]:
            print(f"✅ SUCCESS: Authentication successful! Correct: {result['correctCount']}/{result['totalCount']}")
        else:
            print(f"❌ FAILED: Authentication failed. Correct: {result['correctCount']}/{result['totalCount']}")
    else:
        print(f"❌ ERROR: HTTP {response.status_code}")
    
    # Test case 2: Incorrect answers
    print("\n🔹 Test Case 3.2: Verify incorrect answers")
    
    answers = [
        {"questionId": q["questionId"], "answer": "Wrong Answer"}
        for q in questions
    ]
    
    payload = {
        "customerId": customer_id,
        "answers": answers
    }
    
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    response = requests.post(f"{BASE_URL}/api/identity/security-answers", json=payload)
    print_response(response)
    
    # Test case 3: Fuzzy matching (close but not exact)
    print("\n🔹 Test Case 3.3: Verify with fuzzy matching (similar answers)")
    
    answers = [
        {"questionId": "SQ001", "answer": "bern"},  # lowercase
    ]
    
    payload = {
        "customerId": customer_id,
        "answers": answers
    }
    
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    response = requests.post(f"{BASE_URL}/api/identity/security-answers", json=payload)
    print_response(response)


def test_complete_flow():
    """Test complete verification and authentication flow."""
    print_section("COMPLETE FLOW TEST: Verification → Questions → Authentication")
    
    print("Step 1: Verify customer identity")
    customer_id = test_verify_customer()
    
    if not customer_id:
        print("\n❌ Flow stopped: Customer verification failed")
        return
    
    print(f"\n✅ Customer verified: {customer_id}")
    
    print("\nStep 2: Get security questions")
    questions = test_get_security_questions(customer_id)
    
    if not questions:
        print("\n❌ Flow stopped: Could not retrieve security questions")
        return
    
    print(f"\n✅ Retrieved {len(questions)} security questions")
    
    print("\nStep 3: Verify security answers")
    test_verify_security_answers(customer_id, questions)
    
    print("\n" + "="*70)
    print("  COMPLETE FLOW TEST FINISHED")
    print("="*70)


def main():
    """Main test runner."""
    print("\n" + "🔐"*35)
    print(" "*15 + "IDENTITY VERIFICATION & AUTHENTICATION API TESTS")
    print("🔐"*35)
    
    print("\n⚠️  Make sure the backend server is running on http://localhost:8000")
    print("   Start with: uvicorn main:app --reload\n")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running\n")
        else:
            print("❌ Backend server returned unexpected status\n")
            return
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend server")
        print("   Please start the server with: uvicorn main:app --reload")
        return
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return
    
    # Run individual tests
    print("\n" + "📋"*35)
    print(" "*20 + "RUNNING INDIVIDUAL TESTS")
    print("📋"*35)
    
    # Test 1: Verify Customer
    customer_id = test_verify_customer()
    
    if customer_id:
        # Test 2: Get Security Questions
        questions = test_get_security_questions(customer_id)
        
        if questions:
            # Test 3: Verify Security Answers
            test_verify_security_answers(customer_id, questions)
    
    # Run complete flow test
    print("\n\n" + "🔄"*35)
    print(" "*22 + "COMPLETE FLOW TEST")
    print("🔄"*35)
    
    # Wait for user
    input("\nPress Enter to run complete flow test...")
    
    test_complete_flow()
    
    print("\n\n" + "✅"*35)
    print(" "*25 + "ALL TESTS COMPLETED")
    print("✅"*35 + "\n")


if __name__ == "__main__":
    main()
