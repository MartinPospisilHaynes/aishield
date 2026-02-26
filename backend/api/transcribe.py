"""
AIshield.cz — Speech-to-Text (Whisper API)
Přijme audio blob z frontendu, pošle do OpenAI Whisper API, vrátí text.
"""

import logging
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB (Whisper limit)


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Přijme audio soubor (webm/mp4/wav), pošle do OpenAI Whisper API,
    vrátí přepsaný text.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="Hlasový vstup není nakonfigurován.")

    # Read audio data
    audio_data = await file.read()
    if len(audio_data) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio soubor je příliš velký (max 25 MB).")
    if len(audio_data) < 100:
        raise HTTPException(status_code=400, detail="Audio soubor je prázdný.")

    # Determine filename extension from content type
    content_type = file.content_type or "audio/webm"
    ext_map = {
        "audio/webm": "webm",
        "audio/mp4": "mp4",
        "audio/mpeg": "mp3",
        "audio/wav": "wav",
        "audio/ogg": "ogg",
        "audio/x-m4a": "m4a",
    }
    ext = ext_map.get(content_type, "webm")
    filename = f"recording.{ext}"

    logger.info(f"[TRANSCRIBE] Received {len(audio_data)} bytes ({content_type})")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WHISPER_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                },
                files={
                    "file": (filename, audio_data, content_type),
                },
                data={
                    "model": "whisper-1",
                    "language": "cs",  # Czech
                    "response_format": "json",
                },
            )

        if response.status_code != 200:
            logger.error(f"[TRANSCRIBE] Whisper API error {response.status_code}: {response.text[:200]}")
            raise HTTPException(status_code=502, detail="Chyba při přepisu hlasu.")

        result = response.json()
        text = result.get("text", "").strip()

        if not text:
            raise HTTPException(status_code=422, detail="Nepodařilo se rozpoznat řeč.")

        logger.info(f"[TRANSCRIBE] Transcribed {len(text)} chars")

        # Track usage
        try:
            from backend.monitoring.llm_usage_tracker import usage_tracker
            duration_s = len(audio_data) / 16000  # rough estimate
            cost = max(duration_s / 60, 0.01) * 0.006  # $0.006/min
            usage_tracker.track(
                model="whisper-1",
                input_tokens=0,
                output_tokens=len(text.split()),
                cost_usd=cost,
                endpoint="transcribe",
                company_id="voice-input",
            )
        except Exception:
            pass

        return {"text": text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TRANSCRIBE] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Chyba při zpracování hlasu.")
