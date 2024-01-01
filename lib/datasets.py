import time
import requests
import pandas as pd

from tqdm import tqdm


def get_empty_rows(df):
    """
    DataFrame의 비어있는 행의 timestamp를 확인하는 메서드
    
    :param df: 검사할 DataFrame 
    :return: 비어있는 행의 timestamp가 담겨있는 list
    """
    # timestamp 컬럼을 datetime 형식으로 변환
    df.loc[:,'timestamp'] = pd.to_datetime(df.timestamp)
    df = df.sort_values(by='timestamp')

    # 모든 1분 간격의 timestamp 생성
    start_date = df.timestamp.min()
    end_date = df.timestamp.max()
    all_timestamps = pd.date_range(start=start_date, end=end_date, freq='1T')

    # 비어있는 행의 timestamp 확인
    empty_rows_timestamp = list(set(all_timestamps) - set(df.timestamp))

    return empty_rows_timestamp

def fill_empty_rows_volume_zero(df):
    """
    비어있는 timestamp를 검사하여 ohlc 값을 이전 값의 종가, 거래량을 0으로 채워서 Pandas DataFrame으로 반환하는 메서드
    
    :param df: 검사하고 채워넣을 Pandas DataFrame
    :return: Pandas DataFrame
    """
    df.loc[:, 'timestamp'] = pd.to_datetime(df['timestamp'])

    ets = get_empty_rows(df)
    ets = sorted(ets)
    ets = pd.to_datetime(ets)
    
    for i in tqdm(range(len(ets)), desc="Filling empty"):
        et = ets[i]
        pt = et - pd.Timedelta(minutes=1)
        
        a = df[df['timestamp'] == pt]
        a.loc[:, 'timestamp'] = et
        a.loc[:, 'volume'] = 0

        df = pd.concat([df, a])
        df.sort_values(by='timestamp', inplace=True)
        df.reset_index(inplace=True, drop=True)
        
    return df

def fill_empty_rows_mean(self, df):
    """
    비어있는 행을 검사하여 ohlcv 값을 이전 값과 다음 값의 평균으로 채워서 Pandas DataFrame을 반환하는 메서드
    
    :param df: 검사하고 채워넣을 Pandas DataFrame
    :return: Pandas DataFrame
    """
    empty_rows_timestamp = get_empty_rows(df)

    url = "https://api.upbit.com/v1/market/all?isDetails=false"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    tickers = response.json()
    
    self.params['count'] = 1

    data_list = []
    for timestamp in tqdm(empty_rows_timestamp):
        self.params['to'] = timestamp

        response = requests.get(self.url, headers=self.headers, params=self.params)
        data = response.json()

        if len(data) == 0:
            break

        data_list.extend(data)

        time.sleep(0.1)


    fill_df = pd.DataFrame(data_list)
    fill_df = fill_df[['candle_date_time_utc', 'opening_price', 'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']]
    fill_df = fill_df.rename(columns={
        'candle_date_time_utc' : 'timestamp', 
        'opening_price' : 'open',
        'high_price' : 'high', 
        'low_price' : 'low', 
        'trade_price' : 'close', 
        'candle_acc_trade_volume' : 'volume',
    })

    df = pd.concat([df, fill_df])
    df.sort_values(by='timestamp', inplace=True)
    df.reset_index(inplace=True, drop=True)

    return df