import myTester
import myLearner
import myStrategy


def main() -> None:
    tickers = ['AAPL', 'BABA', 'TSLA', 'MOMO', 'SBER', 'KHC', 'SNGS', 'SPCE', 'JD', 'NVDA', 'KO']
    period = 365 * 2
    print(1.06 ** (period / 365), 1.14 ** (period / 365))
    tester = myTester.SimpleTester(tickers, period)
    tester.get_data()
    strategy = myStrategy.CrossBuyTrailStop
    learner = myLearner.CrossStrategyLearner(tester=tester, strategy=strategy, step=5, limit=250)
    estimations = learner.learn()
    print(estimations)


main()
