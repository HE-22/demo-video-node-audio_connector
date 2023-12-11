import asyncio
import websockets
from urllib.parse import urlparse
import logging

connected = set()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# TODO: Per person stream audio
# TODO: proccess audio
# TODO: send audio back to client


async def handle_audio(websocket, path):
    """Handle incoming audio data over websocket."""
    # Register.
    connected.add(websocket)
    try:
        while True:
            message = await websocket.recv()
            logger.info("Received audio data: %s", message)
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
    finally:
        # Unregister.
        connected.remove(websocket)


start_server = websockets.serve(handle_audio, "localhost", 8765)

logger.info("Starting server at: %s", "ws://localhost:8765")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
