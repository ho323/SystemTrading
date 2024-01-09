import pandas as pd


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
    df.reset_index(inplace=True)

    # 'timestamp' 열을 datetime 객체로 변환
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 데이터 주기 계산
    df['delta'] = df['timestamp'].diff()  # 인접한 timestamp 간의 차이 계산
    common_delta = df['delta'].mode()[0]  # 가장 흔한 차이(주기) 계산

    # 완전한 timestamp 시퀀스 생성
    full_range = pd.date_range(start=df['timestamp'].min(), end=df['timestamp'].max(), freq=common_delta)

    # 새로운 DataFrame 생성 및 기존 데이터 병합
    new_df = pd.DataFrame(full_range, columns=['timestamp'])
    df = new_df.merge(df, on='timestamp', how='left')

    # 누락된 'close' 값들 채우기
    df['close'].ffill(inplace=True)

    # 'open', 'high', 'low'가 NaN이고 'close'에 값이 있는 행 찾기
    mask = df['open'].isna() & df['high'].isna() & df['low'].isna() & df['close'].notna()

    # 해당 행들의 'open', 'high', 'low'를 'close' 값으로 채우기
    df.loc[mask, ['open', 'high', 'low']] = df.loc[mask, 'close']

    # 데이터에 adjclose 있으면 수행
    if 'adjclose' in df.columns:
        adjmask = df['adjclose'].isna() & df['close'].notna()
        df.loc[adjmask, ['adjclose']] = df.loc[adjmask, 'close']

    # 누락된 'volume' 값 채우기
    df['volume'] = df['volume'].fillna(0)

    # 불필요한 'delta' 열 삭제
    df.drop(columns=['delta'], inplace=True)

    # index를 timestamp로
    df.set_index('timestamp', inplace=True)

    return df
