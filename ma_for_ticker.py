import os
from datetime import datetime, timedelta
from typing import List, Tuple
from abc import abstractmethod
import pandas as pd
import plotly.graph_objects as go

import tinvest as ti

client = ti.SyncClient(os.getenv("TINVEST_TOKEN", ''))
interval = ti.CandleResolution.day
ma_period = [5, 60]
eps = 0.05


class Strategy(object):

    @abstractmethod
    def get_buy_points(figi: str, period):
        pass

    def get_sell_points(figi: str, period):
        pass


class ma_strategy(Strategy):

    def get_buy_points(figi: str, period) -> List:
        df = get_figi_data(figi, period)
        data = [df["c"].rolling(window=ma_period[0]).mean(), df["c"].rolling(window=ma_period[1]).mean(), df["time"]]
        result = []
        for i in range(len(data[0])):
            if -eps < ((data[0][i] - data[1][i]) / data[1][i]) < eps:
                if data[0][i - 1] < data[0][i]:
                    result.append(datetime.date(data[2][i]))
        return result

    def get_sell_points(figi: str, period: int) -> List:
        df = get_figi_data(figi, period)
        data = [df["c"].rolling(window=ma_period[0]).mean(), df["c"].rolling(window=ma_period[1]).mean(), df["time"]]
        result = []
        for i in range(len(data[0])):
            if -eps < ((data[1][i] - data[0][i]) / data[1][i]) < eps:
                if data[0][i - 1] > data[0][i]:
                    result.append(datetime.date(data[2][i]))
        return result


class cross_strategy(Strategy):

    def get_buy_points(figi: str, period) -> List:
        df = get_figi_data(figi, period)
        data = [df["c"].rolling(window=ma_period[0]).mean(), df["c"].rolling(window=ma_period[1]).mean(), df["time"]]
        result = []
        for i in range(len(data[0])):
            if ((data[0][i] - data[1][i]) > 0 and (data[0][i - 1] - data[1][i - 1]) < 0):
                result.append(datetime.date(data[2][i]))
        return result

    def get_sell_points(figi: str, period: int) -> List:
        df = get_figi_data(figi, period)
        data = [df["c"].rolling(window=ma_period[0]).mean(), df["c"].rolling(window=ma_period[1]).mean(), df["time"]]
        result = []
        for i in range(len(data[0])):
            if ((data[0][i] - data[1][i]) < 0 and (data[0][i - 1] - data[1][i - 1]) > 0):
                result.append(datetime.date(data[2][i]))
        return result


class Tester(object):
    @abstractmethod
    def test(strategy: Strategy) -> int:
        pass

class Simple_Tester(Tester):
    tickers = ['AAPL', 'BABA', 'TSLA','MOMO', 'SBER' ]
    period = 3000
    def get_sequence(sell_points: List, buy_points: List)->List:
        sequence = []
        s, b = 0, 0
        sequence.append(buy_points[b])
        flag = 1
        while (s <= len(sell_points) - 1) and (b <= len(buy_points) - 1):
            if flag:
                if sell_points[s] > sequence[len(sequence) - 1]:
                    flag = 0
                    sequence.append(sell_points[s])
                s += 1
            else:
                if buy_points[b] > sequence[len(sequence) - 1]:
                    flag = 1
                    sequence.append(buy_points[b])
                b += 1
        return sequence

    def test(strategy: Strategy) -> int:
        period = Simple_Tester.period
        result = 0
        tickers = Simple_Tester.tickers
        for ticker in tickers:
            figi = get_figi_by_ticker(ticker)
            sell_price, buy_price = 0, 0
            df = get_figi_data(figi,period)
            sell_points, buy_points = strategy.get_sell_points(figi, period), strategy.get_buy_points(figi, period)
            if (len(buy_points) == 0) or (len(sell_points) == 0):
                return 0
            sequence = Simple_Tester.get_sequence(sell_points,buy_points)
            prices = [[datetime.date(val[6]), (val[0] + val[5]) / 2] for val in df.values]
            est = 1
            i = 0
            print(sequence)
            while i < (len(sequence) / 2):
                buy_date = sequence[i]
                sell_date = sequence[i + 1]
                for price in prices:
                    if price[0] == buy_date:
                        buy_price = price[1]
                    if price[0] == sell_date:
                        sell_price = price[1]
                print(buy_price, sell_price)
                est = est * (1 + (sell_price - buy_price) / buy_price)
                i += 1
            print('Количество сделок = ', i)
            result+=est
        result = result/len(tickers)
        return result

def main() -> None:
    period = 500
    ticker = "BABA"
    figi = get_figi_by_ticker(ticker)
    print(Simple_Tester.test( cross_strategy))
    # get_graph_by_ticker(ticker, period)
    print(cross_strategy.get_buy_points(figi, period))
    print(cross_strategy.get_sell_points(figi, period))


def get_figure(figis: List[Tuple[str, str]], period: int) -> go.Figure:
    return go.Figure(
        data=[get_candlesstick(get_figi_data(figi, period), figi, name) for figi, name in figis]
    )


def get_figi_by_ticker(ticker: str):
    return client.get_market_search_by_ticker(ticker).payload.instruments[0].figi


def get_graph_by_ticker(ticker: str, period: int):
    get = client.get_market_search_by_ticker(ticker)
    get = [(get.payload.instruments[0].figi, get.payload.instruments[0].name)]
    fig = get_figure(get, period)
    ma = get_figi_data(get[0], period)
    for per in ma_period:
        # fig.add_scatter(name="EMoving average " + str(per), y=ma["c"].ewm(span=per, adjust=False).mean(), x=ma["time"])
        fig.add_scatter(name="Moving average " + str(per), y=ma["c"].rolling(window=per).mean(), x=ma["time"])
    fig.show()


def get_candlesstick(df: pd.DataFrame, figi: str, name: str) -> go.Candlestick:
    return go.Candlestick(
        name=f'{name} {figi}',
        x=df['time'],
        open=df['o'],
        high=df['h'],
        low=df['l'],
        close=df['c'],
    )


def get_figi_data(figi: str, period: int) -> pd.DataFrame:
    local_period = period
    payload = client.get_market_candles(
        figi=figi,
        from_=datetime.now() - timedelta(days=local_period),
        to=datetime.now() - timedelta(days=local_period) + timedelta(days=365),
        interval=interval,
    ).payload
    while local_period > 365:
        local_period -= 365
        new = client.get_market_candles(
            figi=figi,
            from_=datetime.now() - timedelta(days=local_period),
            to=datetime.now() - timedelta(days=local_period) + timedelta(days=365),
            interval=interval,
        ).payload
        for candle in new.candles:
            payload.candles.append(candle)
    return pd.DataFrame(c.dict() for c in payload.candles)





if __name__ == '__main__':
    main()
