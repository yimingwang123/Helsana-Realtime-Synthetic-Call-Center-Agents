"""
Service to automatically generate identity verification data for customers.

This service ensures that whenever a customer profile is created,
corresponding identity verification data (insurance number, security questions)
is automatically generated and stored in both JSON files and Cosmos DB.
"""

import json
import logging
import os
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from azure.cosmos import CosmosClient, exceptions
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

# Security questions pool (German)
SECURITY_QUESTIONS_POOL = [
    {
        "id": "SQ001",
        "question": "In welcher Stadt wurden Sie geboren?",
        "category": "personal",
        "answer_examples": ["Zürich", "Bern", "Basel", "Genf", "Luzern", "St. Gallen", "Lausanne"]
    },
    {
        "id": "SQ002",
        "question": "Wie lautet der Mädchenname Ihrer Mutter?",
        "category": "family",
        "answer_examples": ["Müller", "Meier", "Schmidt", "Fischer", "Weber", "Huber", "Keller"]
    },
    {
        "id": "SQ003",
        "question": "Wie hiess Ihr erstes Haustier?",
        "category": "personal",
        "answer_examples": ["Rex", "Luna", "Max", "Bella", "Milo", "Charlie", "Lucy"]
    },
    {
        "id": "SQ004",
        "question": "An welcher Schule haben Sie Ihre Matura gemacht?",
        "category": "education",
        "answer_examples": ["Gymnasium Zürich", "Kantonsschule Basel", "Realgymnasium Bern", "Gymnasium St. Gallen"]
    },
    {
        "id": "SQ005",
        "question": "Was war Ihr erstes Auto (Marke)?",
        "category": "personal",
        "answer_examples": ["Volkswagen", "Toyota", "BMW", "Mercedes", "Audi", "Opel", "Ford"]
    },
    {
        "id": "SQ006",
        "question": "In welcher Strasse haben Sie als Kind gewohnt?",
        "category": "personal",
        "answer_examples": ["Bahnhofstrasse", "Hauptstrasse", "Lindenweg", "Rosenweg", "Bergstrasse"]
    }
]


class IdentityDataGenerator:
    """Generates identity verification data for synthetic customers."""
    
    def __init__(self, data_dir: Path = None, cosmos_client=None):
        """Initialize the generator."""
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.customers_file = self.data_dir / "sample_customers.json"
        self.security_questions_file = self.data_dir / "security_questions.json"
        
        # Load or initialize data structures
        self.customers = self._load_customers()
        self.security_data = self._load_security_data()
        
        # Initialize Cosmos DB client
        self.cosmos_client = cosmos_client
        self.customer_container = None
        self._init_cosmos_db()
    
    def _init_cosmos_db(self):
        """Initialize Cosmos DB connection."""
        try:
            if self.cosmos_client is None:
                # Try to create Cosmos DB client if not provided
                cosmos_endpoint = os.getenv("COSMOSDB_ENDPOINT")
                if cosmos_endpoint:
                    credential = DefaultAzureCredential()
                    self.cosmos_client = CosmosClient(cosmos_endpoint, credential)
                    logger.info("✅ Created Cosmos DB client for identity data")
                else:
                    logger.warning("⚠️ COSMOSDB_ENDPOINT not set - identity data will only be saved to JSON files")
                    return
            
            if self.cosmos_client:
                cosmos_database = os.getenv("COSMOSDB_DATABASE", "CustomerDB")
                database = self.cosmos_client.get_database_client(cosmos_database)
                
                # Get customer container
                cosmos_customer_container = os.getenv("COSMOSDB_Customer_CONTAINER", "Customer")
                self.customer_container = database.get_container_client(cosmos_customer_container)
                logger.info(f"✅ Connected to Cosmos DB container: {cosmos_customer_container}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize Cosmos DB client: {e}")
            logger.warning("Identity data will only be saved to JSON files")
            self.customer_container = None
    
    def _load_customers(self) -> List[Dict[str, Any]]:
        """Load existing customer data."""
        if self.customers_file.exists():
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _load_security_data(self) -> Dict[str, Any]:
        """Load existing security questions data."""
        if self.security_questions_file.exists():
            with open(self.security_questions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "questions": [
                {"id": q["id"], "question": q["question"], "category": q["category"]}
                for q in SECURITY_QUESTIONS_POOL
            ],
            "customer_answers": {}
        }
    
    def _save_customers(self):
        """Save customers to file."""
        with open(self.customers_file, 'w', encoding='utf-8') as f:
            json.dump(self.customers, f, ensure_ascii=False, indent=2)
    
    def _save_security_data(self):
        """Save security data to file."""
        with open(self.security_questions_file, 'w', encoding='utf-8') as f:
            json.dump(self.security_data, f, ensure_ascii=False, indent=2)
    
    def _generate_insurance_number(self) -> str:
        """Generate a Swiss insurance number (CH-XXXXXXXXXXXXX)."""
        # Generate 13 random digits
        digits = ''.join([str(random.randint(0, 9)) for _ in range(13)])
        return f"CH-76{digits[2:]}"  # Start with 76 (common Swiss prefix)
    
    def _generate_birthdate(self) -> str:
        """Generate a random birthdate (YYYY-MM-DD)."""
        year = random.randint(1950, 2005)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Safe day range
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    def _generate_security_answers(self, customer_id: str) -> List[Dict[str, str]]:
        """Generate random security question answers for a customer."""
        # Select 3 random questions
        selected_questions = random.sample(SECURITY_QUESTIONS_POOL, 3)
        
        answers = []
        for q in selected_questions:
            answer = random.choice(q["answer_examples"])
            answers.append({
                "questionId": q["id"],
                "answer": answer
            })
        
        return answers
    
    def generate_identity_data_for_customer(
        self,
        customer_id: str,
        first_name: str,
        last_name: str,
        email: str = None,
        phone_number: str = None,
        address: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete identity verification data for a customer.
        
        Args:
            customer_id: Customer ID
            first_name: First name
            last_name: Last name
            email: Email address
            phone_number: Phone number
            address: Address dict with street, city, postal_code, country
            
        Returns:
            Dictionary with complete identity data
        """
        logger.info(f"Generating identity data for customer: {customer_id} ({first_name} {last_name})")
        
        # Format full address string
        if address:
            full_address = (
                f"{address.get('street', '')}, "
                f"{address.get('postal_code', '')} {address.get('city', '')}"
            ).strip(", ")
        else:
            full_address = None
        
        # Generate identity data
        identity_data = {
            "customerId": customer_id,
            "name": f"{first_name} {last_name}",
            "versicherungsnummer": self._generate_insurance_number(),
            "geburtstag": self._generate_birthdate(),
            "adresse": full_address,
            "email": email,
            "telefon": phone_number
        }
        
        # Generate security question answers
        security_answers = self._generate_security_answers(customer_id)
        
        # Update data structures
        self._add_or_update_customer(identity_data)
        self._add_or_update_security_answers(customer_id, security_answers)
        
        # Save to files
        self._save_customers()
        self._save_security_data()
        
        # Save to Cosmos DB
        self._save_to_cosmos_db(customer_id, identity_data, security_answers)
        
        logger.info(f"✅ Identity data generated and saved for {customer_id}")
        
        return {
            "identity_data": identity_data,
            "security_answers": security_answers
        }
    
    def _add_or_update_customer(self, customer_data: Dict[str, Any]):
        """Add or update customer in the list."""
        customer_id = customer_data["customerId"]
        
        # Check if customer exists
        for i, customer in enumerate(self.customers):
            if customer.get("customerId") == customer_id:
                self.customers[i] = customer_data
                logger.debug(f"Updated existing customer: {customer_id}")
                return
        
        # Add new customer
        self.customers.append(customer_data)
        logger.debug(f"Added new customer: {customer_id}")
    
    def _add_or_update_security_answers(self, customer_id: str, answers: List[Dict[str, str]]):
        """Add or update security answers for a customer."""
        self.security_data["customer_answers"][customer_id] = answers
        logger.debug(f"Added/updated security answers for: {customer_id}")
    
    def _save_to_cosmos_db(self, customer_id: str, identity_data: Dict[str, Any], security_answers: List[Dict[str, str]]):
        """
        Save identity verification data to Cosmos DB by updating the customer document.
        
        This adds identity_verification fields to the existing customer document.
        """
        if not self.customer_container:
            logger.debug("Cosmos DB not configured - skipping Cosmos DB save")
            return
        
        try:
            # Read existing customer document
            try:
                customer_doc = self.customer_container.read_item(
                    item=customer_id,
                    partition_key=customer_id
                )
                logger.debug(f"Found existing customer document for {customer_id}")
            except exceptions.CosmosResourceNotFoundError:
                logger.warning(f"Customer {customer_id} not found in Cosmos DB - cannot add identity data")
                return
            except Exception as e:
                logger.error(f"Error reading customer document: {e}")
                return
            
            # Add identity verification data to customer document
            customer_doc["identity_verification"] = {
                "versicherungsnummer": identity_data["versicherungsnummer"],
                "geburtstag": identity_data["geburtstag"],
                "adresse": identity_data["adresse"],
                "security_questions": security_answers,
                "generated_at": datetime.utcnow().isoformat(),
                "verified": False  # Will be set to True when customer verifies
            }
            
            # Upsert the document back to Cosmos DB
            self.customer_container.upsert_item(customer_doc)
            logger.info(f"💾 Saved identity data to Cosmos DB for customer: {customer_id}")
            logger.info(f"   Versicherungsnummer: {identity_data['versicherungsnummer']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save identity data to Cosmos DB for {customer_id}: {e}")
            logger.exception(e)
    
    def generate_identity_data_from_cosmos_customer(self, cosmos_customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate identity data from a Cosmos DB customer document.
        
        Args:
            cosmos_customer: Customer document from Cosmos DB
            
        Returns:
            Generated identity data
        """
        customer_id = cosmos_customer.get("customer_id")
        first_name = cosmos_customer.get("first_name")
        last_name = cosmos_customer.get("last_name")
        email = cosmos_customer.get("email")
        phone_number = cosmos_customer.get("phone_number")
        address = cosmos_customer.get("address", {})
        
        return self.generate_identity_data_for_customer(
            customer_id=customer_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            address=address
        )
    
    def batch_generate_from_cosmos(self, cosmos_customers: List[Dict[str, Any]]) -> int:
        """
        Generate identity data for multiple Cosmos DB customers.
        
        Args:
            cosmos_customers: List of customer documents from Cosmos DB
            
        Returns:
            Number of customers processed
        """
        logger.info(f"Batch generating identity data for {len(cosmos_customers)} customers")
        
        count = 0
        for customer in cosmos_customers:
            try:
                self.generate_identity_data_from_cosmos_customer(customer)
                count += 1
            except Exception as e:
                customer_id = customer.get("customer_id", "unknown")
                logger.error(f"Failed to generate identity data for {customer_id}: {e}")
        
        logger.info(f"✅ Batch generation complete: {count}/{len(cosmos_customers)} customers")
        return count


# Singleton instance
_identity_data_generator: IdentityDataGenerator = None


def get_identity_data_generator() -> IdentityDataGenerator:
    """Get or create the identity data generator singleton."""
    global _identity_data_generator
    if _identity_data_generator is None:
        _identity_data_generator = IdentityDataGenerator()
    return _identity_data_generator
