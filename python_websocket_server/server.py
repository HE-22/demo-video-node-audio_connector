import asyncio
import websockets
import logging
import numpy as np
from io import BytesIO
import wave
from openai import OpenAI
from dotenv import load_dotenv
import os
from collections import deque
from datetime import datetime, timedelta
from colorama import Fore, Style

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=api_key)

# WebSocket server configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8765

# Audio stream configuration
SAMPLE_WIDTH = 2  # Assuming 16-bit audio
FRAME_RATE = 16000  # Assuming a sample rate of 16000 Hz
CHANNELS = 1  # Mono audio

# Buffering configuration
BUFFER_DURATION = 10  # Duration in seconds for buffering audio
SILENCE_THRESHOLD = 500  # Silence threshold for audio chunk
PHRASE_TIMEOUT = 3  # Timeout in seconds to consider end of phrase


# Initialize a queue to store audio chunks
audio_queue = deque()
last_audio_time = None

# Initialize a set to store connected websockets
connected = set()

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)


async def handle_audio(websocket, path):
    global last_audio_time
    client_id = id(websocket)
    connected.add(websocket)
    buffer = BytesIO()

    try:
        async for message in websocket:
            # Add logging to track the size of audio chunks
            # logging.info(
            #     f"Client {client_id}: Received audio chunk of size: {len(message)} bytes"
            # )

            # Accumulate audio data until silence is detected for a duration of PHRASE_TIMEOUT
            if not is_silence(message):
                audio_queue.append(message)
                last_audio_time = datetime.now()
            elif last_audio_time and (datetime.now() - last_audio_time) > timedelta(
                seconds=PHRASE_TIMEOUT
            ):
                # logging.info("Silence detected, sending audio for transcription")
                while audio_queue:
                    buffer.write(audio_queue.popleft())

                if buffer.getbuffer().nbytes > 0:
                    buffer.seek(0)
                    file_name = "temp_audio.wav"
                    with wave.open(file_name, "wb") as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(SAMPLE_WIDTH)
                        wf.setframerate(FRAME_RATE)
                        wf.writeframes(buffer.read())

                    transcription = transcribe_audio(file_name)
                    logging.info(
                        f"Client {client_id}: {Fore.GREEN}Transcribed Text: {transcription}{Style.RESET_ALL}"
                    )
                    # stop everythign here
                    await asyncio.sleep(3)

                    # Reset buffer
                    buffer = BytesIO()

    except websockets.exceptions.ConnectionClosed:
        logging.info("Connection closed")
    finally:
        connected.remove(websocket)


def transcribe_audio(file_path: str):
    """
    Transcribe the audio file using OpenAI's Whisper API.

    Args:
    - file_path: Path to the audio file.

    Returns:
    - Transcribed text as a string.
    """
    try:
        with open(file_path, "rb") as audio_file:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                prompt="the speaker will use both russian and english. when they use both languages in the same phrase ensure the correct language is used.",
            )
        # Ensure that the transcribe_audio function extracts and returns only the transcribed text from the Whisper API response
        return response
    except Exception as e:
        logging.error(f"Failed to transcribe audio: {e}")
        return ""


def is_silence(audio_chunk, threshold=500):
    """
    Determine if a given audio chunk is silence.
    """
    amplitude = np.frombuffer(audio_chunk, dtype=np.int16)
    return np.abs(amplitude).mean() < threshold


async def start_server():
    async with websockets.serve(handle_audio, SERVER_HOST, SERVER_PORT):
        logging.info(f"Server started on ws://{SERVER_HOST}:{SERVER_PORT}")
        await asyncio.Future()  # Run forever


# Check if the script is run directly (not imported as a module)
if __name__ == "__main__":
    # Set up the event loop and run the server
    asyncio.run(start_server())
