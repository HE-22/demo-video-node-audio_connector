# server.py

import asyncio
import websockets
import logging

# Server configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8765
FLASK_SERVER_WS_URI = "ws://localhost:5069/audio"  # WebSocket URI of the Flask server

logging.basicConfig(level=logging.INFO)


async def handle_audio(websocket, path):
    """
    Handle incoming audio data over WebSocket and forward it to the Flask server.
    """
    stream_id = path.split("/")[-1]  # Extract the stream_id from the path
    logging.info(f"Stream {stream_id} connected")

    # Establish a WebSocket connection to the Flask server
    try:
        async with websockets.connect(FLASK_SERVER_WS_URI) as flask_socket:
            logging.info(f"Connected to Flask server at {FLASK_SERVER_WS_URI}")

            # Forward the audio data to the Flask server
            try:
                async for message in websocket:
                    if isinstance(message, bytes):
                        await flask_socket.send(message)
                        logging.info(f"Forwarded audio data for stream {stream_id}")
            except Exception as e:
                logging.error(
                    f"Error while forwarding audio data for stream {stream_id}: {e}"
                )

    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Stream {stream_id} connection closed")
    except Exception as e:
        logging.error(f"Error while connecting to Flask server: {e}")


async def start_server():
    # Start the WebSocket server for handling audio data
    async with websockets.serve(handle_audio, SERVER_HOST, SERVER_PORT):
        logging.info(f"WebSocket server started on ws://{SERVER_HOST}:{SERVER_PORT}")
        await asyncio.Future()  # Run server indefinitely


if __name__ == "__main__":
    asyncio.run(start_server())
