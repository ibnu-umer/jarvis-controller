import asyncio
import tempfile
from pathlib import Path
import edge_tts, pyttsx3
import sounddevice as sd
import soundfile as sf

from core.logger import logger



class TTS:
    VOICE = "en-US-GuyNeural"
    reported = False

    async def _generate_tts_async(self, text: str, output_path: Path):
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.VOICE
        )

        with open(output_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])

    def _play_audio(self, path: Path):
        data, samplerate = sf.read(path, dtype="float32")
        sd.play(data, samplerate)
        sd.wait()

    async def _say_offline(self, text: str):
        try:
            _offline_engine = pyttsx3.init()
            await _offline_engine.say(text)
            await _offline_engine.runAndWait()
            _offline_engine.stop()
        except Exception as e:
            logger.debug(f"PYTTSX3 Failed: {e}")

    async def say(self, text: str):
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
            await self._generate_tts_async(text, temp_path)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._play_audio, temp_path)
        except Exception as e:
            if not reported:
                logger.debug(f"Edge-TTS Failed: {e}")
                reported = True
            await self._say_offline(text)
        finally:
            if temp_path.exists():
                temp_path.unlink()

