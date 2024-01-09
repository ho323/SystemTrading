from lib.engines import UpbitOHLCVFetcher
from lib.datasets import fill_empty_rows_volume_zero
from lib.utils import save_ohlcv_to_pkl


fetcher = UpbitOHLCVFetcher()

tickers = fetcher.get_all_tickers_list()    # ["KRW-BTC", "KRW-ETH"] 로 설정해도 됨
intervals = ["days", "weeks"]   # 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m, days, weeks, months

for ticker in tickers:
    for interval in intervals:
        df = fetcher.get_ohlcv(ticker=ticker, interval=interval)
        df = fill_empty_rows_volume_zero(df)

        file_name = f"{ticker}_{interval}_ohlcv_upbit"
        save_ohlcv_to_pkl(df, file_name)
