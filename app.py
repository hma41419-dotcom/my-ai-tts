import os
import hmac
from io import BytesIO

import edge_tts
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

app = FastAPI(title="Myanmar English AI TTS")

TOKEN = os.getenv("TTS_SERVICE_TOKEN", "")

VOICES = {
    "my-MM-NilarNeural",
    "my-MM-ThihaNeural",
    "en-US-JennyNeural",
    "en-US-GuyNeural",
    "en-GB-SoniaNeural",
    "en-GB-RyanNeural",
}


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice: str = "my-MM-NilarNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"


def check_token(authorization: str = Header(default="")):
    if TOKEN:
        expected = f"Bearer {TOKEN}"
        if not hmac.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/")
def home():
    return {"status": "online", "service": "Myanmar English AI TTS"}


@app.get("/voices")
def voices():
    return {"voices": sorted(VOICES)}


@app.post("/synthesize")
async def synthesize(
    request: SpeechRequest,
    authorization: str = Header(default="")
):
    check_token(authorization)

    if request.voice not in VOICES:
        raise HTTPException(status_code=400, detail="Unsupported voice")

    try:
        audio = BytesIO()
        communicate = edge_tts.Communicate(
            request.text,
            request.voice,
            rate=request.rate,
            pitch=request.pitch
        )

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])

        if audio.tell() == 0:
            raise HTTPException(status_code=500, detail="No audio generated")

        return Response(
            content=audio.getvalue(),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
