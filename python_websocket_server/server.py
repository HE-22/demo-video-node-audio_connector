import asyncio
import websockets
import logging
import numpy as np
from io import BytesIO
import whisper
import os
from collections import deque
from datetime import datetime, timedelta
from colorama import Fore, Style

# Load the Whisper model for real-time transcription
model = whisper.load_model("tiny")

# Server configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8765

# Audio stream configuration
SAMPLE_WIDTH = 2  # Assuming 16-bit audio
FRAME_RATE = 16000  # Sample rate
CHANNELS = 1  # Mono audio

# Buffer and transcription configuration
BUFFER_DURATION = 10  # Buffer duration in seconds
SILENCE_THRESHOLD = 500  # Silence threshold for audio chunk
PHRASE_TIMEOUT = 3  # Timeout to consider end of phrase

# Initialize a queue for audio data
audio_queue = deque()
last_audio_time = None

# Set of connected websockets
connected = set()

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)


async def handle_audio(websocket, path):
    global last_audio_time
    connected.add(websocket)
    buffer = BytesIO()

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                buffer.write(message)
                last_audio_time = datetime.now()

            # Transcribe if buffer is full or if silence is detected
            current_time = datetime.now()
            if (
                buffer.getbuffer().nbytes
                >= BUFFER_DURATION * FRAME_RATE * SAMPLE_WIDTH * CHANNELS
            ) or (
                last_audio_time
                and (current_time - last_audio_time) > timedelta(seconds=PHRASE_TIMEOUT)
            ):
                # Reset last audio time
                last_audio_time = None

                # Process and transcribe buffered audio
                buffer.seek(0)
                audio_np = (
                    np.frombuffer(buffer.read(), dtype=np.int16).astype(np.float32)
                    / 32768.0
                )
                result = model.transcribe(audio_np)
                transcription = result["text"].strip()

                logging.info(
                    f"Transcribed Text: {Fore.GREEN}{transcription}{Style.RESET_ALL}"
                )

                # Reset buffer for next audio stream
                buffer = BytesIO()

    except websockets.exceptions.ConnectionClosed:
        logging.info("Connection closed")
    finally:
        connected.remove(websocket)


async def start_server():
    async with websockets.serve(handle_audio, SERVER_HOST, SERVER_PORT):
        logging.info(f"Server started on ws://{SERVER_HOST}:{SERVER_PORT}")
        await asyncio.Future()  # Run server indefinitely


if __name__ == "__main__":
    asyncio.run(start_server())
