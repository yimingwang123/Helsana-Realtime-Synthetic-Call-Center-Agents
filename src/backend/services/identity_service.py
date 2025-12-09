"""Identity verification and authentication service for Helsana customers."""

from __future__ import annotations

import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher

from azure.cosmos import CosmosClient, exceptions as cosmos_exceptions
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

# Paths to data files
DATA_DIR = Path(__file__).parent.parent / "data"
CUSTOMERS_FILE = DATA_DIR / "sample_customers.json"
SECURITY_QUESTIONS_FILE = DATA_DIR / "security_questions.json"


class IdentityService:
    """Service for customer verification and authentication."""
    
    def __init__(self, cosmos_client=None):
        """Initialize the identity service and load data."""
        self.customers = self._load_customers()
        self.security_data = self._load_security_questions()
        
        # Initialize Cosmos DB client
        self.cosmos_client = cosmos_client
        self.customer_container = None
        self._init_cosmos_db()
    
    def _init_cosmos_db(self):
        """Initialize Cosmos DB connection."""
        try:
            if self.cosmos_client is None:
                cosmos_endpoint = os.getenv("COSMOSDB_ENDPOINT")
                if cosmos_endpoint:
                    credential = DefaultAzureCredential()
                    self.cosmos_client = CosmosClient(cosmos_endpoint, credential)
                    logger.info("✅ Created Cosmos DB client for identity service")
                else:
                    logger.info("ℹ️ COSMOSDB_ENDPOINT not set - using JSON files only")
                    return
            
            if self.cosmos_client:
                cosmos_database = os.getenv("COSMOSDB_DATABASE", "CustomerDB")
                database = self.cosmos_client.get_database_client(cosmos_database)
                
                cosmos_customer_container = os.getenv("COSMOSDB_Customer_CONTAINER", "Customer")
                self.customer_container = database.get_container_client(cosmos_customer_container)
                logger.info(f"✅ Connected to Cosmos DB container: {cosmos_customer_container}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize Cosmos DB: {e}")
            self.customer_container = None
        
    def _load_customers(self) -> List[Dict[str, Any]]:
        """Load customer data from JSON file."""
        try:
            if CUSTOMERS_FILE.exists():
                with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} customers from {CUSTOMERS_FILE}")
                    return data
            else:
                logger.warning(f"Customer data file not found: {CUSTOMERS_FILE}")
                return []
        except Exception as e:
            logger.error(f"Error loading customer data: {e}")
            return []
    
    def _load_security_questions(self) -> Dict[str, Any]:
        """Load security questions data from JSON file."""
        try:
            if SECURITY_QUESTIONS_FILE.exists():
                with open(SECURITY_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded security questions from {SECURITY_QUESTIONS_FILE}")
                    return data
            else:
                logger.warning(f"Security questions file not found: {SECURITY_QUESTIONS_FILE}")
                return {"questions": [], "customer_answers": {}}
        except Exception as e:
            logger.error(f"Error loading security questions: {e}")
            return {"questions": [], "customer_answers": {}}
    
    def _get_identity_from_cosmos(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get identity verification data from Cosmos DB for a customer.
        
        Returns identity_verification data if found, otherwise None.
        """
        if not self.customer_container:
            return None
        
        try:
            customer_doc = self.customer_container.read_item(
                item=customer_id,
                partition_key=customer_id
            )
            identity_verification = customer_doc.get("identity_verification")
            if identity_verification:
                # Convert to format compatible with JSON file structure
                return {
                    "customerId": customer_id,
                    "name": customer_doc.get("first_name", "") + " " + customer_doc.get("last_name", ""),
                    "versicherungsnummer": identity_verification.get("versicherungsnummer"),
                    "geburtstag": identity_verification.get("geburtstag"),
                    "adresse": identity_verification.get("adresse"),
                    "email": customer_doc.get("email"),
                    "telefon": customer_doc.get("phone_number")
                }
            return None
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error reading identity data from Cosmos DB: {e}")
            return None
    
    def _get_all_customers_from_cosmos(self) -> List[Dict[str, Any]]:
        """
        Get all customers from Cosmos DB.
        """
        if not self.customer_container:
            logger.warning("Cosmos DB container not available")
            return []
        
        try:
            query = "SELECT * FROM c"
            items = list(self.customer_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Loaded {len(items)} customers from Cosmos DB")
            return items
        except Exception as e:
            logger.error(f"Could not load customers from Cosmos DB: {e}")
            return []
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)."""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats."""
        formats = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    
    def verify_customer(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        street: Optional[str] = None,
        city: Optional[str] = None,
        postal_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify customer identity based on provided information.
        
        Args:
            first_name: Customer's first name
            last_name: Customer's last name
            email: Customer's email address
            phone_number: Customer's phone number
            street: Street address
            city: City
            postal_code: Postal code
            
        Returns:
            Dictionary with verification result:
            - verified: bool (True if customer verified)
            - customerId: str (if verified)
            - confidence: float (0.0-1.0 confidence score)
            - message: str (human-readable message)
            - details: dict (matching details)
        """
        logger.info(
            f"[IdentityService] Verifying customer:\n"
            f"  First Name: {first_name}\n"
            f"  Last Name: {last_name}\n"
            f"  Email: {email}\n"
            f"  Phone: {phone_number}\n"
            f"  Street: {street}\n"
            f"  City: {city}\n"
            f"  Postal Code: {postal_code}"
        )
        
        if not any([first_name, last_name, email, phone_number, street, city, postal_code]):
            return {
                "verified": False,
                "customerId": None,
                "confidence": 0.0,
                "message": "No verification information provided.",
                "details": {}
            }
        
        # Get all customers from Cosmos DB
        all_customers = self._get_all_customers_from_cosmos()
        logger.info(f"[IdentityService] Checking {len(all_customers)} customers for verification")
        
        # ALL provided fields must match exactly (case-insensitive for text)
        best_match = None
        best_details = {}
        
        for customer in all_customers:
            all_fields_match = True
            details = {}
            fields_checked = 0
            
            # Check first name (case-insensitive, exact match required)
            if first_name:
                fields_checked += 1
                if customer.get("first_name", "").lower() == first_name.strip().lower():
                    details["first_name"] = "exact_match"
                else:
                    all_fields_match = False
                    details["first_name"] = "no_match"
            
            # Check last name (case-insensitive, exact match required)
            if last_name:
                fields_checked += 1
                if customer.get("last_name", "").lower() == last_name.strip().lower():
                    details["last_name"] = "exact_match"
                else:
                    all_fields_match = False
                    details["last_name"] = "no_match"
            
            # Check email (case-insensitive, exact match required)
            if email:
                fields_checked += 1
                if customer.get("email", "").lower() == email.strip().lower():
                    details["email"] = "exact_match"
                else:
                    all_fields_match = False
                    details["email"] = "no_match"
            
            # Check phone number (exact match required)
            if phone_number:
                fields_checked += 1
                # Normalize phone numbers by removing spaces and common separators
                customer_phone = customer.get("phone_number", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                provided_phone = phone_number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                if customer_phone == provided_phone:
                    details["phone_number"] = "exact_match"
                else:
                    all_fields_match = False
                    details["phone_number"] = "no_match"
            
            # Check address fields
            customer_address = customer.get("address", {})
            
            if street:
                fields_checked += 1
                if customer_address.get("street", "").lower() == street.strip().lower():
                    details["street"] = "exact_match"
                else:
                    all_fields_match = False
                    details["street"] = "no_match"
            
            if city:
                fields_checked += 1
                if customer_address.get("city", "").lower() == city.strip().lower():
                    details["city"] = "exact_match"
                else:
                    all_fields_match = False
                    details["city"] = "no_match"
            
            if postal_code:
                fields_checked += 1
                if customer_address.get("postal_code", "").lower() == postal_code.strip().lower():
                    details["postal_code"] = "exact_match"
                else:
                    all_fields_match = False
                    details["postal_code"] = "no_match"
            
            # Customer verified only if ALL provided fields match exactly
            if all_fields_match and fields_checked > 0:
                best_match = customer
                best_details = details
                break  # Found exact match, no need to continue
        
        # Verification requires 100% exact match of all provided fields
        if best_match:
            logger.info(
                f"[IdentityService] ✅ Customer verified: {best_match['customer_id']} "
                f"with 100% exact match"
            )
            return {
                "verified": True,
                "customerId": best_match["customer_id"],
                "confidence": 1.0,
                "message": f"Customer successfully verified: {best_match.get('first_name')} {best_match.get('last_name')}",
                "details": best_details,
                "customerData": {
                    "first_name": best_match.get("first_name"),
                    "last_name": best_match.get("last_name"),
                    "email": best_match.get("email"),
                    "phone_number": best_match.get("phone_number"),
                    "address": best_match.get("address")
                }
            }
        else:
            logger.warning(
                "[IdentityService] ❌ Verification failed. No exact match found."
            )
            return {
                "verified": False,
                "customerId": None,
                "confidence": 0.0,
                "message": "Verification failed. All provided information must match exactly.",
                "details": best_details
            }
    
    def get_security_questions(
        self,
        customer_id: str,
        count: int = 2
    ) -> Dict[str, Any]:
        """
        Get random security questions for a customer.
        
        Args:
            customer_id: The customer ID
            count: Number of questions to return (default: 2)
            
        Returns:
            Dictionary with questions list and session info
        """
        logger.info(f"[IdentityService] Getting {count} security questions for {customer_id}")
        
        # Check if customer has security questions
        customer_answers = self.security_data.get("customer_answers", {}).get(customer_id)
        if not customer_answers:
            logger.warning(f"[IdentityService] No security questions found for {customer_id}")
            return {
                "success": False,
                "message": "Keine Sicherheitsfragen für diesen Kunden verfügbar.",
                "questions": []
            }
        
        # Get question IDs for this customer
        available_question_ids = [qa["questionId"] for qa in customer_answers]
        
        # Select random questions
        selected_count = min(count, len(available_question_ids))
        selected_ids = random.sample(available_question_ids, selected_count)
        
        # Get full question details
        all_questions = {q["id"]: q for q in self.security_data.get("questions", [])}
        selected_questions = [
            {
                "questionId": qid,
                "question": all_questions.get(qid, {}).get("question", ""),
                "category": all_questions.get(qid, {}).get("category", "")
            }
            for qid in selected_ids
            if qid in all_questions
        ]
        
        logger.info(f"[IdentityService] Returning {len(selected_questions)} questions")
        return {
            "success": True,
            "customerId": customer_id,
            "questions": selected_questions,
            "message": f"{len(selected_questions)} Sicherheitsfragen bereitgestellt."
        }
    
    def verify_security_answers(
        self,
        customer_id: str,
        answers: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Verify customer's answers to security questions.
        
        Args:
            customer_id: The customer ID
            answers: List of {"questionId": "...", "answer": "..."}
            
        Returns:
            Dictionary with authentication result
        """
        logger.info(
            f"[IdentityService] Verifying {len(answers)} security answers for {customer_id}"
        )
        
        # Get correct answers for customer
        customer_answers = self.security_data.get("customer_answers", {}).get(customer_id)
        if not customer_answers:
            return {
                "authenticated": False,
                "message": "Keine Sicherheitsfragen für diesen Kunden verfügbar.",
                "correctCount": 0,
                "totalCount": len(answers)
            }
        
        # Build lookup dict for correct answers
        correct_answers = {
            qa["questionId"]: qa["answer"]
            for qa in customer_answers
        }
        
        # Check each answer
        correct_count = 0
        results = []
        
        for provided in answers:
            question_id = provided.get("questionId")
            provided_answer = provided.get("answer", "").strip()
            correct_answer = correct_answers.get(question_id, "").strip()
            
            # Case-insensitive exact match for security answers
            is_correct = provided_answer.lower() == correct_answer.lower()
            
            if is_correct:
                correct_count += 1
            
            results.append({
                "questionId": question_id,
                "correct": is_correct,
                "match_type": "exact" if is_correct else "no_match"
            })
            
            logger.debug(
                f"  Q: {question_id}, "
                f"Expected: '{correct_answer}', "
                f"Got: '{provided_answer}', "
                f"Match: {is_correct}"
            )
        
        # Authentication threshold: all questions must be correct
        authenticated = correct_count == len(answers) and len(answers) > 0
        
        if authenticated:
            logger.info(f"[IdentityService] ✅ Authentication successful for {customer_id}")
        else:
            logger.warning(
                f"[IdentityService] ❌ Authentication failed for {customer_id}. "
                f"Correct: {correct_count}/{len(answers)}"
            )
        
        return {
            "authenticated": authenticated,
            "message": (
                "Authentifizierung erfolgreich." if authenticated
                else f"Authentifizierung fehlgeschlagen. {correct_count}/{len(answers)} Antworten korrekt."
            ),
            "correctCount": correct_count,
            "totalCount": len(answers),
            "results": results
        }


# Singleton instance
_identity_service: Optional[IdentityService] = None


def get_identity_service() -> IdentityService:
    """Get or create the identity service singleton."""
    global _identity_service
    if _identity_service is None:
        _identity_service = IdentityService()
    return _identity_service
