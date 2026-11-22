import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class TranscriptionUnavailable(Exception):
    pass


def transcribe_audio(audio_path, mime_type="audio/wav", language="auto"):
    endpoint = os.getenv("VOICE_STT_ENDPOINT", "").strip()
    api_key = os.getenv("VOICE_STT_API_KEY", "").strip()
    if not endpoint:
        raise TranscriptionUnavailable(
            "Managed speech-to-text is not configured. Use browser speech recognition or manually enter/correct the transcript."
        )

    path = Path(audio_path)
    if not path.is_file():
        raise TranscriptionUnavailable("Audio file is unavailable.")

    boundary = "----SmartFactoryVoiceBoundary"
    payload = bytearray()
    payload.extend(f"--{boundary}\r\n".encode())
    payload.extend(f'Content-Disposition: form-data; name="audio"; filename="{path.name}"\r\n'.encode())
    payload.extend(f"Content-Type: {mime_type}\r\n\r\n".encode())
    payload.extend(path.read_bytes())
    payload.extend(f"\r\n--{boundary}--\r\n".encode())

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if language and language != "UNKNOWN":
        headers["X-Speech-Language"] = language.lower()

    request = Request(endpoint, data=bytes(payload), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=90) as response:
            import json
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise TranscriptionUnavailable(f"Speech-to-text service unavailable: {exc}") from exc

    for key in ("text", "transcript", "result"):
        value = body.get(key) if isinstance(body, dict) else None
        if isinstance(value, str) and value.strip():
            return value.strip()
    results = body.get("results") if isinstance(body, dict) else None
    if isinstance(results, list):
        texts = [
            item.get("text") or item.get("transcript")
            for item in results
            if isinstance(item, dict)
        ]
        text = " ".join(item for item in texts if item)
        if text:
            return text.strip()
    raise TranscriptionUnavailable("Speech-to-text returned no transcript text.")
