import os
import pandas as pd

def save_ohlcv_to_csv(candle_data, save_path='./', file_name='ohlcv'):
    """
    데이터를 CSV 파일로 저장하는 메서드

    :param candle_data: 데이터를 담고 있는 Pandas DataFrame
    :param save_path: 저장할 경로 (기본값: 현재 디렉터리)
    :param file_name: 저장할 파일 이름 (포맷: ticker_interval_datatype_source)
    """
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    file_path = os.path.join(save_path, f"{file_name}.csv")
    candle_data.to_csv(file_path)

def load_ohlcv_csv(file_path: str):
    """
    OHLCV CSV 파일을 불러오는 메서드

    :param path: 예시: './data/KRW-BTC_1m_ohlcv_upbit.csv'
    :return: PandasDataFrame
    """
    df = pd.read_csv(file_path, index_col=0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df
