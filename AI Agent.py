"""
Bulut AI Agent - Natural Language Payment Parser
Converts human language to structured payment intents
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Initialize API client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class PaymentRequest(BaseModel):
    text: str = Field(..., description="Natural language payment command")
    user_id: Optional[str] = Field(None, description="User identifier for context")
    timezone: Optional[str] = Field("UTC", description="User timezone for date parsing")

class BulutAIAgent:
    """Core AI agent for parsing payment intents"""
    
    SYSTEM_PROMPT = """You are Bulut's payment intent parser. Your job is to convert natural language into structured JSON payment commands.

PAYMENT TYPES:
1. **single**: One-time payments (send, request)
2. **subscription**: Recurring payments (weekly, monthly, etc.)
3. **split**: Divide payment among multiple people

EXTRACTION RULES:
- Extract amounts: "50 dollars", "$50", "fifty bucks" → 50
- Extract aliases: "@alice", "@bob123" → validate format
- Extract temporal: "tomorrow", "next Monday", "in 3 days", "monthly"
- Split logic: "split evenly", "bob gets 60%", "divide between"
- Currencies: USD (default), EUR, ARC, BTC, ETH

CONFIDENCE SCORING:
- 0.9-1.0: Clear, unambiguous intent
- 0.7-0.89: Minor ambiguity, safe to proceed
- 0.5-0.69: Significant ambiguity, needs clarification
- <0.5: Cannot parse, return error

OUTPUT FORMAT:
Return ONLY valid JSON matching the bulut_json_schema. No additional text.

EXAMPLES:
"Send $50 to @alice" → single payment, confidence 0.95
"Pay @netflix $9.99 every month" → subscription, confidence 0.92
"Split $100 with @bob and @carol" → split payment, confidence 0.89
"Give @john half and @jane half of $60" → split payment, confidence 0.91

Be strict about validation. If critical info is missing, set confidence <0.7 and provide error details."""

    def __init__(self):
        self.model = "claude-sonnet-4-20250514"
    
    def parse_payment_intent(self, text: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main parsing function - converts natural language to payment JSON
        
        Args:
            text: User's natural language command
            user_context: Optional context (timezone, user_id, etc.)
        
        Returns:
            Structured payment intent JSON
        """
        try:
            # Enhance prompt with user context
            user_message = f"Parse this payment command: \"{text}\""
            
            if user_context and user_context.get("timezone"):
                user_message += f"\n\nUser timezone: {user_context['timezone']}"
                user_message += f"\nCurrent time: {datetime.now().isoformat()}"
            
            # Call API
            message = client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract JSON from response
            response_text = message.content[0].text
            payment_intent = json.loads(response_text)
            
            # Add metadata
            payment_intent["_metadata"] = {
                "raw_input": text,
                "parsed_at": datetime.utcnow().isoformat(),
                "model_version": self.model
            }
            
            return payment_intent
            
        except json.JSONDecodeError as e:
            return self._error_response(
                "parsing_error",
                f"Failed to parse AI response: {str(e)}",
                ["Try rephrasing your command"]
            )
        except Exception as e:
            return self._error_response(
                "parsing_error",
                f"Unexpected error: {str(e)}",
                ["Please try again"]
            )
    
    def validate_and_enhance(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-processing validation and enhancement
        Adds safety checks and fills in defaults
        """
        # Validate alias format
        if "recipient" in intent.get("intent", {}):
            alias = intent["intent"]["recipient"].get("alias")
            if alias and not self._is_valid_alias(alias):
                intent["confidence"] = max(0, intent.get("confidence", 0) - 0.2)
                intent["requires_confirmation"] = True
        
        # Validate split payment percentages
        if intent.get("payment_type") == "split":
            recipients = intent["intent"].get("recipients", [])
            total_pct = sum(r.get("percentage", 0) for r in recipients)
            if total_pct != 100 and total_pct != 0:
                intent["confidence"] = max(0, intent.get("confidence", 0) - 0.15)
        
        # Require confirmation for large amounts
        amount = intent.get("intent", {}).get("amount", 0)
        if amount > 1000:
            intent["requires_confirmation"] = True
            intent["confidence"] = min(intent.get("confidence", 1), 0.85)
        
        return intent
    
    @staticmethod
    def _is_valid_alias(alias: str) -> bool:
        """Validate alias format: @username (3-20 chars, alphanumeric + underscore)"""
        pattern = r'^@[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, alias))
    
    @staticmethod
    def _error_response(code: str, message: str, suggestions: List[str]) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            "payment_type": None,
            "intent": {},
            "confidence": 0.0,
            "requires_confirmation": False,
            "error": {
                "code": code,
                "message": message,
                "suggestions": suggestions
            }
        }


# FastAPI Application
app = FastAPI(title="Bulut AI Agent", version="1.0.0")
agent = BulutAIAgent()

@app.post("/parse_payment")
async def parse_payment(request: PaymentRequest):
    """
    Parse natural language payment command
    
    Returns structured JSON payment intent
    """
    user_context = {
        "timezone": request.timezone,
        "user_id": request.user_id
    }
    
    # Parse intent
    intent = agent.parse_payment_intent(request.text, user_context)
    
    # Validate and enhance
    intent = agent.validate_and_enhance(intent)
    
    # Return based on confidence
    if intent.get("confidence", 0) < 0.5:
        raise HTTPException(
            status_code=400,
            detail={
                "error": intent.get("error"),
                "message": "Could not parse payment intent with sufficient confidence"
            }
        )
    
    return intent

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bulut-ai-agent"}

# Utility function for direct integration
def get_payment_intent(text: str, **kwargs) -> Dict[str, Any]:
    """
    Standalone function for easy integration
    
    Usage:
        intent = get_payment_intent("Send $50 to @alice")
    """
    agent = BulutAIAgent()
    intent = agent.parse_payment_intent(text, kwargs)
    return agent.validate_and_enhance(intent)


if __name__ == "__main__":
    # Test cases
    test_commands = [
        "Send $50 to @alice for lunch",
        "Pay @spotify $9.99 every month",
        "Split $120 evenly between @bob, @carol, and @dave",
        "Request $200 from @client for consulting",
        "Send 0.5 ARC to @developer tomorrow"
    ]
    
    print("🧠 Bulut AI Agent - Testing Payment Parser\n")
    for cmd in test_commands:
        print(f"Input: {cmd}")
        result = get_payment_intent(cmd)
        print(f"Type: {result.get('payment_type')}")
        print(f"Confidence: {result.get('confidence'):.2f}")
        print(f"Confirmation: {result.get('confirmation_text')}")
        print("-" * 60)