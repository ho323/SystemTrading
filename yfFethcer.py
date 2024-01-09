from lib.engines import YHFOHLCVFetcher
from lib.utils import save_ohlcv_to_pkl

fetcher = YHFOHLCVFetcher()

tickers = ["AAPL", "MSFT"]
intervals = ["1d", "1wk"]

for ticker in tickers:
    for interval in intervals:
        df = fetcher.get_ohlcv(ticker=ticker, interval=interval)

        file_name = f"{ticker}_{interval}_ohlcv_upbit"
        save_ohlcv_to_pkl(df, file_name)
