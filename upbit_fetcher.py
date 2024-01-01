# from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from lib.engines import UpbitOHLCVFetcher
from lib.datasets import fill_empty_rows_volume_zero
from lib.utils import save_ohlcv_to_csv


ticker = "KRW-SEI"      # ALL로 하면 모든 종목 가져옴
interval = "1m"
fill_empty = True       # 빈 값을 채워서 저장할지 결정
save_path = "./data/upbit"
file_name = f"{ticker}_{interval}_ohlcv_upbit"

# 종목 OHLCV 데이터 가져와서 저장하는 함수
def process_ticker(fetcher, ticker, fill_empty=False):
    df = fetcher.get_all_ohlcv(ticker)
    if fill_empty:
        df = fill_empty_rows_volume_zero(df)

    if not df.empty:
        save_ohlcv_to_csv(df, save_path, file_name)

if __name__ == '__main__':
    print(f"Upbit {ticker} OHLCV 데이터 수집 시작")

    try:
        fetcher = UpbitOHLCVFetcher(ticker, interval)
        
        if ticker == "ALL":
            tickers = fetcher.get_all_tickers(isDetails=False) # 업비트 모든 종목의 ticker를 가져옴
            for ticker in tqdm(tickers):
                process_ticker(fetcher, ticker['market'], fill_empty)

        else:
            process_ticker(fetcher, ticker, fill_empty)

        print(f"{ticker} 완료")

    except Exception as e:
        print("잘못된 입력", e)

