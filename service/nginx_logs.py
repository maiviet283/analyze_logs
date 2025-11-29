from .base_logs import BaseLogFetcher


class NginxLogFetcher(BaseLogFetcher):
    def __init__(self):
        super().__init__(index_pattern="nginx-logs-*")