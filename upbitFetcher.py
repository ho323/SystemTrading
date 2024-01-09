from lib.engines import UpbitOHLCVFetcher
from lib.utils import save_ohlcv_to_pkl

fetcher = UpbitOHLCVFetcher()

tickers = ["KRW-BTC", "KRW-ETH"]
intervals = ["240m", "days"]   # 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m, days, weeks, months

for ticker in tickers:
    for interval in intervals:
        df = fetcher.get_ohlcv(ticker=ticker, interval=interval)

        file_name = f"{ticker}_{interval}_ohlcv_upbit"
        save_ohlcv_to_pkl(df, file_name)
