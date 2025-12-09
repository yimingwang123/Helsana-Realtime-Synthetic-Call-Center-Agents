"""Quick test to demonstrate 100% exact matching for verification."""

import sys
sys.path.insert(0, '.')

from services.identity_service import IdentityService

def test_exact_matching():
    """Test that verification requires 100% exact match."""
    service = IdentityService()
    
    print("="*70)
    print("IDENTITY VERIFICATION - 100% EXACT MATCH TESTS")
    print("="*70)
    
    # Test 1: Perfect match (all fields)
    print("\n✅ Test 1: Perfect match (all fields)")
    result = service.verify_customer(
        name="Hans Müller",
        versicherungsnummer="CH-7601234567890",
        geburtstag="1985-03-15",
        adresse="Bahnhofstrasse 12, 8001 Zürich"
    )
    print(f"Result: {'VERIFIED' if result['verified'] else 'NOT VERIFIED'}")
    print(f"Confidence: {result['confidence']:.1%}")
    
    # Test 2: Case variations (should work)
    print("\n✅ Test 2: Case variations (should still match)")
    result = service.verify_customer(
        name="hans müller",
        versicherungsnummer="ch-7601234567890",
        adresse="BAHNHOFSTRASSE 12, 8001 ZÜRICH"
    )
    print(f"Result: {'VERIFIED' if result['verified'] else 'NOT VERIFIED'}")
    print(f"Confidence: {result['confidence']:.1%}")
    
    # Test 3: Typo in name (should fail)
    print("\n❌ Test 3: Typo in name (should fail)")
    result = service.verify_customer(
        name="Hans Mueller",  # Mueller instead of Müller
        versicherungsnummer="CH-7601234567890"
    )
    print(f"Result: {'VERIFIED' if result['verified'] else 'NOT VERIFIED'}")
    print(f"Confidence: {result['confidence']:.1%}")
    
    # Test 4: Wrong insurance number (should fail)
    print("\n❌ Test 4: Wrong insurance number (should fail)")
    result = service.verify_customer(
        name="Hans Müller",
        versicherungsnummer="CH-9999999999999"
    )
    print(f"Result: {'VERIFIED' if result['verified'] else 'NOT VERIFIED'}")
    print(f"Confidence: {result['confidence']:.1%}")
    
    # Test 5: Security answers (case-insensitive)
    print("\n✅ Test 5: Security answers - exact match (case-insensitive)")
    result = service.verify_security_answers(
        customer_id="CUST001",
        answers=[
            {"questionId": "SQ001", "answer": "Bern"},
            {"questionId": "SQ002", "answer": "Fischer"}
        ]
    )
    print(f"Result: {'AUTHENTICATED' if result['authenticated'] else 'NOT AUTHENTICATED'}")
    print(f"Correct: {result['correctCount']}/{result['totalCount']}")
    
    # Test 6: Security answers with case variation (should work)
    print("\n✅ Test 6: Security answers - case variations (should work)")
    result = service.verify_security_answers(
        customer_id="CUST001",
        answers=[
            {"questionId": "SQ001", "answer": "bern"},  # lowercase
            {"questionId": "SQ002", "answer": "FISCHER"}  # uppercase
        ]
    )
    print(f"Result: {'AUTHENTICATED' if result['authenticated'] else 'NOT AUTHENTICATED'}")
    print(f"Correct: {result['correctCount']}/{result['totalCount']}")
    
    # Test 7: Security answers - partial answer (should fail)
    print("\n❌ Test 7: Security answers - partial answer (should fail)")
    result = service.verify_security_answers(
        customer_id="CUST001",
        answers=[
            {"questionId": "SQ001", "answer": "Ber"},  # Partial: "Ber" instead of "Bern"
        ]
    )
    print(f"Result: {'AUTHENTICATED' if result['authenticated'] else 'NOT AUTHENTICATED'}")
    print(f"Correct: {result['correctCount']}/{result['totalCount']}")
    
    print("\n" + "="*70)
    print("TESTS COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_exact_matching()
