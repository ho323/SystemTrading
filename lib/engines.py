import jwt
import uuid
import hashlib
import random

import time
import requests
import pandas as pd

from datetime import datetime
from urllib.parse import urlencode, unquote


class UpbitOHLCVFetcher:
    def __init__(self):
        self.server_url = 'https://api.upbit.com/v1'

    def get_all_tickers_list(self, isDetails=False):
        """
        업비트 전 종목의 ticker를 가져오는 메서드
        :param is_details: 유의종목 필드과 같은 상세 정보 노출 여부(선택 파라미터)
        """
        if isDetails:
            d = "true"
        else:
            d = "false"
        url = f"{self.server_url}/market/all?isDetails={d}"
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers)
        tickers = response.json()

        tickers_list = [item['market'] for item in tickers if 'market' in item and item['market'].startswith('KRW-')]

        return tickers_list

    def _convert_list_to_df(self, data_list):
        
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

    def get_ohlcv(self, ticker, interval="days", start_date=datetime(2016,1,1), end_date=datetime.now(), count=200):
        """
        과거 모든 OHLCV 데이터를 Pandas DataFrame으로 가져오는 메서드

        :param ticker: 티커 ('KRW-BTC', 'KRW-ETH' 등)
        :param interval: 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m, days, weeks, months (기본값: days)
        :param end_date: 수집할 마지막 캔들 시간의 datetime 비우면 현재 시간
        :return: Pandas DataFrame
        """
        if interval[-1] == 'm':
            url = f"{self.server_url}/candles/minutes/{interval[:-1]}"
        else:
            url = f"{self.server_url}/candles/{interval}"
        params = {
            "market": ticker,
            "count": count, 
            "to": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        headers = {"accept": "application/json"}

        data_list = []
        while True:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if len(data) == 0:
                break

            data_list.extend(data)
            dt = data[-1]['candle_date_time_utc']
            params['to'] = dt

            if pd.to_datetime(dt) < start_date:
                break

            time.sleep(0.101)

        df = self._convert_list_to_df(data_list)

        print(f"[Upbit] {ticker} {interval} OHLCV 수집 완료")

        return df
    

class YHFOHLCVFetcher:
    def __init__(self):
        self.server_url = "https://query1.finance.yahoo.com/v7"

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

        url = f"{self.server_url}/finance/download/{ticker}"
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
        url = f"{self.server_url}/finance/download/{ticker}"
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


class UpbitExchanger:
    def __init__(self, access_key, secret_key):
        self.server_url = 'https://api.upbit.com/v1'
        self.access_key = access_key
        self.secret_key = secret_key

    def _get_authorization(self, query=None):
        """
        requests 시에 headers에 사용할 authorization 생성 메서드
        params 입력 시 SHA512 사용
        """
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        if query != None:
            query_string = unquote(urlencode(query, doseq=True)).replace("%5B%5D=", "[]=").encode("utf-8")

            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()

            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'

        jwt_token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        authorization = 'Bearer {}'.format(jwt_token)

        return authorization

    def get_account(self):
        """
        자산 조회 메서드
        """
        authorization = self._get_authorization()
        headers = {'Authorization': authorization}
        res = requests.get(self.server_url + '/accounts', headers=headers)

        return res.json()
    
    def request_order(self, ticker, side, ord_type, volume=None, price=None):
        """
        주문 요청 메서드

        :param ticker: 주문할 ticker (KRW-BTC, KRW-ETH 등)
        :param side: 매수, 매도 여부 (bid, ask)
        :param ord_type: 주문 종류 (지정가 주문 -limit, 시장가 매수 -price, 시장가 매도 -market)
        :param volume: 주문 수량 (지정가 주문, 시장가 매도 시 필수)
        :param price: 주문 가격 (지정가 주문, 시장가 매수 시 필수) ex)KRW-BTC 마켓에서 1BTC당 1,000 KRW로 거래할 경우, 값은 1000 이 된다.
        """
        params = {
            'market': ticker,
            'side': side,
            'ord_type': ord_type,
        }

        if ord_type == 'limit' or ord_type == 'price':
            params['price'] = price
        if ord_type == 'limit' or ord_type == 'market':
            params['volume'] = volume

        authorization = self._get_authorization(query=params)
        headers = {'Authorization': authorization}
        res = requests.post(self.server_url + '/orders', json=params, headers=headers)

        return res.json()
    
    def get_order_list(self, done=False):
        """
        주문 리스트 조회 메서드

        :param done: False - 미체결 주문 조회, True - 완료 주문 조회
        """
        if done:
            params = {'states[]': ['done', 'cancel']}
        else:
            params = {'states[]': ['wait', 'watch']}
    
        authorization = self._get_authorization(query=params)
        headers = {'Authorization': authorization}
        res = requests.post(self.server_url + '/orders', json=params, headers=headers)

        return res.json()

    def cancel_order(self, uuid):
        """
        주문 취소 메서드

        :param uuid: 취소할 주문의 UUID (필수)
        """
        params = {
            'uuid': uuid
        }
        authorization = self._get_authorization(query=params)
        headers = {'Authorization': authorization}
        res = requests.post(self.server_url + '/order', json=params, headers=headers)

        return res.json()

class KRXFetcher:
    def __init__(self):
        self.url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://data.krx.co.kr",
            "Referer": f"http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
    
    def get_kospi200_future(self, date, share=1, money=1, csvxls_isNo='false'):
        """
        코스피 200 선물 조회
        """
        stat = "MDCSTAT12501"
        prod_id = "KRDRVFUK2I"

        response = requests.post(
            url=self.url,
            headers=self.headers,
            data=f"bld=dbms/MDC/STAT/standard/{stat}&locale=ko_KR&trdDd={date}&prodId={prod_id}&trdDdBox1={date}&trdDdBox2={date}&mktTpCd=T&rghtTpCd=T&share={share}&money={money}&csvxls_isNo={csvxls_isNo}"
        )

        rand_value = random.random()
        time.sleep(rand_value)

        df = pd.DataFrame(response.json()['output'])

        return df
    
    def get_kospi200_option(self, date, weekly=1, share=1, money=1, csvxls_isNo='false'):
        """
        코스피 200 옵션 조회
        """
        stat = "MDCSTAT12502"

        if weekly == 1:
            prod_id = "KRDRVOPK2I"
        elif weekly == 2:  # 위클리 옵션(월)
            prod_id = "KRDRVOPWKI"
        elif weekly == 3:  # 위클리 옵션(목)
            prod_id = "KRDRVOPWKM"

        response = requests.post(
            url=self.url,
            headers=self.headers,
            data=f"bld=dbms/MDC/STAT/standard/{stat}&locale=ko_KR&trdDd={date}&prodId={prod_id}&trdDdBox1={date}&trdDdBox2={date}&mktTpCd=T&rghtTpCd=T&share={share}&money={money}&csvxls_isNo={csvxls_isNo}"
        )

        rand_value = random.random()
        time.sleep(rand_value)

        df = pd.DataFrame(response.json()['output'])

        return df

    def get_etf_info(self):
        stat = "MDCSTAT04601"

        response = requests.post(
            url=self.url,
            headers=self.headers,
            data=f"bld=dbms/MDC/STAT/standard/{stat}&locale=ko_KR&share=1&csvxls_isNo=false"
        )
        df = pd.DataFrame(response.json()['output'])

        return df
    
    def get_individual_performence_by_investor(self, short_code, full_code, start_date, end_date, money=1):
        stat = "MDCSTAT04903"
        
        response = requests.post(
            url=self.url,
            headers=self.headers,
            data=f"bld=dbms/MDC/STAT/standard/{stat}&locale=ko_KR&inqTpCd=2&inqCondTpCd1=1&inqCondTpCd2=1&tboxisuCd_finder_secuprodisu1_1={short_code}&isuCd={full_code}&strtDd={start_date}&endDd={end_date}&detailView=1&money={money}&csvxls_isNo=false"
        )

        df = pd.DataFrame(response.json()['output'])
        if len(df) == 0:
            return df
        
        return  df