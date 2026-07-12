import httpx
from app.config import settings


async def transcribe_audio_brief(audio_url: str) -> str:
    """Download audio file and transcribe via OpenAI Whisper API."""
    import openai

    async with httpx.AsyncClient() as http:
        audio_data = await http.get(audio_url)

    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=("brief.mp3", audio_data.content, "audio/mpeg"),
        language="en",
    )
    return transcript.text
