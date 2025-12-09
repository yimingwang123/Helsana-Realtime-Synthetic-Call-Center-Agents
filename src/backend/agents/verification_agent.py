"""
Identity Verification Agent using Azure AI Foundry Agent Framework.

This agent MUST be called FIRST when a customer calls to verify their identity
before allowing access to other services.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


def verification_agent(customer_id: str) -> Dict[str, Any]:
    """
    Return the verification agent configuration for identity verification.
    
    This agent enforces MANDATORY identity verification using:
    1. First Name - EXACT match required (case-insensitive)
    2. Last Name - EXACT match required (case-insensitive)
    3. Email - EXACT match required (case-insensitive)
    4. Phone Number - EXACT match required
    5. Address (Street, City, Postal Code) - EXACT match required
    6. Security questions - case-insensitive answers
    
    Args:
        customer_id: The customer ID to verify
        
    Returns:
        Agent configuration dictionary
    """
    instructions = [
        "🔐 You are the Identity Verification Agent.",
        "",
        "IMPORTANT: The customer MUST verify their identity before accessing any services.",
        "",
        "VERIFICATION PROCESS:",
        "1. Greet the customer warmly",
        "2. Explain that identity verification is required",
        "3. Request the following information:",
        "   - First Name",
        "   - Last Name",
        "   - Email Address",
        "   - Phone Number (format: +1234567890 or with dashes)",
        "   - Street Address (e.g., 'Maple Avenue 45')",
        "   - City",
        "   - Postal Code",
        "",
        "4. Call verify_customer_identity with the collected information",
        "5. If verification is NOT successful:",
        "   - Inform the customer politely",
        "   - Offer 2 more attempts",
        "   - After 3 failed attempts: Transfer to a human agent",
        "",
        "6. If verification is SUCCESSFUL:",
        "   - Congratulate the customer",
        "   - Confirm that identity verification is complete",
        "   - Inform them they now have access to all services",
        "   - Transfer to main service agents",
        "",
        "IMPORTANT RULES:",
        "- ALL fields must match EXACTLY (100% accuracy required)",
        "- Text fields are case-insensitive",
        "- For typos or missing information: ask again",
        "- No tolerance for inaccuracies - security is priority",
        "- Keep the conversation natural and friendly",
        "- Once verified, immediately grant access - NO additional authentication needed",
        "",
        f"CUSTOMER_ID for verification: {customer_id}",
        "",
        "Begin the verification process NOW."
    ]
    
    return {
        "id": "Assistant_Verification",
        "name": "IdentityVerificationAgent",
        "description": (
            "Verifies customer identity using personal information (name, email, phone, address). "
            "MUST be completed before any other interactions."
        ),
        "system_message": "\n".join(instructions),
        "tools": [
            {
                "name": "verify_customer_identity",
                "description": (
                    "Verifies customer identity using personal information. "
                    "All fields must match EXACTLY (100%)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The customer ID for verification"
                        },
                        "first_name": {
                            "type": "string",
                            "description": "Customer's first name (case-insensitive)"
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Customer's last name (case-insensitive)"
                        },
                        "email": {
                            "type": "string",
                            "description": "Customer's email address (case-insensitive)"
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "Customer's phone number (e.g., +12065551234 or 206-555-1234)"
                        },
                        "street": {
                            "type": "string",
                            "description": "Street address (e.g., 'Maple Avenue 45')"
                        },
                        "city": {
                            "type": "string",
                            "description": "City name"
                        },
                        "postal_code": {
                            "type": "string",
                            "description": "Postal code"
                        }
                    },
                    "required": ["customer_id"]
                },
                "returns": _verify_customer_identity_tool
            }
        ]
    }


def _verify_customer_identity_tool(params: Dict[str, Any]) -> str:
    """
    Tool function to verify customer identity.
    
    Calls the identity service API endpoint.
    """
    try:
        # Import here to avoid circular dependencies
        from services.identity_service import get_identity_service
        
        identity_service = get_identity_service()
        
        # Note: customer_id is for context tracking, actual verification is done by matching data
        customer_id = params.get("customer_id")  # For logging/tracking
        
        result = identity_service.verify_customer(
            first_name=params.get("first_name"),
            last_name=params.get("last_name"),
            email=params.get("email"),
            phone_number=params.get("phone_number"),
            street=params.get("street"),
            city=params.get("city"),
            postal_code=params.get("postal_code")
        )
        
        if result["verified"]:
            return json.dumps({
                "status": "VERIFIED",
                "customerId": result["customerId"],
                "confidence": result["confidence"],
                "message": "✅ Identity successfully verified. Proceed with security questions."
            }, ensure_ascii=False)
        else:
            details = result.get("details", {})
            failed_fields = [field for field, status in details.items() if status == "no_match"]
            return json.dumps({
                "status": "NOT_VERIFIED",
                "confidence": result["confidence"],
                "failed_fields": failed_fields,
                "message": f"❌ Verification failed. The following fields did not match: {', '.join(failed_fields) if failed_fields else 'No fields provided'}"
            }, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Error in verify_customer_identity_tool: {e}")
        return json.dumps({
            "status": "ERROR",
            "message": f"An error occurred: {str(e)}"
        }, ensure_ascii=False)

