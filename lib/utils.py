import os
import shutil
import pandas as pd


def save_ohlcv_to_pkl(data, file_name):
    temp_path = f"./data/temp/{file_name}.pkl"
    store_path = f"./data/store/{file_name}.pkl"

    data.to_pickle(temp_path)

    if not os.path.exists(store_path):
        shutil.copy(temp_path, store_path)
    else:
        temp = pd.read_pickle(temp_path)
        store = pd.read_pickle(store_path)

        store.update(temp)

        overlap_index = store.index.intersection(temp.index)
        store.loc[overlap_index] = temp.loc[overlap_index]

        store.to_pickle(store_path)


def load_ohlcv_pkl(file_path: str):
    """
    OHLCV pickle 파일을 불러오는 메서드

    :param path: 예시: './data/store/KRW-BTC_days_ohlcv_upbit.pkl'
    :return: PandasDataFrame
    """
    df = pd.read_pickle(file_path)
    df.index = pd.to_datetime(df.index)
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

    return df
