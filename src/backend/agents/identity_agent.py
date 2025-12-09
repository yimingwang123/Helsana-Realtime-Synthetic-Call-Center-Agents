"""Identity verification and authentication agent using Azure AI Foundry."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

# Backend API endpoint (local or through APIM)
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")


def verify_customer_identity(params: Dict[str, Any]) -> str:
    """
    Verify customer identity using backend API.
    
    This tool calls the backend /api/identity/verifyCustomer endpoint
    to verify a customer's identity based on provided information.
    
    Parameters
    ----------
    params : Dict[str, Any]
        Dictionary containing:
        - first_name: str (optional) - Customer's first name
        - last_name: str (optional) - Customer's last name
        - email: str (optional) - Customer's email address
        - phone_number: str (optional) - Customer's phone number
        - street: str (optional) - Street address
        - city: str (optional) - City
        - postal_code: str (optional) - Postal code
        
    Returns
    -------
    str
        A formatted string describing the verification result.
    """
    logger.info(
        f"[Identity_Agent][Verify] Verifying customer identity:\n"
        f"  First Name: {params.get('first_name')}\n"
        f"  Last Name: {params.get('last_name')}\n"
        f"  Email: {params.get('email')}\n"
        f"  Phone: {params.get('phone_number')}\n"
        f"  Street: {params.get('street')}\n"
        f"  City: {params.get('city')}\n"
        f"  Postal Code: {params.get('postal_code')}"
    )
    
    try:
        url = f"{BACKEND_API_URL}/api/identity/verifyCustomer"
        response = requests.post(url, json=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("verified"):
            customer_data = result.get("customerData", {})
            logger.info(f"[Identity_Agent][Verify] ✅ Customer verified: {result.get('customerId')}")
            return (
                f"✅ Customer successfully verified!\n"
                f"Customer ID: {result.get('customerId')}\n"
                f"Name: {customer_data.get('first_name')} {customer_data.get('last_name')}\n"
                f"Confidence: {result.get('confidence') * 100:.1f}%\n"
                f"{result.get('message')}"
            )
        else:
            logger.warning(f"[Identity_Agent][Verify] ❌ Verification failed")
            return (
                f"❌ Verification failed.\n"
                f"Confidence: {result.get('confidence') * 100:.1f}%\n"
                f"{result.get('message')}\n"
                f"Please check the information and try again."
            )
            
    except requests.Timeout:
        logger.error("[Identity_Agent][Verify] Request timed out")
        return "❌ Error: Verification request timed out. Please try again."
        
    except requests.RequestException as e:
        logger.error(f"[Identity_Agent][Verify] API error: {e}", exc_info=True)
        return f"❌ Verification error: {str(e)}"


def get_security_questions(params: Dict[str, Any]) -> str:
    """
    Get security questions for a customer.
    
    This tool retrieves random security questions (Sicherheitsfragen)
    for a verified customer from the backend API.
    
    Parameters
    ----------
    params : Dict[str, Any]
        Dictionary containing:
        - customerId: str (required) - Customer ID (e.g., CUST001)
        - count: int (optional) - Number of questions (default: 2, max: 3)
        
    Returns
    -------
    str
        A formatted string with the security questions.
    """
    customer_id = params.get("customerId")
    count = params.get("count", 2)
    
    logger.info(f"[Identity_Agent][Questions] Getting {count} security questions for {customer_id}")
    
    if not customer_id:
        return "❌ Fehler: Kunden-ID ist erforderlich."
    
    try:
        url = f"{BACKEND_API_URL}/api/identity/security-questions"
        response = requests.get(
            url,
            params={"customerId": customer_id, "count": count},
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success"):
            questions = result.get("questions", [])
            logger.info(f"[Identity_Agent][Questions] Retrieved {len(questions)} questions")
            
            if not questions:
                return "❌ Keine Sicherheitsfragen für diesen Kunden verfügbar."
            
            # Format questions
            questions_text = "\n".join(
                f"{i+1}. {q['question']} (ID: {q['questionId']})"
                for i, q in enumerate(questions)
            )
            
            return (
                f"📋 Sicherheitsfragen für Kunden {customer_id}:\n\n"
                f"{questions_text}\n\n"
                f"Bitte beantworten Sie die Fragen zur Authentifizierung."
            )
        else:
            logger.warning(f"[Identity_Agent][Questions] Failed: {result.get('message')}")
            return f"❌ {result.get('message')}"
            
    except requests.Timeout:
        logger.error("[Identity_Agent][Questions] Request timed out")
        return "❌ Fehler: Zeitüberschreitung beim Abrufen der Fragen. Bitte versuchen Sie es erneut."
        
    except requests.RequestException as e:
        logger.error(f"[Identity_Agent][Questions] API error: {e}", exc_info=True)
        return f"❌ Fehler beim Abrufen der Fragen: {str(e)}"


def verify_security_answers(params: Dict[str, Any]) -> str:
    """
    Verify customer's security question answers.
    
    This tool checks if the customer's answers to security questions
    are correct, completing the authentication process.
    
    Parameters
    ----------
    params : Dict[str, Any]
        Dictionary containing:
        - customerId: str (required) - Customer ID
        - answers: list (required) - List of {"questionId": "...", "answer": "..."}
        
    Returns
    -------
    str
        A formatted string describing the authentication result.
    """
    customer_id = params.get("customerId")
    answers = params.get("answers", [])
    
    logger.info(f"[Identity_Agent][Auth] Verifying {len(answers)} answers for {customer_id}")
    
    if not customer_id:
        return "❌ Fehler: Kunden-ID ist erforderlich."
    
    if not answers:
        return "❌ Fehler: Keine Antworten bereitgestellt."
    
    try:
        url = f"{BACKEND_API_URL}/api/identity/security-answers"
        payload = {
            "customerId": customer_id,
            "answers": answers
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("authenticated"):
            logger.info(f"[Identity_Agent][Auth] ✅ Authentication successful for {customer_id}")
            return (
                f"✅ Authentifizierung erfolgreich!\n"
                f"Kunde {customer_id} wurde erfolgreich authentifiziert.\n"
                f"Alle {result.get('correctCount')}/{result.get('totalCount')} Antworten sind korrekt.\n"
                f"Sie können nun mit der Bearbeitung Ihrer Anfrage fortfahren."
            )
        else:
            logger.warning(
                f"[Identity_Agent][Auth] ❌ Authentication failed for {customer_id}. "
                f"Correct: {result.get('correctCount')}/{result.get('totalCount')}"
            )
            return (
                f"❌ Authentifizierung fehlgeschlagen.\n"
                f"Nur {result.get('correctCount')}/{result.get('totalCount')} Antworten sind korrekt.\n"
                f"{result.get('message')}\n"
                f"Bitte überprüfen Sie Ihre Antworten und versuchen Sie es erneut."
            )
            
    except requests.Timeout:
        logger.error("[Identity_Agent][Auth] Request timed out")
        return "❌ Fehler: Zeitüberschreitung bei der Authentifizierung. Bitte versuchen Sie es erneut."
        
    except requests.RequestException as e:
        logger.error(f"[Identity_Agent][Auth] API error: {e}", exc_info=True)
        return f"❌ Fehler bei der Authentifizierung: {str(e)}"


# Azure AI Foundry Agent Configuration
identity_agent: Dict[str, Any] = {
    "id": "Assistant_Identity_Verification",
    "name": "Identity & Authentication Agent",
    "description": (
        "Handles customer identity verification and authentication using "
        "personal information (name, email, phone, address) and security questions."
    ),
    "system_message": (
        "You are an identity verification and authentication specialist.\n\n"
        "Your responsibilities:\n"
        "1. **Verification**: Verify customer identity using:\n"
        "   - First Name (EXACT match required, case-insensitive)\n"
        "   - Last Name (EXACT match required, case-insensitive)\n"
        "   - Email (EXACT match required, case-insensitive)\n"
        "   - Phone Number (EXACT match required)\n"
        "   - Address: Street, City, Postal Code (EXACT match required, case-insensitive)\n\n"
        "2. **Authentication**: After verification, authenticate using:\n"
        "   - Retrieve 2-3 security questions for the customer\n"
        "   - Verify the customer's answers (case-insensitive, but must match exactly)\n\n"
        "**CRITICAL INPUT FORMAT REQUIREMENTS:**\n"
        "- First Name: e.g., 'Wendy'\n"
        "- Last Name: e.g., 'Taylor'\n"
        "- Email: e.g., 'wendy.taylor@example.com'\n"
        "- Phone Number: e.g., '+12065551234' or '206-555-1234'\n"
        "- Street: e.g., 'Maple Avenue 45'\n"
        "- City: e.g., 'Seattle'\n"
        "- Postal Code: e.g., '98109'\n"
        "- Security Answers: Single word or short phrase (case-insensitive)\n\n"
        "**IMPORTANT: ALL verification fields must match EXACTLY (100%). No partial matches accepted.**\n\n"
        "**Process Flow:**\n"
        "- Step 1: Ask customer for verification details\n"
        "- Step 2: Use verify_customer_identity tool to verify (requires 100% exact match)\n"
        "- Step 3: If verified, use get_security_questions tool to retrieve questions\n"
        "- Step 4: Ask customer to answer the security questions\n"
        "- Step 5: Use verify_security_answers tool to authenticate\n"
        "- Step 6: Confirm successful authentication or ask to retry\n\n"
        "**Important Guidelines:**\n"
        "- Always be polite and professional\n"
        "- Keep responses concise (this is voice interaction)\n"
        "- Handle sensitive data with care\n"
        "- If verification fails, remind customer that ALL fields must match EXACTLY\n"
        "- If authentication fails, allow customer to retry\n"
    ),
    "tools": [
        {
            "name": "verify_customer_identity",
            "description": (
                "Verify customer identity using personal information. ALL provided fields must match "
                "EXACTLY (100% match required, case-insensitive for text fields). "
                "Returns verification result with customer ID if successful."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "Customer's first name (case-insensitive). Must match exactly.",
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Customer's last name (case-insensitive). Must match exactly.",
                    },
                    "email": {
                        "type": "string",
                        "description": "Customer's email address (case-insensitive). Must match exactly.",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Customer's phone number. Format: +1234567890 or with dashes/spaces. Must match exactly.",
                    },
                    "street": {
                        "type": "string",
                        "description": "Street address (case-insensitive). Example: 'Maple Avenue 45'. Must match exactly.",
                    },
                    "city": {
                        "type": "string",
                        "description": "City name (case-insensitive). Example: 'Seattle'. Must match exactly.",
                    },
                    "postal_code": {
                        "type": "string",
                        "description": "Postal code. Example: '98109'. Must match exactly.",
                    },
                },
                "required": [],
            },
            "returns": verify_customer_identity,
        },
        {
            "name": "get_security_questions",
            "description": (
                "Retrieve security questions (Sicherheitsfragen) for a verified customer. "
                "Returns 2-3 random questions that the customer must answer for authentication."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customerId": {
                        "type": "string",
                        "description": "Customer ID obtained from verification (e.g., 'CUST001')",
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of questions to retrieve (default: 2, max: 3)",
                        "default": 2,
                    },
                },
                "required": ["customerId"],
            },
            "returns": get_security_questions,
        },
        {
            "name": "verify_security_answers",
            "description": (
                "Verify customer's answers to security questions. All answers must be "
                "correct for successful authentication. Answers are case-insensitive but must "
                "match exactly. Examples: 'Bern' matches 'bern', 'BERN', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customerId": {
                        "type": "string",
                        "description": "Customer ID from verification",
                    },
                    "answers": {
                        "type": "array",
                        "description": (
                            "List of answers to security questions. Each answer should be a single word "
                            "or short phrase exactly matching the expected answer (case-insensitive). "
                            "Examples: 'Bern', 'Fischer', 'Rex', 'Gymnasium Bern', etc."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "questionId": {
                                    "type": "string",
                                    "description": "Question ID (e.g., 'SQ001')",
                                },
                                "answer": {
                                    "type": "string",
                                    "description": (
                                        "Customer's answer to the question. Single word or short phrase. "
                                        "Case-insensitive but must match exactly. Examples: 'Bern', 'Fischer', 'Rex'"
                                    ),
                                },
                            },
                            "required": ["questionId", "answer"],
                        },
                    },
                },
                "required": ["customerId", "answers"],
            },
            "returns": verify_security_answers,
        },
    ],
}
