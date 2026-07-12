import base64
import httpx
from anthropic import Anthropic
from app.config import settings


async def transcribe_audio_brief(audio_url: str) -> str:
    """Transcribe audio brief using Claude's audio understanding."""
    # Download audio file
    async with httpx.AsyncClient() as http:
        audio_data = await http.get(audio_url)

    audio_b64 = base64.standard_b64encode(audio_data.content).decode("utf-8")

    # Determine media type
    content_type = "audio/mpeg"
    if audio_url.endswith(".wav"):
        content_type = "audio/wav"
    elif audio_url.endswith(".mp4") or audio_url.endswith(".m4a"):
        content_type = "audio/mp4"

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "audio",
                        "source": {
                            "type": "base64",
                            "media_type": content_type,
                            "data": audio_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Transcribe this audio brief word for word. Return only the transcription, no commentary.",
                    },
                ],
            }
        ],
    )

    return response.content[0].text
