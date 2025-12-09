"""Identity verification and authentication API routes."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.identity_service import get_identity_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class VerifyCustomerRequest(BaseModel):
    """Request model for customer verification."""
    first_name: Optional[str] = Field(None, description="Customer's first name")
    last_name: Optional[str] = Field(None, description="Customer's last name")
    email: Optional[str] = Field(None, description="Customer's email address")
    phone_number: Optional[str] = Field(None, description="Customer's phone number")
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    postal_code: Optional[str] = Field(None, description="Postal code")


class VerifyCustomerResponse(BaseModel):
    """Response model for customer verification."""
    verified: bool = Field(..., description="Whether customer was verified")
    customerId: Optional[str] = Field(None, description="Customer ID if verified")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    message: str = Field(..., description="Human-readable message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Matching details")
    customerData: Optional[Dict[str, Any]] = Field(None, description="Customer data if verified")


class SecurityQuestion(BaseModel):
    """Security question model."""
    questionId: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text in German")
    category: str = Field(..., description="Question category")


class SecurityQuestionsResponse(BaseModel):
    """Response model for security questions."""
    success: bool = Field(..., description="Whether questions were retrieved successfully")
    customerId: Optional[str] = Field(None, description="Customer ID")
    questions: List[SecurityQuestion] = Field(default_factory=list, description="List of security questions")
    message: str = Field(..., description="Human-readable message")


class SecurityAnswer(BaseModel):
    """Security answer model."""
    questionId: str = Field(..., description="Question ID")
    answer: str = Field(..., description="Customer's answer")


class VerifySecurityAnswersRequest(BaseModel):
    """Request model for verifying security answers."""
    customerId: str = Field(..., description="Customer ID")
    answers: List[SecurityAnswer] = Field(..., description="List of answers to verify")


class VerifySecurityAnswersResponse(BaseModel):
    """Response model for security answer verification."""
    authenticated: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Human-readable message")
    correctCount: int = Field(..., description="Number of correct answers")
    totalCount: int = Field(..., description="Total number of questions")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed results per question")


# API Endpoints
@router.post("/identity/verifyCustomer", response_model=VerifyCustomerResponse)
async def verify_customer(request: VerifyCustomerRequest):
    """
    Verify customer identity based on provided information.
    
    This endpoint attempts to match the provided customer information
    (first name, last name, email, phone, address) against the customer database.
    
    Returns a verification result with a confidence score.
    A confidence score of 1.0 means all fields matched exactly.
    """
    try:
        logger.info("[API] POST /api/identity/verifyCustomer")
        
        identity_service = get_identity_service()
        result = identity_service.verify_customer(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone_number=request.phone_number,
            street=request.street,
            city=request.city,
            postal_code=request.postal_code
        )
        
        return VerifyCustomerResponse(**result)
        
    except Exception as e:
        logger.error(f"Error verifying customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/identity/security-questions", response_model=SecurityQuestionsResponse)
async def get_security_questions(customerId: str, count: int = 2):
    """
    Get random security questions for a customer.
    
    Args:
        customerId: The customer ID (e.g., CUST001)
        count: Number of questions to return (default: 2, max: 3)
        
    Returns:
        A list of security questions for the customer to answer.
    """
    try:
        logger.info(f"[API] GET /api/identity/security-questions?customerId={customerId}&count={count}")
        
        # Validate count
        if count < 1 or count > 3:
            raise HTTPException(status_code=400, detail="Count must be between 1 and 3")
        
        identity_service = get_identity_service()
        result = identity_service.get_security_questions(customerId, count)
        
        return SecurityQuestionsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting security questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/identity/security-answers", response_model=VerifySecurityAnswersResponse)
async def verify_security_answers(request: VerifySecurityAnswersRequest):
    """
    Verify customer's answers to security questions.
    
    This endpoint checks if the provided answers match the customer's
    stored security question answers. Uses fuzzy matching with 80% similarity threshold.
    
    All answers must be correct for successful authentication.
    """
    try:
        logger.info(f"[API] POST /api/identity/security-answers for customer {request.customerId}")
        
        if not request.answers:
            raise HTTPException(status_code=400, detail="No answers provided")
        
        identity_service = get_identity_service()
        
        # Convert Pydantic models to dicts
        answers_dict = [{"questionId": ans.questionId, "answer": ans.answer} for ans in request.answers]
        
        result = identity_service.verify_security_answers(
            customer_id=request.customerId,
            answers=answers_dict
        )
        
        return VerifySecurityAnswersResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying security answers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
