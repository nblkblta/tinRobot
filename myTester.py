from typing import List
from abc import abstractmethod
from datetime import datetime
import pandas as pd
import myStrategy
import ma_for_ticker


class Tester(object):
    @abstractmethod
    def test(self, strategy: myStrategy.Strategy) -> int:
        pass


class SimpleTester(Tester):
    tickers: List[str]
    period: int
    data: List

    def get_data(self):
        self.data = []
        for ticker in self.tickers:
            self.data.append(
                [ticker, ma_for_ticker.get_figi_data(ma_for_ticker.get_figi_by_ticker(ticker), self.period)])

    def get_df_from_data(self, ticker: str) -> pd.DataFrame:
        for data in self.data:
            if ticker == data[0]:
                return data[1]

    def test(self, strategy: myStrategy.Strategy) -> float:
        result = 0
        tickers = self.tickers
        for ticker in tickers:
            sell_price, buy_price = 0, 0
            df = self.get_df_from_data(self, ticker)
            sequence = strategy.get_sequence(strategy, df)
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
            result += est
        result = result / len(tickers)
        return result
