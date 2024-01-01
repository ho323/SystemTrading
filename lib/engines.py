import time
import requests
import pandas as pd

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tqdm import tqdm 


class UpbitOHLCVFetcher:
    def __init__(self, ticker, interval):
        """
        :param ticker: 티커 ('KRW-BTC', 'KRW-ETH' 등)
        :param interval: 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m, days, weeks, months
        """
        self.ticker = ticker
        self.interval = interval
        self.url = f"https://api.upbit.com/v1"
        self.params = {
            "market": self.ticker,
            "count": 200, 
            "to": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.headers = {"accept": "application/json"}

    def get_all_tickers(self, isDetails=False):
        """
        업비트 전 종목의 ticker를 가져오는 메서드
        :param is_details: 유의종목 필드과 같은 상세 정보 노출 여부(선택 파라미터)
        """
        if isDetails:
            d = "true"
        else:
            d = "false"
        url = f"{self.url}/market/all?isDetails={d}"
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers)
        tickers = response.json()

        return tickers

    def get_trade_months(self):
        """
        최초 거래 월까지의 개월 수를 알아내는 메서드
        tqdm으로 진행률을 표시할 때 유용함
        """
        url = f"{self.url}/candles/months"
        response = requests.get(url, headers=self.headers, params=self.params)
        data = response.json()

        first_trade_date = data[-1]['candle_date_time_utc']
        first_trade_date = datetime.strptime(first_trade_date, "%Y-%m-%dT%H:%M:%S")

        delta = relativedelta(datetime.now(), first_trade_date)
        result = delta.years * 12 + delta.months

        return result

    def get_all_ohlcv(self, ticker=None, to=datetime.now()):
        """
        모든 과거 데이터를 Pandas DataFrame으로 가져오는 메서드

        :param to: 마지막 캔들 시간의 datetime 혹은 str (포맷: yyyy-MM-dd'T'HH:mm:ss) 비우면 현재 시각
        :return: Pandas DataFrame
        """
        if self.interval[-1] == 'm':
            url = f"{self.url}/candles/minutes/{self.interval[:-1]}"
        else:
            url = f"{self.url}/candles/{self.interval}"

        if ticker:
            self.ticker = ticker
            self.params['market'] = ticker

        if type(to) != str:
            self.params['to'] = to.strftime("%Y-%m-%dT%H:%M:%S")

        total = self.get_trade_months()
        with tqdm(total=total, desc=self.ticker) as pbar:
            data_list = []
            pre_month = to.month
            while True:
                response = requests.get(url, headers=self.headers, params=self.params)
                data = response.json()

                if len(data) == 0:
                    break

                data_list.extend(data)
                dt = data[-1]['candle_date_time_utc']
                self.params['to'] = dt

                dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                if dt.month != pre_month:
                    pbar.update(1)
                pre_month = dt.month

                time.sleep(0.11)

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

        df = df[::-1].reset_index(drop=True)

        return df


class BinanceOHLCVFetcher:
    def __init__(self, ticker, interval):
        self.ticker = ticker
        self.interval = interval
        self.url = "https://api.binance.com/api/v1"
        self.params = {
            "symbol": ticker,
            "interval": interval,
            "limit": 1000, 
            "startTime": int(datetime(2015, 1, 1).timestamp()) * 1000,
            "endTime": int(datetime.now().timestamp()) * 1000
        }

    def get_trade_months(self, ticker=None):
        if ticker:
            self.ticker = ticker

        url = f"https://api.binance.com/api/v1/klines?symbol={self.ticker}&interval=1M&limit=1000"
        
        response = requests.get(url)
        data = response.json()

        first_trade_date = pd.to_datetime(data[0][0], unit='ms')

        delta = relativedelta(datetime.now(), first_trade_date)
        result = delta.years * 12 + delta.months
        
        return result 

    
    def get_all_ohlcv(self, ticker=None, start_date=datetime(2015,1,1), end_date=None):
        """
        :param ticker: str
        :param start_date: datetime
        """
        url = f"{self.url}/klines"
        if ticker:
            self.ticker = ticker
            self.params["symbol"] = ticker

        self.params["startTime"] = int(start_date.timestamp()) * 1000,
        
        if end_date:
            self.params["endTime"] = int(end_date.timestamp()) * 1000,

        total = self.get_trade_months() + 1
        with tqdm(total=total, desc=self.ticker) as pbar:
            data_list = []
            pre_month = start_date.month
            while True:
                response = requests.get(url=url, params=self.params)
                data = response.json()

                if len(data) == 0:
                    break
                
                data_list.extend(data)

                dt = data[-1][0] + 1
                self.params["startTime"] = dt

                dt = pd.to_datetime(dt, unit='ms')
                if dt.month != pre_month:
                    pbar.update(1)
                
                pre_month = dt.month

        df = pd.DataFrame(data_list)

        # OHLCV만 가져옴
        df = df.iloc[:, :6]

        # 데이터 형태 변환
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], unit='ms')
        df.iloc[:, 1:] = df.iloc[:, 1:].astype(float)

        # 컬럼명 설정
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        return df