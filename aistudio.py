import os
import asyncio
import traceback
import pyaudio
import argparse

from google import genai
from google.genai import types

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024 

MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
DEFAULT_MODE = "none"

# --- ΡΥΘΜΙΣΗ SYSTEM INSTRUCTIONS ---
SYST_INSTRUCT = """
ΕΙΣΑΓΩΓΗ:
Είσαι ένας βοηθός για ηλικιωμένους.

ΚΑΝΟΝΕΣ:
1. Μην δίνεις ποτέ ιατρικές διαγνώσεις.
2. Να είσαι ευγενικός και υπομονετικός.
3. Αν δεν ξέρεις κάτι, πες "δεν γνωρίζω".
4. Η ώρα να ειναι πάντα για την Ελλάδα.
5. Χρησιμοποίησε απλή γλώσσα.
6. Απόφυγε τη χρήση τεχνικών όρων.
7. Αν η ώρα είναι π.μ. να αναφέρεις "πρωί", αν είναι μ.μ. να αναφέρεις "απόγευμα".
8. Έχεις πρόσβαση στο Google Search για να βρίσκεις πληροφορίες σε πραγματικό χρόνο.
9. Όταν ψάχνεις, πες ότι ψάχνεις.

ΓΛΩΣΣΑ:
Απάντα πάντα σε απλά Ελληνικά.
"""

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    
    # Ενεργοποίηση Instructions
    system_instruction=types.Content(
        parts=[types.Part(text=SYST_INSTRUCT)]
    ),
    
    # Ενεργοποίηση Google Search
    tools=[
        types.Tool(google_search=types.GoogleSearch())
    ],

    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=25600,
        sliding_window=types.SlidingWindow(target_tokens=12800),
    ),
)

pya = pyaudio.PyAudio()


class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.is_playing = False 

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(input, "message > ")
            if text.lower() == "q":
                break
            
            await self.session.send_client_content(
                turns=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=text or ".")]
                    )
                ],
                turn_complete=True
            )

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            
            # Walkie-Talkie Logic: Mute mic when AI speaks
            if self.is_playing:
                continue

            await self.session.send_realtime_input(
                audio={
                    "data": msg["data"],
                    "mime_type": "audio/pcm"
                }
            )

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def receive_audio(self):
            while True:
                turn = self.session.receive()
                async for response in turn:
                    if server_content := response.server_content:
                        if model_turn := server_content.model_turn:
                            for part in model_turn.parts:
                                # 1. Κείμενο & Σκέψεις (π.χ. "Investigating...")
                                if part.text:
                                    print(part.text, end="")
                                
                                # 2. Ήχος
                                if part.inline_data and part.inline_data.data:
                                    self.audio_in_queue.put_nowait(part.inline_data.data)

                # Walkie-Talkie logic: Καθαρισμός ουράς
                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            self.is_playing = False
            bytestream = await self.audio_in_queue.get()
            self.is_playing = True

            while not self.audio_in_queue.empty():
                bytestream += self.audio_in_queue.get_nowait()

            await asyncio.to_thread(stream.write, bytestream)

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                send_text_task = tg.create_task(self.send_text())
                
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            if hasattr(self, 'audio_stream') and self.audio_stream:
                self.audio_stream.close()
            traceback.print_exception(EG)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="pixels to stream from",
        choices=["none"],
    )
    args = parser.parse_args()
    main = AudioLoop(video_mode=args.mode)
    asyncio.run(main.run())