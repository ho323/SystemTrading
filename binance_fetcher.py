from tqdm import tqdm

from lib.engines import BinanceOHLCVFetcher
from lib.datasets import fill_empty_rows_volume_zero
from lib.utils import save_ohlcv_to_csv
# from concurrent.futures import ThreadPoolExecutor, as_completed


ticker = "SEIUSDT"      # ALL로 하면 모든 종목 가져옴
interval = "1m"
fill_empty = True       # 빈 값을 채워서 저장할지 결정
save_path = "./data/binance"
file_name = f"{ticker}_{interval}_ohlcv_binance"

# 종목 OHLCV 데이터 가져와서 저장하는 함수
def process_ticker(fetcher, ticker, fill_empty=False):
    df = fetcher.get_all_ohlcv(ticker)
    if fill_empty:
        df = fill_empty_rows_volume_zero(df)

    if not df.empty:
        save_ohlcv_to_csv(df, save_path, file_name)

if __name__ == '__main__':
    print(f"Binance {ticker} OHLCV 데이터 수집 시작")

    try:
        fetcher = BinanceOHLCVFetcher(ticker, interval)
        
        if ticker == "ALL":
            tickers = fetcher.get_all_tickers(isDetails=False)  # 바이낸스 모든 종목 정보 가져옴 (미완성)
            for ticker in tqdm(tickers):
                process_ticker(fetcher, ticker['market'], fill_empty)

                # # 모든 종목의 데이터를 가져와서 저장 병렬 처리
                # with ThreadPoolExecutor() as executor:
                #     futures = {executor.submit(process_ticker, fetcher, ticker): ticker for ticker in tickers}

                #     for future in tqdm(as_completed(futures), total=len(futures)):
                #         ticker = futures[future]
                #         try:
                #             df = future.result()
                #             if not df.empty:
                #                 save_ohlcv_to_csv(df, save_path, file_name)
                #         except Exception as e:
                #             print(f"Error fetching data for {ticker}: {e}")
        else:
            process_ticker(fetcher, ticker, fill_empty)

    except Exception as e:
        print("잘못된 입력", e)

