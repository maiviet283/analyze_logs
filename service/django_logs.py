from .base_streamer import BaseStreamer

class DjangoStreamer(BaseStreamer):
    def __init__(self):
        super().__init__(index_pattern="django-logs-*")
