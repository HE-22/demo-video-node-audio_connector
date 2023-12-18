# # server.py

# import asyncio
# import websockets
# import logging
# import subprocess
# import logging
# import os
# import shutil

# # Server configuration
# SERVER_HOST = "localhost"
# SERVER_PORT = 8765

# HLS_SERVER_DIRECTORY = "/Users/hassen/Dev/Jeenie/optimized_hls_server/hls_files"

# logging.basicConfig(level=logging.INFO)


# def process_audio_with_ffmpeg(audio_bytes, segment_index):
#     """
#     Process incoming audio bytes using FFmpeg to transcode and segment them.
#     """
#     try:
#         ffmpeg_command = [
#             "ffmpeg",
#             "-i",
#             "-",  # Read from stdin
#             "-f",
#             "segment",  # Format to segment
#             "-segment_time",
#             "10",  # Duration of each segment in seconds
#             "-c:a",
#             "aac",  # Audio codec
#             f"segment_{segment_index:03d}.ts",  # Output segment file name
#         ]

#         # Start the FFmpeg process
#         process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
#         process.stdin.write(audio_bytes)
#         process.stdin.close()
#         process.wait()  # Wait for FFmpeg to finish processing

#         return f"segment_{segment_index:03d}.ts"

#     except subprocess.CalledProcessError as e:
#         logging.error(f"FFmpeg processing failed: {e}")
#         return None


# def generate_m3u8_playlist(latest_segment):
#     """
#     Generate or update the M3U8 playlist file.
#     """
#     try:
#         with open("stream.m3u8", "a") as playlist:
#             playlist.write(f"#EXTINF:10,\n{latest_segment}\n")
#     except IOError as e:
#         logging.error(f"Failed to update M3U8 playlist: {e}")


# def transfer_files_to_hls_server(file_name, hls_server_directory):
#     """
#     Transfer segment files and M3U8 file to the HLS server.
#     """
#     try:
#         shutil.move(file_name, os.path.join(hls_server_directory, file_name))
#     except Exception as e:
#         logging.error(f"Failed to transfer files to HLS server: {e}")


# # MAIN SERVER LOGIC
# async def handle_audio(websocket, path):
#     segment_index = 0  # Initialize segment index
#     try:
#         async for message in websocket:
#             if isinstance(message, bytes):
#                 # Process audio segment
#                 segment_file = process_audio_with_ffmpeg(message, segment_index)
#                 if segment_file:
#                     # Update M3U8 playlist
#                     generate_m3u8_playlist(segment_file)
#                     # Transfer files to HLS server
#                     transfer_files_to_hls_server(segment_file, HLS_SERVER_DIRECTORY)
#                     segment_index += 1
#     except Exception as e:
#         logging.error(f"WebSocket error: {e}")


# async def start_server():
#     # Start the WebSocket server for handling audio data
#     async with websockets.serve(handle_audio, SERVER_HOST, SERVER_PORT):
#         logging.info(f"WebSocket server started on ws://{SERVER_HOST}:{SERVER_PORT}")
#         await asyncio.Future()  # Run server indefinitely


# if __name__ == "__main__":
#     asyncio.run(start_server())
