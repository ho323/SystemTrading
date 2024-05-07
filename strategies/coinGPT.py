import os
from dotenv import load_dotenv
load_dotenv()
import requests
import pyupbit
import pandas as pd
import pandas_ta as ta
import json
from openai import OpenAI
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


upbit = pyupbit.Upbit(os.getenv("UPBIT_ACCESS_KEY"), os.getenv("UPBIT_SECRET_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def crawl_google_news(keyword):
    service = Service(ChromeDriverManager().install())

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        base_url = f'https://news.google.com/search?q={keyword}' # &hl=ko&gl=KR&ceid=KR:ko
        search_url = base_url.format(keyword=keyword + ' when:1d') # 지난 24시간
        
        driver.get(search_url)
        time.sleep(5) # 페이지가 완전히 로드될 때까지 기다림
        
        titles = driver.find_elements(By.CLASS_NAME, 'JtKRv')
        timestamps = driver.find_elements(By.CLASS_NAME, 'hvbAAd')
        
        result = []
        for title, timestamp in zip(titles, timestamps):
            result.append({
                "Title": title.text,
                "Timestamp": timestamp.get_attribute('datetime'), 
                "Time": timestamp.text
                })
        
        return json.dumps(result)
    finally:
        driver.quit()

def fetch_and_prepare_data(ticker):
    df = pyupbit.get_ohlcv(ticker, "day", count=90)

    def add_indicators(df):
        # Moving Averages
        df['SMA_20'] = ta.sma(df['close'], length=20)
        df['SMA_60'] = ta.sma(df['close'], length=60)

        # RSI
        df['RSI_14'] = ta.rsi(df['close'], length=14)

        # Bollinger Bands
        df['Middle_Band'] = df['close'].rolling(window=20).mean()
        std_dev = df['close'].rolling(window=20).std()
        df['Upper_Band'] = df['Middle_Band'] + (std_dev * 2)
        df['Lower_Band'] = df['Middle_Band'] - (std_dev * 2)

        return df

    df = add_indicators(df)
    df = df.to_json(orient='split')

    return json.dumps(df)

def get_current_status():
    orderbook = pyupbit.get_orderbook(ticker="KRW-BTC")
    current_time = orderbook['timestamp']
    btc_balance = 0
    krw_balance = 0
    btc_avg_buy_price = 0
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == "BTC":
            btc_balance = b['balance']
            btc_avg_buy_price = b['avg_buy_price']
        if b['currency'] == "KRW":
            krw_balance = b['balance']

    current_status = {'current_time': current_time, 'orderbook': orderbook, 'btc_balance': btc_balance, 'krw_balance': krw_balance, 'btc_avg_buy_price': btc_avg_buy_price}
    return json.dumps(current_status)

def fetch_fear_and_greed_index(limit=1, date_format=''):
    """
    Fetches the latest Fear and Greed Index data.
    Parameters:
    - limit (int): Number of results to return. Default is 1.
    - date_format (str): Date format ('us', 'cn', 'kr', 'world'). Default is '' (unixtime).
    Returns:
    - dict or str: The Fear and Greed Index data in the specified format.
    """
    base_url = "https://api.alternative.me/fng/"
    params = {
        'limit': limit,
        'format': 'json',
        'date_format': date_format
    }
    response = requests.get(base_url, params=params)
    myData = response.json()['data']
    resStr = ""
    for data in myData:
        resStr += str(data)
    return resStr

def get_instructions(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            instructions = file.read()
        return instructions
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print("An error occurred while reading the file:", e)

def analyze_data_with_gpt(ticker="KRW-BTC", keyword="bitcoin", model="gpt-3.5-turbo"):
    try:
        data_json = fetch_and_prepare_data(ticker)
        news_json = crawl_google_news(keyword)
        fear_and_greed = fetch_fear_and_greed_index(limit=30)
        current_status = get_current_status()

        instructions_path = "./gpt/instructions.md"
        instructions = get_instructions(instructions_path)
        if not instructions:
            print("No instructions found.")
            return None
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": news_json},
                {"role": "user", "content": data_json},
                {"role": "user", "content": fear_and_greed},
                {"role": "user", "content": current_status}
            ],
            response_format={"type":"json_object"}
        )
        advice = response.choices[0].message.content
        return json.loads(advice)
    except Exception as e:
        print(f"Error in analyzing data with GPT: {e}")
        return None
    
def strategy():
    ticker = "KRW-BTC"
    keyword = "bitcoin"

    advice = analyze_data_with_gpt(
        ticker=ticker, 
        keyword=keyword, 
        model="gpt-4-turbo-preview"
    )

    action = advice["decision"]
    percentage = advice["percentage"]
    price = None    # 시장가

    if percentage > 1:
        percentage /= 100

    return ticker, action, percentage, price