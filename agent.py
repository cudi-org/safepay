"""
agent.py
Bulut's AI Brain – converts human text → structured JSON (payment intent)
"""

import os
import httpx
import re
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import HTTPException, status

# =============================================================================
# CONFIG
# =============================================================================

AI_API_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
AI_API_KEY = os.getenv("AI_API_KEY", "your-openai-key")
AI_MODEL = os.getenv("AI_MODEL", "gpt-5")

# =============================================================================
# SCHEMA
# =============================================================================

class PaymentIntent(BaseModel):
    """Standardized response for payment intent"""
    payment_type: str = Field(..., description="single | subscription | split")
    intent: dict = Field(..., description="Parsed intent details")
    confidence: float = Field(default=1.0, ge=0, le=1)
    requires_confirmation: bool = Field(default=True)
    confirmation_text: str | None = None
    error: dict | None = None

# =============================================================================
# BULUT AI AGENT
# =============================================================================

class AIAgent:
    """
    Bulut's AI functionality.
    Converts conversational text into a structured JSON payment intent.
    """

    @staticmethod
    async def parse_payment(text: str, user_id: str = None, timezone: str = "UTC") -> PaymentIntent:
        """
        Core function: sends natural text to AI model and validates response.
        Falls back to regex-based extraction if API fails.
        """
        try:
            headers = {
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json",
            }

            prompt = f"""
            You are Bulut, an intelligent financial AI that converts user payment commands
            into structured JSON following this schema:
            {{
              "payment_type": "single" | "subscription" | "split",
              "intent": {{
                  "amount": number,
                  "currency": "ARC" | "USD" | "ETH",
                  "recipient": {{"alias": "@alias_name"}},
                  "memo": optional string,
                  "subscription": optional {{
                      "frequency": "daily" | "weekly" | "monthly" | "yearly",
                      "start_date": ISO-8601 string
                  }},
                  "recipients": optional list for split payments
              }},
              "confidence": float (0-1),
              "requires_confirmation": boolean,
              "confirmation_text": string
            }}

            Example:
            Input: "Send 20 ARC to @john for coffee"
            Output: {{
                "payment_type": "single",
                "intent": {{
                    "amount": 20,
                    "currency": "ARC",
                    "recipient": {{"alias": "@john"}},
                    "memo": "coffee"
                }},
                "confidence": 0.98,
                "requires_confirmation": true,
                "confirmation_text": "Send 20 ARC to @john for coffee?"
            }}
            """

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    AI_API_URL,
                    headers=headers,
                    json={
                        "model": AI_MODEL,
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": text}
                        ],
                        "temperature": 0.1
                    }
                )

            if response.status_code != 200:
                raise Exception(f"AI API error {response.status_code}: {response.text}")

            content = response.json()
            output = content.get("choices", [{}])[0].get("message", {}).get("content")

            # Try parsing JSON
            import json
            data = json.loads(output)
            return PaymentIntent(**data)

        except Exception as e:
            # Fallback: simple local parsing (basic intent extraction)
            print(f"[Bulut AI fallback] {e}")
            return await AIAgent._fallback_parser(text)

    # -------------------------------------------------------------------------
    # FALLBACK PARSER (for local dev)
    # -------------------------------------------------------------------------

    @staticmethod
    async def _fallback_parser(text: str) -> PaymentIntent:
        """Backup method if API fails"""
        text_lower = text.lower()

        # Extract amount
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', text)
        amount = float(amount_match.group(1)) if amount_match else 0.0

        # Extract alias
        alias_match = re.search(r'@(\w+)', text)
        alias = f"@{alias_match.group(1)}" if alias_match else "@unknown"

        # Extract memo
        memo = None
        if "for" in text_lower:
            memo_parts = text_lower.split("for", 1)
            if len(memo_parts) > 1:
                memo = memo_parts[1].strip()

        return PaymentIntent(
            payment_type="single",
            intent={
                "action": "send",
                "amount": amount,
                "currency": "ARC",
                "recipient": {"alias": alias},
                "memo": memo,
            },
            confidence=0.6,
            requires_confirmation=True,
            confirmation_text=f"Send ARC {amount} to {alias}?"
        )
