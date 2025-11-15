import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from pydantic import BaseModel, Field
except ImportError:
    BaseModel = object
    Field = lambda *args, **kwargs: None

class RealAIAgent:
    MODEL = "gpt-4o"
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
ERROR HANDLING
If critical information is missing:

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
CRITICAL RULES
ALWAYS return valid JSON
NEVER include markdown code blocks
NEVER add explanatory text outside JSON
BE STRICT about validation
PREFER lower confidence over incorrect parsing
ALWAYS include confirmation_text for user review
For ambiguous amounts: ASK rather than GUESS
Remember: Accuracy > Speed. Better to ask for clarification than execute wrong payment."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key (AIMLAPI_KEY) no encontrada. Revisa tu .env")
        if not OpenAI:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = OpenAI(base_url="https://api.aimlapi.com/v1", api_key=api_key)

    async def parse_payment(self, text: str, user_id: Optional[str] = None, timezone: str = "UTC") -> Dict[str, Any]:
        user_message = f"Parse this payment command: \"{text}\""
        if timezone:
            current_time = datetime.utcnow()
            user_message += f"\n\nContext:"
            user_message += f"\n- Current UTC time: {current_time.isoformat()}"
            user_message += f"\n- User timezone: {timezone}"
        try:
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                response_format={"type": "json_object"}
            )
            raw_json = response.choices[0].message.content
            data = json.loads(raw_json)
            data = self._validate_and_enhance(data)
            data["_metadata"] = {"raw_input": text, "parsed_at": datetime.utcnow().isoformat(), "model": self.MODEL}
            return data
        except Exception as e:
            return self._error_response("unexpected_error", str(e), ["Please try again"])

    def _validate_and_enhance(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        if "recipient" in intent.get("intent", {}):
            alias = intent["intent"]["recipient"].get("alias")
            if alias and not self._is_valid_alias(alias):
                intent["confidence"] = max(0, intent.get("confidence", 0) - 0.2)
        if not intent.get("confirmation_text"):
            intent["confirmation_text"] = "Confirm payment?"
        return intent

    @staticmethod
    def _is_valid_alias(alias: str) -> bool:
        pattern = r'^@[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, alias))

    @staticmethod
    def _error_response(code: str, message: str, suggestions: List[str]) -> Dict[str, Any]:
        return {
            "payment_type": None,
            "intent": {},
            "confidence": 0.0,
            "requires_confirmation": False,
            "error": {"code": code, "message": message, "suggestions": suggestions}
        }

class MockAIParser:
    @staticmethod
    async def parse_payment(text: str, user_id: Optional[str] = None, timezone: str = "UTC") -> Dict[str, Any]:
        text_lower = text.lower()
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', text)
        amount = float(amount_match.group(1)) if amount_match else None
        aliases = re.findall(r'@(\w+)', text)
        if "split" in text_lower or len(aliases) > 1:
            return MockAIParser._parse_split(text, amount, "USD", aliases)
        if "every" in text_lower or "monthly" in text_lower:
            return MockAIParser._parse_subscription(text, amount, "USD", aliases)
        return MockAIParser._parse_single(text, amount, "USD", aliases)

    @staticmethod
    def _parse_single(text: str, amount: float, currency: str, aliases: List[str]) -> Dict:
        if not amount or not aliases:
            return {"payment_type": "single", "intent": {}, "confidence": 0.3, "error": {"code": "missing_info", "message": "Need amount and recipient"}}
        alias = f"@{aliases[0]}"
        return {
            "payment_type": "single",
            "intent": {"action": "send", "amount": amount, "currency": currency, "recipient": {"alias": alias}, "memo": "Mocked payment"},
            "confidence": 0.85,
            "requires_confirmation": True,
            "confirmation_text": f"Send {currency} {amount} to {alias}?",
            "_metadata": {"parser": "mock"}
        }

    @staticmethod
    def _parse_subscription(text: str, amount: float, currency: str, aliases: List[str]) -> Dict:
        alias = f"@{aliases[0] if aliases else 'recipient'}"
        return {
            "payment_type": "subscription",
            "intent": {"action": "send", "amount": amount, "currency": currency, "recipient": {"alias": alias}, "subscription": {"frequency": "monthly"}},
            "confidence": 0.80,
            "requires_confirmation": True,
            "confirmation_text": f"Set up monthly {currency} {amount} to {alias}?",
            "_metadata": {"parser": "mock"}
        }

    @staticmethod
    def _parse_split(text: str, amount: float, currency: str, aliases: List[str]) -> Dict:
        return {
            "payment_type": "split",
            "intent": {"action": "split", "amount": amount, "currency": currency, "recipients": [{"alias": f"@{a}"} for a in aliases]},
            "confidence": 0.78,
            "requires_confirmation": True,
            "confirmation_text": f"Split {currency} {amount} between {len(aliases)} people?",
            "_metadata": {"parser": "mock"}
        }

async def parse_payment_command(text: str, api_key: Optional[str] = None, user_id: Optional[str] = None, timezone: str = "UTC") -> Dict[str, Any]:
    api_key = api_key or os.getenv("AIMLAPI_KEY")
    if api_key and OpenAI:
        agent = RealAIAgent(api_key=api_key)
        return await agent.parse_payment(text, user_id, timezone)
    else:
        return await MockAIParser.parse_payment(text, user_id, timezone)

if __name__ == "__main__":
    import asyncio
    print("=" * 70)
    print("🧠 Bulut AI Agent - Test Suite")
    print("=" * 70)
    test_commands = ["Send $50 to @alice for lunch", "Split $120 between @bob and @carol", "Pay @netflix $9.99 every month"]
    async def run_tests():
        api_key = os.getenv("AIMLAPI_KEY")
        if api_key and OpenAI:
            print("\n✅ Using Real AI Agent (aimlapi.com)")
        else:
            print("\n⚠️  Using Mock Parser (No API key found or 'openai' not installed)")
            print("Set AIMLAPI_KEY environment variable to use Real AI\n")
        for i, command in enumerate(test_commands, 1):
            print(f"\n{'─'*70}\nTest {i}: {command}\n{'─'*70}")
            result = await parse_payment_command(command)
            print(f"Type: {result.get('payment_type')}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Confirmation: {result.get('confirmation_text')}")
            if result.get('error'):
                print(f"Error: {result['error'].get('message')}")
            else:
                print(f"Intent: {json.dumps(result.get('intent'), indent=2)}")
    asyncio.run(run_tests())
