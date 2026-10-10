import sys
import json
import base64
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")

from teacher_agent import TeachingAgent, Session, GREETING
from tts_engine import TTSEngine

app = FastAPI(title="Voice Teaching Agent")
teacher_agent = TeachingAgent()
tts_engine = TTSEngine()


async def send_reply(websocket: WebSocket, data: dict):
    audio, fmt = await asyncio.to_thread(tts_engine.text_to_speech, data["response"])
    await websocket.send_json({
        "type": "response",
        "text": data["response"],
        "options": data.get("options", []),
        "phase": data.get("phase", "probe"),
        "plan": data.get("plan", []),
        "current_step": data.get("current_step"),
        "emotion": data.get("emotion", "calm"),
        "confusion_score": data.get("confusion_score", 0.0),
        "audio": base64.b64encode(audio).decode("utf-8"),
        "audio_format": fmt,
    })


@app.websocket("/ws/teach")
async def websocket_teach(websocket: WebSocket):
    """Client sends {"type": "voice_turn", "text", "audio"} or {"type": "text_input", "text"}."""
    await websocket.accept()
    session = Session()
    await send_reply(websocket, {"response": GREETING, "phase": "probe"})

    try:
        while True:
            message = json.loads(await websocket.receive_text())
            text = (message.get("text") or "").strip()
            if not text:
                continue
            audio = base64.b64decode(message["audio"]) if message.get("audio") else None
            try:
                data = await teacher_agent.generate_response(session, text, audio)
                await send_reply(websocket, data)
            except Exception as e:
                print(f"Turn error: {e}", flush=True)
                await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        pass


app.mount("/", StaticFiles(directory=str(Path(__file__).parent.parent / "frontend"), html=True), name="frontend")
