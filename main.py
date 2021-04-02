import myTester
import myLearner
import myStrategy


def main() -> None:
    tickers = ['AAPL', 'BABA', 'TSLA', 'MOMO', 'SBER']
    period = 365 * 2
    print(1.06 ** (period / 365),1.14 ** (period / 365))
    tester = myTester.SimpleTester
    tester.tickers, tester.period = tickers, period
    tester.get_data(tester)
    strategy = myStrategy.CrossBuyTrailStop
    learner = myLearner.CrossStrategyLearner(tester=tester, strategy=strategy, step=3, limit=250)
    learner.learn()


main()
