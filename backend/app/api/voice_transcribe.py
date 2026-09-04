"""
NEXO In-Built Audio & Voice Transcription API Endpoint.

100% In-Built, Local, and Offline speech-to-text using Vosk Kaldi Engine.
ZERO Google API. ZERO OpenAI API. ZERO cloud dependencies.
"""

import os
import json
import base64
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/api/voice", tags=["In-Built Voice Transcription"])

# Global singleton for the in-built offline Vosk model
_vosk_model = None


def get_inbuilt_vosk_model():
    """Load and cache the offline Vosk speech recognition model in memory."""
    global _vosk_model
    if _vosk_model is None:
        try:
            import vosk
            vosk.SetLogLevel(-1)  # Suppress verbose Vosk C++ logs
            logger.info("[VoiceTranscribe] Loading in-built offline Vosk model...")
            _vosk_model = vosk.Model(lang="en-us")
            logger.info("[VoiceTranscribe] In-built offline Vosk model loaded successfully! ✓")
        except Exception as e:
            logger.error(f"[VoiceTranscribe] Error loading in-built Vosk model: {e}")
    return _vosk_model


def resample_pcm16(audio_bytes: bytes, in_rate: int, out_rate: int = 16000) -> bytes:
    """Resample 16-bit mono PCM bytes to 16kHz for Kaldi acoustic model."""
    if in_rate == out_rate or not audio_bytes:
        return audio_bytes
    import struct
    num_samples = len(audio_bytes) // 2
    if num_samples == 0:
        return b""
    samples = struct.unpack(f"<{num_samples}h", audio_bytes)
    ratio = out_rate / in_rate
    out_len = int(num_samples * ratio)
    out_samples = [0] * out_len
    for i in range(out_len):
        orig_idx = i / ratio
        idx = int(orig_idx)
        frac = orig_idx - idx
        if idx + 1 < num_samples:
            val = int(samples[idx] * (1 - frac) + samples[idx + 1] * frac)
        else:
            val = samples[-1]
        out_samples[i] = max(-32768, min(32767, val))
    return struct.pack(f"<{out_len}h", *out_samples)


class Base64AudioPayload(BaseModel):
    audio_base64: str
    format: str = "pcm"  # Raw PCM bytes
    sample_rate: int = 16000


@router.post("/transcribe")
async def transcribe_audio(payload: Base64AudioPayload = Body(...)):
    """
    Transcribe raw audio recorded from phone microphone using in-built offline engine.
    Completely offline, zero Google, zero OpenAI.
    """
    try:
        audio_bytes = base64.b64decode(payload.audio_base64)
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio payload")

        in_sample_rate = payload.sample_rate if payload.sample_rate in [8000, 16000, 44100, 48000] else 16000
        logger.info(f"[VoiceTranscribe] Received {len(audio_bytes)} bytes at {in_sample_rate} Hz. Resampling to 16kHz...")

        # Resample to 16kHz for native Kaldi acoustic model accuracy
        pcm_16k = resample_pcm16(audio_bytes, in_sample_rate, 16000)

        model = get_inbuilt_vosk_model()
        transcribed_text = ""

        if model is not None:
            try:
                import vosk
                # In-built Kaldi Recognizer calibrated at native 16kHz
                rec = vosk.KaldiRecognizer(model, 16000)
                rec.SetWords(True)

                results = []
                chunk_size = 4000
                for i in range(0, len(pcm_16k), chunk_size):
                    chunk = pcm_16k[i:i + chunk_size]
                    if rec.AcceptWaveform(chunk):
                        res = json.loads(rec.Result())
                        text_part = res.get("text", "").strip()
                        if text_part:
                            results.append(text_part)

                final_res = json.loads(rec.FinalResult())
                final_part = final_res.get("text", "").strip()
                if final_part:
                    results.append(final_part)

                transcribed_text = " ".join(results).strip()
                logger.info(f"[VoiceTranscribe] In-Built Vosk Transcribed (High Accuracy): '{transcribed_text}' ✓")
            except Exception as vosk_err:
                logger.error(f"[VoiceTranscribe] Vosk transcription error: {vosk_err}")

        if not transcribed_text:
            transcribed_text = ""

        return {
            "status": "ok",
            "transcribed_text": transcribed_text,
            "byte_count": len(audio_bytes),
            "engine": "in-built-offline-vosk",
        }
    except Exception as e:
        logger.error(f"[VoiceTranscribe] In-built transcription error: {e}")
        return {
            "status": "error",
            "transcribed_text": "",
            "byte_count": 0,
            "error": str(e),
        }
