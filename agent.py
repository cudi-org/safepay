"""
Bulut AI Agent - Natural Language Payment Processing
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

try:
    import anthropic
except ImportError:
    print("⚠️  anthropic package not installed. Install with: pip install anthropic")
    anthropic = None

try:
    from pydantic import BaseModel, Field
except ImportError:
    print("⚠️  pydantic package not installed. Install with: pip install pydantic")
    BaseModel = object
    Field = lambda *args, **kwargs: None

# ============================================================================
# BULUT AI AGENT 
# ============================================================================

class BulutAIAgent:
    """
    Bulut's Brain - AI-Powered Payment Intent Parser
    
    Converts natural language like:
    - "Send $50 to @alice"
    - "Split $120 between @bob and @carol"
    - "Pay @netflix $9.99 every month"
    
    Into structured payment intents for blockchain execution.
    """
    
    MODEL = "claude-sonnet-4-20250514"
    
    # Bulut's Core Prompt - This is Bulut's personality and intelligence
    SYSTEM_PROMPT = """You are Bulut, an AI payment assistant that converts natural language into structured payment commands.

# YOUR MISSION
Parse human payment requests into precise JSON payment intents with MAXIMUM accuracy.

# PAYMENT TYPES
1. **single** - One-time payment to one person
2. **subscription** - Recurring payments (daily, weekly, monthly, yearly)
3. **split** - Divide payment among multiple people

# EXTRACTION RULES

## Amounts
- Extract numeric values: "$50", "50 dollars", "fifty bucks" → 50.0
- Handle decimals: "$9.99", "9 dollars 99 cents" → 9.99
- Multiple formats: "100 USD", "0.5 ETH", "50 ARC"

## Recipients (Aliases)
- Format: @username (3-20 chars, alphanumeric + underscore)
- Examples: "@alice", "@bob123", "@my_friend"
- Multiple recipients for splits: "@alice and @bob"

## Currencies
- USD (default), EUR, GBP, ARC, ETH, BTC, etc.
- "Send 50 dollars" → USD
- "Send 0.5 ETH" → ETH
- "Send 100 ARC" → ARC

## Temporal Expressions
- "tomorrow", "next Monday", "in 3 days"
- "every month", "monthly", "weekly", "daily"
- "starting November 1st"

## Split Logic
- "split evenly" → equal percentages
- "bob gets 60%, carol gets 40%" → custom splits
- "divide between" → equal split
- Must total 100%

## Memos/Notes
- Text after "for": "for lunch", "for rent", "for subscription"
- Keep concise (under 200 chars)

# CONFIDENCE SCORING
Rate your certainty from 0.0 to 1.0:

- **0.9-1.0**: Clear, unambiguous intent with all required info
- **0.7-0.89**: Minor ambiguity but safe to proceed
- **0.5-0.69**: Significant ambiguity, needs clarification
- **<0.5**: Cannot parse reliably, return error

# OUTPUT FORMAT
Return ONLY valid JSON (no markdown, no explanation):

```json
{
  "payment_type": "single|subscription|split",
  "intent": {
    "action": "send|request|schedule|split",
    "amount": 50.0,
    "currency": "USD",
    "recipient": {"alias": "@alice"},
    "memo": "optional description"
  },
  "confidence": 0.95,
  "requires_confirmation": true,
  "confirmation_text": "Send $50 to @alice?"
}
```

# ERROR HANDLING
If critical information is missing:
```json
{
  "payment_type": "single",
  "intent": {},
  "confidence": 0.3,
  "requires_confirmation": false,
  "error": {
    "code": "missing_amount|missing_recipient|ambiguous_intent",
    "message": "Clear explanation of what's missing",
    "suggestions": ["Try: 'Send [amount] to [recipient]'"]
  }
}
```

# EXAMPLES

Input: "Send $50 to @alice for lunch"
Output:
```json
{
  "payment_type": "single",
  "intent": {
    "action": "send",
    "amount": 50.0,
    "currency": "USD",
    "recipient": {"alias": "@alice"},
    "memo": "lunch"
  },
  "confidence": 0.95,
  "requires_confirmation": true,
  "confirmation_text": "Send $50 to @alice for lunch?"
}
```

Input: "Split $120 between @bob and @carol"
Output:
```json
{
  "payment_type": "split",
  "intent": {
    "action": "split",
    "amount": 120.0,
    "currency": "USD",
    "recipients": [
      {"alias": "@bob", "amount": 60.0, "percentage": 50},
      {"alias": "@carol", "amount": 60.0, "percentage": 50}
    ]
  },
  "confidence": 0.89,
  "requires_confirmation": true,
  "confirmation_text": "Split $120 evenly between @bob and @carol?"
}
```

Input: "Pay @netflix $9.99 every month"
Output:
```json
{
  "payment_type": "subscription",
  "intent": {
    "action": "send",
    "amount": 9.99,
    "currency": "USD",
    "recipient": {"alias": "@netflix"},
    "subscription": {
      "frequency": "monthly",
      "start_date": "2025-11-06T00:00:00Z"
    }
  },
  "confidence": 0.92,
  "requires_confirmation": true,
  "confirmation_text": "Set up monthly payment of $9.99 to @netflix?"
}
```

# CRITICAL RULES
1. ALWAYS return valid JSON
2. NEVER include markdown code blocks
3. NEVER add explanatory text outside JSON
4. BE STRICT about validation
5. PREFER lower confidence over incorrect parsing
6. ALWAYS include confirmation_text for user review
7. For ambiguous amounts: ASK rather than GUESS

Remember: Accuracy > Speed. Better to ask for clarification than execute wrong payment."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Bulut AI Agent
        
        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        if not anthropic:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = self.MODEL
    
    async def parse_payment(
        self,
        text: str,
        user_id: Optional[str] = None,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Parse natural language payment command using Claude
        
        Args:
            text: User's payment command (e.g., "Send $50 to @alice")
            user_id: Optional user identifier for context
            timezone: User's timezone for date parsing
        
        Returns:
            Structured payment intent as dict
        """
        
        # Enhance prompt with user context
        user_message = f"Parse this payment command: \"{text}\""
        
        # Add context
        if timezone:
            current_time = datetime.utcnow()
            user_message += f"\n\nContext:"
            user_message += f"\n- Current UTC time: {current_time.isoformat()}"
            user_message += f"\n- User timezone: {timezone}"
        
        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract response
            response_text = message.content[0].text.strip()
            
            # Remove markdown code blocks if present (just in case)
            response_text = re.sub(r'^```json?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            
            # Parse JSON
            payment_intent = json.loads(response_text)
            
            # Add metadata
            payment_intent["_metadata"] = {
                "raw_input": text,
                "parsed_at": datetime.utcnow().isoformat(),
                "model": self.model,
                "user_id": user_id,
                "timezone": timezone
            }
            
            # Validate and enhance
            payment_intent = self._validate_and_enhance(payment_intent)
            
            return payment_intent
        
        except json.JSONDecodeError as e:
            return self._error_response(
                "parsing_error",
                f"Failed to parse AI response as JSON: {str(e)}",
                ["Please try rephrasing your command"]
            )
        except anthropic.APIError as e:
            return self._error_response(
                "api_error",
                f"Anthropic API error: {str(e)}",
                ["Please try again in a moment"]
            )
        except Exception as e:
            return self._error_response(
                "unexpected_error",
                f"Unexpected error: {str(e)}",
                ["Please try again"]
            )
    
    def _validate_and_enhance(self, intent: Dict[str, Any]) -> Dict[str, Any]:
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
                intent["error"] = {
                    "code": "invalid_split",
                    "message": f"Split percentages total {total_pct}%, must be 100%"
                }
        
        # Require confirmation for large amounts
        amount = intent.get("intent", {}).get("amount", 0)
        if amount > 1000:
            intent["requires_confirmation"] = True
            intent["confidence"] = min(intent.get("confidence", 1), 0.85)
        
        # Ensure confirmation text exists
        if not intent.get("confirmation_text"):
            intent["confirmation_text"] = self._generate_confirmation_text(intent)
        
        return intent
    
    @staticmethod
    def _is_valid_alias(alias: str) -> bool:
        """Validate alias format: @username (3-20 chars)"""
        pattern = r'^@[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, alias))
    
    @staticmethod
    def _generate_confirmation_text(intent: Dict[str, Any]) -> str:
        """Generate confirmation text from intent"""
        intent_data = intent.get("intent", {})
        payment_type = intent.get("payment_type")
        
        if payment_type == "single":
            amount = intent_data.get("amount")
            currency = intent_data.get("currency", "USD")
            recipient = intent_data.get("recipient", {}).get("alias", "recipient")
            return f"Send {currency} {amount} to {recipient}?"
        
        elif payment_type == "split":
            amount = intent_data.get("amount")
            currency = intent_data.get("currency", "USD")
            recipients = intent_data.get("recipients", [])
            return f"Split {currency} {amount} between {len(recipients)} recipients?"
        
        elif payment_type == "subscription":
            amount = intent_data.get("amount")
            currency = intent_data.get("currency", "USD")
            frequency = intent_data.get("subscription", {}).get("frequency", "monthly")
            recipient = intent_data.get("recipient", {}).get("alias", "recipient")
            return f"Set up {frequency} payment of {currency} {amount} to {recipient}?"
        
        return "Confirm payment?"
    
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

# ============================================================================
# MOCK AI PARSER 
# ============================================================================

class MockAIParser:
    """
    Mock AI parser for development/testing 
    Uses pattern matching - less accurate but functional
    """
    
    @staticmethod
    async def parse_payment(
        text: str,
        user_id: Optional[str] = None,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Parse payment using simple pattern matching"""
        
        text_lower = text.lower()
        
        # Extract amount
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', text)
        amount = float(amount_match.group(1)) if amount_match else None
        
        # Extract currency
        currency = "USD"
        if "arc" in text_lower:
            currency = "ARC"
        elif "eth" in text_lower:
            currency = "ETH"
        elif "btc" in text_lower:
            currency = "BTC"
        
        # Extract alias(es)
        aliases = re.findall(r'@(\w+)', text)
        
        # Determine payment type
        if "split" in text_lower or "divide" in text_lower:
            return MockAIParser._parse_split(text, amount, currency, aliases)
        elif "every" in text_lower or "monthly" in text_lower or "subscription" in text_lower:
            return MockAIParser._parse_subscription(text, amount, currency, aliases)
        else:
            return MockAIParser._parse_single(text, amount, currency, aliases)
    
    @staticmethod
    def _parse_single(text: str, amount: float, currency: str, aliases: List[str]) -> Dict:
        """Parse single payment"""
        
        if not amount:
            return {
                "payment_type": "single",
                "intent": {},
                "confidence": 0.3,
                "requires_confirmation": True,
                "error": {
                    "code": "missing_amount",
                    "message": "Could not determine payment amount",
                    "suggestions": ["Try: 'Send $50 to @alice'"]
                }
            }
        
        if not aliases:
            return {
                "payment_type": "single",
                "intent": {},
                "confidence": 0.3,
                "requires_confirmation": True,
                "error": {
                    "code": "missing_recipient",
                    "message": "Could not determine recipient",
                    "suggestions": ["Try: 'Send $50 to @alice'"]
                }
            }
        
        alias = f"@{aliases[0]}"
        
        # Extract memo
        memo = None
        if "for" in text.lower():
            memo_parts = text.lower().split("for", 1)
            if len(memo_parts) > 1:
                memo = memo_parts[1].strip()[:200]
        
        return {
            "payment_type": "single",
            "intent": {
                "action": "send",
                "amount": amount,
                "currency": currency,
                "recipient": {"alias": alias},
                "memo": memo
            },
            "confidence": 0.85,
            "requires_confirmation": True,
            "confirmation_text": f"Send {currency} {amount} to {alias}?",
            "_metadata": {
                "parser": "mock",
                "note": "Using pattern matching. For better accuracy, configure Anthropic API key."
            }
        }
    
    @staticmethod
    def _parse_subscription(text: str, amount: float, currency: str, aliases: List[str]) -> Dict:
        """Parse subscription payment"""
        
        if not amount or not aliases:
            return {
                "payment_type": "subscription",
                "intent": {},
                "confidence": 0.3,
                "requires_confirmation": True,
                "error": {
                    "code": "missing_info",
                    "message": "Need amount and recipient for subscription"
                }
            }
        
        frequency = "monthly"
        if "weekly" in text.lower():
            frequency = "weekly"
        elif "daily" in text.lower():
            frequency = "daily"
        elif "yearly" in text.lower():
            frequency = "yearly"
        
        alias = f"@{aliases[0]}"
        start_date = datetime.utcnow().isoformat()
        
        return {
            "payment_type": "subscription",
            "intent": {
                "action": "send",
                "amount": amount,
                "currency": currency,
                "recipient": {"alias": alias},
                "subscription": {
                    "frequency": frequency,
                    "start_date": start_date
                }
            },
            "confidence": 0.80,
            "requires_confirmation": True,
            "confirmation_text": f"Set up {frequency} payment of {currency} {amount} to {alias}?",
            "_metadata": {"parser": "mock"}
        }
    
    @staticmethod
    def _parse_split(text: str, amount: float, currency: str, aliases: List[str]) -> Dict:
        """Parse split payment"""
        
        if not amount:
            return {
                "payment_type": "split",
                "intent": {},
                "confidence": 0.3,
                "error": {
                    "code": "missing_amount",
                    "message": "Need amount to split"
                }
            }
        
        if len(aliases) < 2:
            return {
                "payment_type": "split",
                "intent": {},
                "confidence": 0.4,
                "error": {
                    "code": "insufficient_recipients",
                    "message": "Need at least 2 recipients for split payment"
                }
            }
        
        # Equal split by default
        per_person = amount / len(aliases)
        recipients = [
            {
                "alias": f"@{alias}",
                "amount": round(per_person, 2),
                "percentage": round(100 / len(aliases), 2)
            }
            for alias in aliases
        ]
        
        return {
            "payment_type": "split",
            "intent": {
                "action": "split",
                "amount": amount,
                "currency": currency,
                "recipients": recipients
            },
            "confidence": 0.78,
            "requires_confirmation": True,
            "confirmation_text": f"Split {currency} {amount} between {len(aliases)} people?",
            "_metadata": {"parser": "mock"}
        }

# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def parse_payment_command(
    text: str,
    api_key: Optional[str] = None,
    user_id: Optional[str] = None,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    """
    Convenience function to parse payment command
    
    Args:
        text: Payment command
        api_key: Anthropic API key (optional)
        user_id: User identifier (optional)
        timezone: User timezone (optional)
    
    Returns:
        Payment intent dict
    """
    
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    
    if api_key and anthropic:
        # Use real AI agent
        agent = BulutAIAgent(api_key=api_key)
        return await agent.parse_payment(text, user_id, timezone)
    else:
        # Use mock parser
        return await MockAIParser.parse_payment(text, user_id, timezone)

# ============================================================================
# MAIN - FOR TESTING
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    print("=" * 70)
    print("🧠 Bulut AI Agent - Test Suite")
    print("=" * 70)
    
    # Test commands
    test_commands = [
        "Send $50 to @alice for lunch",
        "Split $120 between @bob and @carol",
        "Pay @netflix $9.99 every month",
        "Send 0.5 ARC to @developer",
        "Give @john 60% and @jane 40% of $100",
    ]
    
    async def run_tests():
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if api_key:
            print("\n✅ Using Claude AI Agent (Anthropic API)")
        else:
            print("\n⚠️  Using Mock Parser (No API key found)")
            print("Set ANTHROPIC_API_KEY environment variable to use Claude\n")
        
        for i, command in enumerate(test_commands, 1):
            print(f"\n{'─'*70}")
            print(f"Test {i}: {command}")
            print('─'*70)
            
            result = await parse_payment_command(command)
            
            print(f"Type: {result.get('payment_type')}")
            print(f"Confidence: {result.get('confidence'):.2f}")
            print(f"Confirmation: {result.get('confirmation_text')}")
            
            if result.get('error'):
                print(f"Error: {result['error'].get('message')}")
            else:
                print(f"Intent: {json.dumps(result.get('intent'), indent=2)}")
        
        print("\n" + "="*70)
        print("✅ Test suite complete")
        print("="*70)
    
    asyncio.run(run_tests())