import os
import base64
import json
from typing import Dict


class ModulateEmotionDetector:
    """Wrapper for Modulate emotion detection API."""

    def __init__(self):
        self.api_key = os.getenv("MODULATE_API_KEY")
        self.api_url = "https://api.modulate.ai/v1/detect"

    async def detect_emotion(self, audio_bytes: bytes) -> Dict:
        """Analyze emotion from audio stream.

        Args:
            audio_bytes: Raw audio data (WAV or MP3)

        Returns:
            {
                "emotion": "calm" | "confused" | "frustrated",
                "confusion_score": 0.0-1.0,
                "confidence": 0.0-1.0,
            }
        """
        try:
            import httpx

            # Encode audio to base64 for API
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"audio": audio_b64, "format": "wav"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "emotion": data.get("emotion", "calm"),  # calm, confused, frustrated
                        "confusion_score": data.get("confusion_score", 0.0),
                        "confidence": data.get("confidence", 0.0),
                    }
                else:
                    return {
                        "success": False,
                        "emotion": "calm",
                        "confusion_score": 0.0,
                        "confidence": 0.0,
                        "error": f"API error: {response.status_code}",
                    }
        except Exception as e:
            # Fallback: assume calm if API fails
            return {
                "success": False,
                "emotion": "calm",
                "confusion_score": 0.0,
                "confidence": 0.0,
                "error": str(e),
            }

    def get_adaptation_instruction(self, confusion_score: float) -> str:
        """Generate teaching style adaptation based on emotion."""
        if confusion_score > 0.7:
            return "The student sounds very confused/frustrated. Use VERY SIMPLE language, break concepts into tiny steps, use concrete analogies, and check understanding frequently."
        elif confusion_score > 0.5:
            return "The student seems a bit confused. Slow down, use examples, and rephrase your explanation in simpler words."
        else:
            return "The student seems comfortable. Proceed with normal explanation."
