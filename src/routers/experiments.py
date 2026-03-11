from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

from lib.env import env

router = APIRouter(prefix="/experiments", tags=["experiments"])
openai_client = AsyncOpenAI(api_key=env.OPENAI_API_KEY)
CHROME_EXTENSION_ORIGIN = "chrome-extension://cnhndebfkfpdhpakkfckefglmbjonmbp"


class TextToSpeechRequest(BaseModel):
    text: str
    voice: str | None = None


@router.post("/tts")
async def text_to_speech(payload: TextToSpeechRequest, request: Request):
    origin = request.headers.get("origin")
    if origin != CHROME_EXTENSION_ORIGIN:
        raise HTTPException(
            status_code=403, detail="Origin not allowed for TTS."
        )
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    async def _audio_stream():
        try:
            async with openai_client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=payload.voice or "alloy",
                input=text,
            ) as response:
                async for chunk in response.iter_bytes():
                    if chunk:
                        yield chunk
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"TTS stream failed: {exc}"
            ) from exc

    return StreamingResponse(_audio_stream(), media_type="audio/mpeg")
