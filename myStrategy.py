from decimal import Decimal
from typing import List
from abc import abstractmethod
from datetime import datetime, timedelta
import pandas as pd


class Strategy(object):

    @abstractmethod
    def get_buy_points(self: str, df: pd.DataFrame) -> List:
        pass

    @abstractmethod
    def get_sell_points(self: str, df: pd.DataFrame) -> List:
        pass

    def get_sequence(self, df: pd.DataFrame) -> List:
        sell_points, buy_points = self.get_sell_points(self, df), self.get_buy_points(self, df)
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


class MovingAverageStrategy(Strategy):
    ma_period: List
    eps = 0.05

    def get_buy_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(),
                df["time"]]
        result = []
        for i in range(len(data[0])):
            if -self.eps < ((data[0][i] - data[1][i]) / data[1][i]) < self.eps:
                if data[0][i - 1] < data[0][i]:
                    result.append(datetime.date(data[2][i]))
        return result

    def get_sell_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(),
                df["time"]]
        result = []
        for i in range(len(data[0])):
            if -self.eps < ((data[1][i] - data[0][i]) / data[1][i]) < self.eps:
                if data[0][i - 1] > data[0][i]:
                    result.append(datetime.date(data[2][i]))
        return result


class CrossStrategy(Strategy):
    ma_periods: List

    def get_buy_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(),
                df["time"]]
        result = []
        for i in range(len(data[0])):
            if (data[0][i] - data[1][i]) > 0 > (data[0][i - 1] - data[1][i - 1]):
                result.append(datetime.date(data[2][i]))
        return result

    def get_sell_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(),
                df["time"]]
        result = []
        for i in range(len(data[0])):
            if (data[0][i] - data[1][i]) < 0 < (data[0][i - 1] - data[1][i - 1]):
                result.append(datetime.date(data[2][i]))
        return result


class CrossBuyTrailStop(Strategy):
    ma_periods: List
    eps = 0.10

    def get_buy_points(self, df: pd.DataFrame) -> List:
        data = [df["c"].rolling(window=self.ma_periods[0]).mean(), df["c"].rolling(window=self.ma_periods[1]).mean(),
                df["time"]]
        result = []
        for i in range(len(data[0])):
            if (data[0][i] - data[1][i]) > 0 > (data[0][i - 1] - data[1][i - 1]):
                result.append(datetime.date(data[2][i]))
        return result

    def get_sell_points(self, df: pd.DataFrame) -> List:
        buy_points = self.get_buy_points(self, df)
        result = []
        data = [[datetime.date(val[6]), val[2], val[4]] for val in df.values]
        i, j = 0, 0
        while i < len(data) and j < len(buy_points):
            if buy_points[j] == data[i][0]:
                high = float(data[i][1])
                while i < len(data) and high * (1 - self.eps) < data[i][2]:
                    if data[i][1] > high:
                        high = float(data[i][1])
                    i += 1
                if i < len(data):
                    result.append(data[i][0])
                j += 1
            i += 1
        return result
