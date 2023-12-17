# server.py

import asyncio
import websockets
import logging
from hls_stream_manager import HLSStreamManager

# Server configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8765
HLS_OUTPUT_DIR = "/Users/hassen/Dev/Jeenie/demo-video-node-audio_connector/python_websocket_server/hls_content"  # Set the directory where HLS files will be stored
HTTP_SERVER_PORT = 8000  # Port for the HTTP server to serve HLS content

# Dictionary to track HLSStreamManager instances for each stream_id
hls_managers = {}

logging.basicConfig(level=logging.INFO)


async def handle_audio(websocket, path):
    stream_id = path.replace(
        "/socket/", "", 1
    )  # TODO: Stream Id still broken, shows up like 'socket/c01123d6-1328-4e65-a641-6f4ec156b5c1' (check again)
    logging.info(f"Stream {stream_id} connected")

    # Create a new HLSStreamManager for the stream_id if it doesn't exist
    if stream_id not in hls_managers:
        hls_managers[stream_id] = HLSStreamManager(
            stream_id, HLS_OUTPUT_DIR, SERVER_HOST, HTTP_SERVER_PORT
        )
        hls_url = hls_managers[stream_id].get_hls_playlist_url()
        logging.info(f"HLS URL for stream {stream_id}: {hls_url}")

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                hls_managers[stream_id].write_audio_data(message)
    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Stream {stream_id} connection closed")
        hls_managers[stream_id].cleanup()
        del hls_managers[stream_id]


async def start_server():
    async with websockets.serve(handle_audio, SERVER_HOST, SERVER_PORT):
        logging.info(f"WebSocket server started on ws://{SERVER_HOST}:{SERVER_PORT}")
        await asyncio.Future()  # Run server indefinitely


if __name__ == "__main__":
    asyncio.run(start_server())
