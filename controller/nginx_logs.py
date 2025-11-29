from service.zeek_logs import ZeekLogFetcher

django_fetcher = ZeekLogFetcher()

df = django_fetcher.fetch_logs(seconds=30)

print(django_fetcher.show_columns())
print(django_fetcher.head(5))
