# # hls_stream_manager.py

# import subprocess
# import os
# from collections import defaultdict
# from io import BytesIO
# from http.server import HTTPServer, SimpleHTTPRequestHandler
# import threading
# import logging


# class HLSStreamManager:
#     def __init__(self, stream_id, output_dir, server_host, server_port):
#         self.stream_id = stream_id
#         self.output_dir = output_dir
#         self.server_host = server_host
#         self.server_port = server_port
#         self.audio_buffers = defaultdict(lambda: [BytesIO(), BytesIO()])
#         self.active_buffer_index = 0
#         self.ffmpeg_process = self.start_ffmpeg_process()
#         self.http_server_thread = self.start_http_server()

#     def start_ffmpeg_process(self):
#         # Ensure the output directory exists
#         os.makedirs(self.output_dir, exist_ok=True)
#         # Start the FFmpeg process for encoding and segmenting the audio
#         ffmpeg_command = [
#             "ffmpeg",
#             "-i",
#             "-",
#             "-c:a",
#             "aac",
#             "-b:a",
#             "128k",
#             "-vn",
#             "-hls_time",
#             "4",
#             "-hls_playlist_type",
#             "event",
#             "-hls_segment_filename",
#             os.path.join(self.output_dir, f"{self.stream_id}_%03d.ts"),
#             os.path.join(self.output_dir, f"{self.stream_id}.m3u8"),
#         ]
#         return subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, bufsize=10**8)

#     def write_audio_data(self, data):
#         # Write audio data to the active buffer
#         buffer = self.audio_buffers[self.stream_id][self.active_buffer_index]
#         buffer.write(data)
#         # If the buffer exceeds a certain size, switch and process
#         if buffer.tell() >= 1024 * 1024:  # 1MB size for example
#             self.switch_and_process_buffer()

#     def switch_and_process_buffer(self):
#         # Switch the active buffer
#         self.active_buffer_index = 1 - self.active_buffer_index
#         # Get the buffer to process
#         buffer_to_process = self.audio_buffers[self.stream_id][
#             1 - self.active_buffer_index
#         ]
#         # Reset the buffer for future data
#         buffer_to_process.seek(0)
#         # Send the audio data to FFmpeg for processing
#         try:
#             self.ffmpeg_process.stdin.write(buffer_to_process.getvalue())
#             self.ffmpeg_process.stdin.flush()
#         except BrokenPipeError:
#             if self.ffmpeg_process and self.ffmpeg_process.stderr:
#                 ffmpeg_stderr = self.ffmpeg_process.stderr.read().decode()
#                 logging.error(f"FFmpeg error output: {ffmpeg_stderr}")
#             logging.error("FFmpeg process has exited unexpectedly. Restarting...")
#             self.ffmpeg_process = self.start_ffmpeg_process()
#         # Clear the buffer
#         buffer_to_process.seek(0)
#         buffer_to_process.truncate()

#     def get_hls_playlist_url(self):
#         # Return the URL to the HLS playlist
#         return f"http://{self.server_host}:{self.server_port}/{self.stream_id}.m3u8"

#     def cleanup(self):
#         # Close the FFmpeg process
#         if self.ffmpeg_process:
#             self.ffmpeg_process.stdin.close()
#             self.ffmpeg_process.terminate()
#             self.ffmpeg_process.wait()
#         # Remove the audio buffers
#         del self.audio_buffers[self.stream_id]

#     def start_http_server(self):
#         # Define a handler that serves files from the output directory
#         class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
#             def __init__(self, *args, **kwargs):
#                 # No need to pop 'directory' since it's already being handled by the lambda function
#                 super().__init__(*args, **kwargs)

#         # Create a handler class that is bound to the output directory
#         # The lambda function correctly passes 'directory' as a keyword argument
#         handler_class = lambda *args, **kwargs: CustomHTTPRequestHandler(
#             *args, **kwargs
#         )

#         # Start a new HTTP server in a separate thread to serve the HLS files
#         server = HTTPServer((self.server_host, self.server_port), handler_class)
#         thread = threading.Thread(target=server.serve_forever)
#         thread.daemon = (
#             True  # Set thread as a daemon so it automatically closes on program exit
#         )
#         thread.start()
#         return thread
