from .base_streamer import BaseStreamer

class NginxStreamer(BaseStreamer):
    def __init__(self):
        super().__init__(index_pattern="nginx-logs-*")
