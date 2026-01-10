import asyncio
import tempfile
from pathlib import Path

import edge_tts
import sounddevice as sd
import soundfile as sf


VOICE = "en-US-GuyNeural"


async def _generate_tts_async(text: str, output_path: Path):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE
    )

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])


async def _generate_tts(text: str, output_path: Path):
    await _generate_tts_async(text, output_path)


def _play_audio(path: Path):
    data, samplerate = sf.read(path, dtype="float32")
    sd.play(data, samplerate)
    sd.wait()


async def say(text: str):
    """
    Generate TTS, play it, and clean up temp audio.
    """
    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        await _generate_tts(text, temp_path)
        _play_audio(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    say("Hello sir. All systems are operational.")
