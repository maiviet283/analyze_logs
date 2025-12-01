from .base_streamer import BaseStreamer

class ZeekStreamer(BaseStreamer):
    def __init__(self):
        super().__init__(index_pattern="zeek-logs-*")
