from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import httpx

from lib.env import env

router = APIRouter(prefix="/experiments", tags=["experiments"])


class TextToSpeechRequest(BaseModel):
    text: str
    voice: str | None = None


@router.post("/tts")
async def text_to_speech(payload: TextToSpeechRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {env.OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini-tts",
                "voice": payload.voice or "alloy",
                "input": text,
            },
        )

    if response.status_code != 200:
        error_detail: str | dict
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text or "TTS request failed"
        raise HTTPException(status_code=500, detail=error_detail)

    if not response.content:
        raise HTTPException(
            status_code=500, detail="TTS stream unavailable"
        )

    return Response(content=response.content, media_type="audio/mpeg")
