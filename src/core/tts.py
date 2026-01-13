import asyncio
import tempfile
from pathlib import Path
import edge_tts, pyttsx3
import sounddevice as sd
import soundfile as sf

from core.logger import logger



VOICE = "en-US-GuyNeural"
reported = False


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


async def say_offline(text: str):
    try:
        _offline_engine = pyttsx3.init()
        await _offline_engine.say(text)
        await _offline_engine.runAndWait()
        _offline_engine.stop()
    except Exception as e:
        logger.debug(f"PYTTSX3 Failed: {e}")


async def say(text: str):
    """
    Generate TTS, play it, and clean up temp audio.
    """
    global reported

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        await _generate_tts(text, temp_path)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _play_audio, temp_path)
    except Exception as e:
        if not reported:
            logger.debug(f"Edge-TTS Failed: {e}")
            reported = True
        await say_offline(text)
    finally:
        if temp_path.exists():
            temp_path.unlink()





if __name__ == "__main__":
    say("Hello sir. All systems are operational.")
