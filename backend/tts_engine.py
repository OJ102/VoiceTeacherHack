import os
import io
from gtts import gTTS
from typing import Tuple


class TTSEngine:
    """Text-to-speech engine using Google TTS (gTTS)."""

    def __init__(self, language: str = "en"):
        self.language = language

    def text_to_speech(self, text: str) -> Tuple[bytes, str]:
        """Convert text to speech audio.

        Args:
            text: Text to convert to speech

        Returns:
            (audio_bytes, audio_format)
            - audio_bytes: MP3 audio data
            - audio_format: "mp3"
        """
        try:
            # Create TTS object
            tts = gTTS(text=text, lang=self.language, slow=False)

            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_bytes = audio_buffer.read()

            return audio_bytes, "mp3"
        except Exception as e:
            # Return empty audio if TTS fails
            print(f"TTS Error: {e}")
            return b"", "mp3"
