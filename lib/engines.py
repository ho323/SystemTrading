import time
import requests
import pandas as pd

from datetime import datetime


class UpbitOHLCVFetcher:
    def __init__(self):
        pass

    def get_all_tickers_list(self, isDetails=False):
        """
        업비트 전 종목의 ticker를 가져오는 메서드
        :param is_details: 유의종목 필드과 같은 상세 정보 노출 여부(선택 파라미터)
        """
        if isDetails:
            d = "true"
        else:
            d = "false"
        url = f"https://api.upbit.com/v1/market/all?isDetails={d}"
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers)
        tickers = response.json()

        tickers_list = [item['market'] for item in tickers if 'market' in item and item['market'].startswith('KRW-')]

        return tickers_list

    def convert_list_to_df(self, data_list):
        
        df = pd.DataFrame(data_list)
        df = df[['candle_date_time_utc', 'opening_price', 'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']]
        df = df.rename(columns={
            'candle_date_time_utc' : 'timestamp', 
            'opening_price' : 'open',
            'high_price' : 'high', 
            'low_price' : 'low', 
            'trade_price' : 'close', 
            'candle_acc_trade_volume' : 'volume',
        })
        df.loc[:,'timestamp'] = pd.to_datetime(df.timestamp)
        df = df[::-1].reset_index(drop=True)
        df = df.set_index('timestamp')

        return df

    def get_ohlcv(self, ticker, interval="days", end_date=datetime.now()):
        """
        과거 모든 OHLCV 데이터를 Pandas DataFrame으로 가져오는 메서드

        :param ticker: 티커 ('KRW-BTC', 'KRW-ETH' 등)
        :param interval: 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m, days, weeks, months (기본값: days)
        :param end_date: 수집할 마지막 캔들 시간의 datetime 비우면 현재 시간
        :return: Pandas DataFrame
        """
        url = f"https://api.upbit.com/v1/candles"
        if interval[-1] == 'm':
            url = f"{url}/minutes/{interval[:-1]}"
        else:
            url = f"{url}/{interval}"
        params = {
            "market": ticker,
            "count": 200, 
            "to": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        headers = {"accept": "application/json"}

        # print(f"[Upbit] {ticker} {interval} OHLCV 수집 시작")

        data_list = []
        while True:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if len(data) == 0:
                break

            data_list.extend(data)
            dt = data[-1]['candle_date_time_utc']
            params['to'] = dt

            time.sleep(0.11)

        df = self.convert_list_to_df(data_list)

        print(f"[Upbit] {ticker} {interval} OHLCV 수집 완료")

        return df
    
    def get_current_ohlcv(self, ticker, interval="days", count=1):
        """
        현재 OHLCV 데이터를 Pandas DataFrame으로 가져오는 메서드

        :param ticker: 티커 ('KRW-BTC', 'KRW-ETH' 등)
        :param interval: 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m, days, weeks, months (기본값: days)
        :return: Pandas DataFrame
        """
        url = f"https://api.upbit.com/v1"
        if interval[-1] == 'm':
            url = f"{url}/candles/minutes/{interval[:-1]}"
        else:
            url = f"{url}/candles/{interval}"
        params = {
            "market": ticker,
            "count": count, 
        }
        headers = {"accept": "application/json"}

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        df = self.convert_list_to_df(data)

        return df

  

class YHFOHLCVFetcher:
    def __init__(self):
        pass

    def get_ohlcv(self, ticker, interval="1d", start_date=None, end_date=None):
        """
        과거 OHLCV 데이터를 Pandas DataFrame으로 가져오는 메서드
        
        :param ticker: str
        :param interval: str (기본값: 1d)
        :param start_date: datetime (비워두면 가장 오래된 시간)
        :param start_date: datetime (비워두면 가장 최근 시간)
        """
        if start_date == None and end_date == None:
            period1 = "0"
            period2 = "9999999999"  # Unix 타임스탬프에서 사용되는 최대값   

        if start_date != None and end_date == None:
            period1 = int(time.mktime(start_date.timetuple()))
            end_date = datetime.now()
            period2 = int(time.mktime(end_date.timetuple()))
        
        if start_date == None and end_date != None:
            period1 = "0"
            period2 = int(time.mktime(end_date.timetuple()))

        if start_date != None and end_date != None:
            period1 = int(time.mktime(start_date.timetuple()))
            period2 = int(time.mktime(end_date.timetuple()))

        url = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}"
        params = f"?interval={interval}&period1={period1}&period2={period2}&events=history&includeAdjustedClose=true"
        
        df = pd.read_csv(url+params, parse_dates=True)
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
        df = df.rename(columns={
            'Date' : 'timestamp', 
            'Open' : 'open',
            'High' : 'high', 
            'Low' : 'low', 
            'Close' : 'close', 
            'Adj Close' : 'adjclose',
            'Volume' : 'volume',
        })
        df = df.set_index('timestamp')


        print(f"[YahooFinance] {ticker} {interval} 수집 완료")

        return df
    
    def get_current_ohlcv(self, ticker, interval="1d", count=1):
        url = f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}"
        params = f"?interval={interval}&events=history&includeAdjustedClose=true"
        
        df = pd.read_csv(url+params, parse_dates=True)
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
        df = df.rename(columns={
            'Date' : 'timestamp', 
            'Open' : 'open',
            'High' : 'high', 
            'Low' : 'low', 
            'Close' : 'close', 
            'Adj Close' : 'adjclose',
            'Volume' : 'volume',
        })
        df = df.set_index('timestamp')

        return df
