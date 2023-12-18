import asyncio
import websockets
import logging

logger = logging.getLogger(__name__)


async def connect():
    """Connect to the websocket server and handle messages."""
    uri = "ws://localhost:8765/socket/fbf3c3d5-10e3-462a-8f88-7a9cfcd865dd"
    async with websockets.connect(uri) as websocket:
        logger.info("Connected to the server.")
        await websocket.send("Hello, server!")  # Send a test message to the server

        async for message in websocket:
            logger.info("Message from server: %s", message)


try:
    asyncio.get_event_loop().run_until_complete(connect())
except Exception as e:
    logger.error("WebSocket error observed: %s", e)
finally:
    logger.info("Disconnected from the server.")
