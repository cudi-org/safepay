"""
Bulut Voice Integration - ElevenLabs API
Convert payment confirmations to natural voice audio
"""

import os
import httpx
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

# Voice settings for Bulut
BULUT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (warm, professional)
# Alternative voices:
# "EXAVITQu4vr4xnSDxMaL" - Sarah (friendly)
# "ErXwobaYiN019PkySvjV" - Antoni (male, confident)

class VoiceRequest(BaseModel):
    """Request for voice synthesis"""
    text: str
    voice_id: Optional[str] = BULUT_VOICE_ID
    model_id: Optional[str] = "eleven_multilingual_v2"
    voice_settings: Optional[Dict] = None

class BulutVoice:
    """
    Bulut Voice Agent
    Converts confirmation text to natural speech
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = ELEVENLABS_API_URL
        
        # Default voice settings optimized for payment confirmations
        self.default_settings = {
            "stability": 0.71,           # More stable, less variation
            "similarity_boost": 0.5,     # Natural voice similarity
            "style": 0.0,                # Neutral style
            "use_speaker_boost": True    # Enhance clarity
        }
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str = BULUT_VOICE_ID,
        output_format: str = "mp3_44100_128"
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs API
        
        Args:
            text: Text to convert
            voice_id: ElevenLabs voice ID
            output_format: Audio format (mp3_44100_128, pcm_16000, etc.)
        
        Returns:
            Audio bytes in specified format
        """
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": self.default_settings
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"ElevenLabs API error: {response.text}"
                )
            
            return response.content
    
    def format_confirmation_text(self, payment_intent: Dict) -> str:
        """
        Format payment intent into natural confirmation speech
        
        Args:
            payment_intent: Parsed payment intent from AI
        
        Returns:
            Natural language confirmation text optimized for TTS
        """
        
        payment_type = payment_intent.get("payment_type")
        intent = payment_intent.get("intent", {})
        
        # Single payment
        if payment_type == "single":
            amount = intent.get("amount")
            currency = intent.get("currency", "dollars")
            recipient = intent.get("recipient", {}).get("alias", "the recipient")
            memo = intent.get("memo")
            
            text = f"Ready to send {amount} {currency} to {recipient}."
            
            if memo:
                text += f" For {memo}."
            
            text += " Please confirm to continue."
        
        # Subscription
        elif payment_type == "subscription":
            amount = intent.get("amount")
            currency = intent.get("currency", "dollars")
            recipient = intent.get("recipient", {}).get("alias")
            frequency = intent.get("subscription", {}).get("frequency", "monthly")
            
            text = f"Setting up {frequency} payment of {amount} {currency} to {recipient}. "
            text += "Please confirm to continue."
        
        # Split payment
        elif payment_type == "split":
            amount = intent.get("amount")
            currency = intent.get("currency", "dollars")
            recipients = intent.get("recipients", [])
            
            text = f"Splitting {amount} {currency} between "
            
            if len(recipients) == 2:
                text += f"{recipients[0].get('alias')} and {recipients[1].get('alias')}."
            else:
                alias_list = [r.get('alias') for r in recipients[:-1]]
                text += f"{', '.join(alias_list)}, and {recipients[-1].get('alias')}."
            
            text += " Please confirm to continue."
        
        else:
            text = "Payment intent received. Please confirm to continue."
        
        # Add pauses for natural speech (SSML-style)
        text = text.replace(". ", "... ")
        
        return text
    
    async def generate_confirmation_audio(
        self,
        payment_intent: Dict,
        format: str = "mp3"
    ) -> Dict[str, str]:
        """
        Generate complete audio confirmation for payment
        
        Returns:
            Dict with audio data (base64) and metadata
        """
        
        # Format text for speech
        confirmation_text = self.format_confirmation_text(payment_intent)
        
        # Synthesize speech
        audio_bytes = await self.synthesize_speech(
            text=confirmation_text,
            voice_id=BULUT_VOICE_ID
        )
        
        # Encode to base64 for easy transport
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {
            "audio_data": audio_base64,
            "format": format,
            "text": confirmation_text,
            "duration_estimate": len(confirmation_text) * 0.1,  # Rough estimate
            "size_bytes": len(audio_bytes)
        }


# FastAPI application for voice service
app = FastAPI(title="Bulut Voice Service", version="1.0.0")

# Initialize voice agent
voice_agent = BulutVoice(api_key=ELEVENLABS_API_KEY)

@app.post("/voice/confirmation")
async def generate_voice_confirmation(payment_intent: Dict):
    """
    Generate voice confirmation for payment intent
    
    Returns audio file in base64 format
    """
    
    if not ELEVENLABS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Voice service not configured"
        )
    
    try:
        result = await voice_agent.generate_confirmation_audio(payment_intent)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice generation failed: {str(e)}"
        )

@app.post("/voice/custom")
async def generate_custom_voice(request: VoiceRequest):
    """
    Generate voice for custom text
    Useful for testing and custom messages
    """
    
    if not ELEVENLABS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Voice service not configured"
        )
    
    try:
        audio_bytes = await voice_agent.synthesize_speech(
            text=request.text,
            voice_id=request.voice_id
        )
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {
            "audio_data": audio_base64,
            "format": "mp3",
            "text": request.text,
            "size_bytes": len(audio_bytes)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice generation failed: {str(e)}"
        )

@app.get("/voice/voices")
async def list_available_voices():
    """
    List all available ElevenLabs voices
    """
    
    if not ELEVENLABS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Voice service not configured"
        )
    
    url = f"{ELEVENLABS_API_URL}/voices"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch voices"
            )
        
        return response.json()


# Frontend Integration Example (JavaScript/TypeScript)
FRONTEND_EXAMPLE = """
// Frontend usage of Bulut Voice

async function playConfirmation(paymentIntent) {
  // Request voice confirmation from backend
  const response = await fetch('https://api.bulut.app/voice/confirmation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(paymentIntent)
  });
  
  const data = await response.json();
  
  // Decode base64 audio
  const audioData = atob(data.audio_data);
  const audioArray = new Uint8Array(audioData.length);
  for (let i = 0; i < audioData.length; i++) {
    audioArray[i] = audioData.charCodeAt(i);
  }
  
  // Create audio blob and play
  const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);
  
  audio.play();
  
  // Show visual confirmation simultaneously
  showConfirmationUI(data.text);
}

// Usage in payment flow
const intent = await processCommand("Send $50 to @alice");
await playConfirmation(intent);
"""

# Pitch Demo Script
PITCH_DEMO_SCRIPT = """
# Bulut Voice - Pitch Demo Script

## Demo Flow:

1. **Opening:**
   "Meet Bulut - your AI-powered payment assistant"
   
2. **Command Examples:**
   User: "Send 50 dollars to Alice"
   Bulut Voice: "Ready to send 50 dollars to @alice. Please confirm to continue."
   
   User: "Split the dinner bill of 120 with Bob and Carol"
   Bulut Voice: "Splitting 120 dollars between @bob and @carol. Please confirm to continue."
   
   User: "Pay Netflix 9.99 every month"
   Bulut Voice: "Setting up monthly payment of 9 dollars and 99 cents to @netflix. Please confirm to continue."

3. **Success Confirmation:**
   Bulut Voice: "Payment successful. 50 dollars sent to @alice. Transaction complete."

4. **Closing:**
   "Bulut makes payments as natural as having a conversation."

## Voice Settings for Demo:
- Voice: Rachel (warm, professional)
- Stability: 0.71 (clear and consistent)
- Speed: 1.0x (natural pace)
- Format: MP3, 44.1kHz
"""

if __name__ == "__main__":
    print("🎤 Bulut Voice Service")
    print("=" * 60)
    print("\nFeatures:")
    print("✓ Natural voice confirmations for all payment types")
    print("✓ ElevenLabs integration with optimized settings")
    print("✓ Base64 audio encoding for easy transport")
    print("✓ Customizable voices and speech parameters")
    print("\nDemo Script:")
    print(PITCH_DEMO_SCRIPT)