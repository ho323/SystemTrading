import os
import re
import pyupbit
import pandas as pd
import schedule
import time
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import importlib.util

upbit = pyupbit.Upbit(os.getenv("UPBIT_ACCESS_KEY"), os.getenv("UPBIT_SECRET_KEY"))

def execute_buy_upbit(ticker, percentage, balance, price=None):
    """
    Upbit 매수 주문 함수
    price를 비우면 시장가 매수
    :param ticker: 주문할 ticker
    :param percentage: 가용 금액 대비 주문 비율
    :param price: 호가
    """
    print(f"Attempting to buy {ticker} with KRW balance...")
    try:
        krw_balance = upbit.get_balance("KRW")
        amount_to_invest = krw_balance * (percentage)
        if price:
            result = upbit.buy_limit_order(ticker, price, amount_to_invest*0.9995)  # Adjust for fees
        else:
            result = upbit.buy_market_order(ticker, amount_to_invest*0.9995)  # Adjust for fees
        print("Buy order successful:", result)
    except Exception as e:
        print(f"Failed to execute buy order: {e}")

def execute_sell_upbit(ticker, percentage, balance, price=None):
    """
    Upbit 매도 주문 함수 
    price를 비우면 시장가 매도
    :param ticker: 주문할 ticker
    :param percentage: 가용 금액 대비 주문 비율
    :param price: 호가
    """
    print(f"Attempting to sell {ticker}...")
    try:
        btc_balance = upbit.get_balance(ticker)
        amount_to_sell = btc_balance * (percentage)
        if price:
            result = upbit.sell_limit_order(ticker, price, amount_to_sell)
        else:
            result = upbit.sell_market_order(ticker, amount_to_sell)
        print("Sell order successful:", result)
    except Exception as e:
        print(f"Failed to execute sell order: {e}")

def excute_strategy(st):
    try:
        spec = importlib.util.spec_from_file_location(st, f"./strategies/{st}.py")
        strategy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy)

        ticker, action, percentage, price = strategy.strategy()

        return ticker, action, percentage, price
    except Exception as e:
        print(f"{st}전략 실행 실패 ", e)


def make_decision_and_execute(st, market, balance):
    """
    전략 및 주문 실행 함수
    :param st: 실행할 전략
    :param balance: 해당 전략에 할당된 가용 금액
    """
    print(f"Making decision of {st} in {market} and executing...")
    try:
        ticker, action, percentage, price = excute_strategy(st)
        if market == "upbit":
            if action == "buy":
                execute_buy_upbit(ticker, percentage, balance, price)
            elif action == "sell":
                execute_sell_upbit(ticker, percentage, balance, price)
        elif market == "yahoo":
            return
        elif market == "binance":
            return
        elif market == "yahoo":
            return
        else:
            print(f"{market} is not available market")
            return

        return ticker, action, percentage, price
    except Exception as e:
        print(f"Failed to make decisions in strategies: {e}")

def load_strategies():
    with open('./config.json') as file:
        strategies = json.load(file)

    return strategies

if __name__ == "__main__":
    strategies = load_strategies()

    for st, v in strategies.items():
        cycle, market, balance, t = v # 7 or "monday", '08:00', 500000
        if type(cycle) == int:
            schedule.every(cycle).day.at(t).do(make_decision_and_execute, st, market, balance)
        elif cycle == "monday":
            schedule.every().monday.at(t).do(make_decision_and_execute, st, market, balance)
        elif cycle == "tuesday":
            schedule.every().tuesday.at(t).do(make_decision_and_execute, st, market, balance)
        elif cycle == "wednesday":
            schedule.every().wednesday.at(t).do(make_decision_and_execute, st, market, balance)
        elif cycle == "thursday":
            schedule.every().thursday.at(t).do(make_decision_and_execute, st, market, balance)
        elif cycle == "friday":
            schedule.every().friday.at(t).do(make_decision_and_execute, st, market, balance)
        elif cycle == "saturday":
            schedule.every().saturday.at(t).do(make_decision_and_execute, st, market, balance)
        elif cycle == "sunday":
            schedule.every().sunday.at(t).do(make_decision_and_execute, st, market, balance)

    print("자동 매매 시작\n", strategies)
    while True:
        schedule.run_pending()
        time.sleep(1)
