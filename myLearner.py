from abc import abstractmethod
from typing import List

import myStrategy
import myTester


class Learner(object):
    tester: myTester.Tester
    strategy: myStrategy.Strategy
    step: int
    limit: int

    @abstractmethod
    def learn(self: str)->List:
        pass

    def __init__(self, tester: myTester.Tester, strategy: myStrategy.Strategy, step: int, limit: int):
        self.tester = tester
        self.strategy = strategy
        self.step = step
        self.limit = limit


class CrossStrategyLearner(Learner):


    def learn(self) -> List:
        estimations = []
        best_est = 1
        i = 1
        while i < self.limit:
            j = i + self.step
            while j < self.limit:
                self.strategy.ma_periods = [i, j]
                est = self.tester.test(self.strategy)
                if est > best_est:
                    best_est = est
                    print([i, j], best_est)
                estimations.append([self.strategy.ma_periods, est])
                j += self.step
            i += self.step
        return estimations
