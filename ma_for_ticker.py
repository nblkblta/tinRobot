import os
from datetime import datetime, timedelta
from typing import List, Tuple
from abc import abstractmethod
import pandas as pd
import plotly.graph_objects as go

import tinvest as ti

client = ti.SyncClient(os.getenv("TINVEST_TOKEN", ''))
interval = ti.CandleResolution.day
ma_period = [5, 50]


class Strategy(object):

    @abstractmethod
    def get_buy_points(self: str, df: pd.DataFrame) -> List:
        pass

    @abstractmethod
    def get_sell_points(self: str, df: pd.DataFrame) -> List:
        pass


class MovingAverageStrategy(Strategy):
    ma_period:List
    ma_periods = ma_period
    eps = 0.05

    def get_buy_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(), df["time"]]
        result = []
        for i in range(len(data[0])):
            if -self.eps < ((data[0][i] - data[1][i]) / data[1][i]) < self.eps:
                if data[0][i - 1] < data[0][i]:
                    result.append(datetime.date(data[2][i]))
        return result

    def get_sell_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(), df["time"]]
        result = []
        for i in range(len(data[0])):
            if -self.eps < ((data[1][i] - data[0][i]) / data[1][i]) < self.eps:
                if data[0][i - 1] > data[0][i]:
                    result.append(datetime.date(data[2][i]))
        return result


class CrossStrategy(Strategy):

    ma_periods = ma_period

    def get_buy_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(), df["time"]]
        result = []
        for i in range(len(data[0])):
            if (data[0][i] - data[1][i]) > 0 > (data[0][i - 1] - data[1][i - 1]):
                result.append(datetime.date(data[2][i]))
        return result

    def get_sell_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(), df["time"]]
        result = []
        for i in range(len(data[0])):
            if (data[0][i] - data[1][i]) < 0 < (data[0][i - 1] - data[1][i - 1]):
                result.append(datetime.date(data[2][i]))
        return result


class Tester(object):
    @abstractmethod
    def test(strategy: Strategy) -> int:
        pass


class SimpleTester(Tester):
    tickers: List[str]
    period: int
    data: List

    def get_data(self):
        self.data = []
        for ticker in self.tickers:
            self.data.append([ticker,get_figi_data(get_figi_by_ticker(ticker), self.period)])

    def get_sequence(self, sell_points: List, buy_points: List) -> List:
        sequence = []
        if (len(buy_points) == 0) or (len(sell_points) == 0):
            return sequence
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
        if flag:
            sequence.pop()
        return sequence

    def get_df_from_data(self, ticker: str)-> pd.DataFrame:
        for data in self.data:
            if ticker==data[0]:
                return data[1]


    def test(self, strategy: Strategy) -> float:
        period = self.period
        result = 0
        inf = 1.06 ** (period / 365)
        sp500 = 1.12 ** (period / 365)
        tickers = self.tickers
        for ticker in tickers:
            sell_price, buy_price = 0, 0
            df = self.get_df_from_data(self,ticker)
            sell_points, buy_points = strategy.get_sell_points(strategy,df), strategy.get_buy_points(strategy,df)
            sequence = self.get_sequence(self, sell_points, buy_points)
            prices = [[datetime.date(val[6]), (val[0] + val[5]) / 2] for val in df.values]
            est = 1
            i = 0
            while i < (len(sequence) / 2):
                buy_date = sequence[i]
                sell_date = sequence[i + 1]
                for price in prices:
                    if price[0] == buy_date:
                        buy_price = price[1]
                    if price[0] == sell_date:
                        sell_price = price[1]
                est = est * (1 + (sell_price - buy_price) / buy_price)
                i += 1
            # print('Ticker = ', ticker, ' Количество сделок = ', i, ' Оценка = ', est)
            result += est
        result = result / len(tickers)
        print('Средняя оценок = ', result)
        # print('Ожидаемая инфляция = ', inf)
        # print('Ожидаемый рост биржи = ', sp500)
        return result


class Learner(object):

    @abstractmethod
    def learn(self: str):
        pass


class CrossStrategyLearner(Learner):

    tester: Tester

    def learn(self)->List:
        estimations =[]
        best_ma = [1,2]
        best_est = 1
        i = 1
        while i < 300:
            j = i+5
            while j < 300:
                strategy = CrossStrategy
                strategy.ma_periods = [i,j]
                res = self.tester.test(self.tester, strategy)
                if res > best_est:
                    best_ma = [i, j]
                    best_est = res
                estimations.append([strategy.ma_periods, res])
                j += 5
            i += 5
        print(best_ma)
        return estimations


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
        # fig.add_scatter(name="EMoving average " + str(per), y=ma["c"].ewm(span=per, adjust=False).mean(),
        # x=ma["time"])
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


def main() -> None:
    tickers = ['AAPL', 'BABA', 'TSLA', 'MOMO', 'SBER']
    period = 2000
    tester = SimpleTester
    tester.tickers,tester.period = tickers, period
    tester.get_data(tester)
    learner = CrossStrategyLearner
    CrossStrategyLearner.tester = tester
    print(learner.learn(self=learner))


main()
