import asyncio
import websockets
import logging
import wave
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=api_key)


connected = set()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Constants for audio format
SAMPLE_RATE = 16000  # 16 kHz
BIT_DEPTH = 2  # 16 bits (2 bytes) per sample
CHANNELS = 1  # Mono audio
BUFFER_DURATION = 10  # Seconds

# Calculate the buffer size for 10 seconds of audio
BUFFER_SIZE = SAMPLE_RATE * BIT_DEPTH * CHANNELS * BUFFER_DURATION


async def handle_audio(websocket, path):
    connected.add(websocket)
    audio_buffer = bytearray()

    try:
        while True:
            message = await websocket.recv()
            audio_buffer += message

            if len(audio_buffer) >= BUFFER_SIZE:
                file_name = "temp_audio.wav"
                save_audio_data(audio_buffer[:BUFFER_SIZE], file_name)
                transcribed_text = transcribe_audio(file_name)
                logger.info(f"Transcribed text: {transcribed_text}")

                # Keep the remaining audio data in the buffer
                audio_buffer = audio_buffer[BUFFER_SIZE:]
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
    finally:
        connected.remove(websocket)


def save_audio_data(audio_data, file_name):
    try:
        with wave.open(file_name, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(BIT_DEPTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data)
    except Exception as e:
        logger.error(f"Failed to save audio data: {e}")


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
                prompt="you will listen for only spanish or english",
            )
        return response
    except Exception as e:
        logging.error(f"Failed to transcribe audio: {e}")
        return ""


start_server = websockets.serve(handle_audio, "localhost", 8765)
logger.info("Starting server at ws://localhost:8765")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
