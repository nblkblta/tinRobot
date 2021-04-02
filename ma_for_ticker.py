import os
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd
import plotly.graph_objects as go
import tinvest as ti

client = ti.SyncClient(os.getenv("TINVEST_TOKEN", ''))
interval = ti.CandleResolution.day
ma_period = [5, 50]


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
        fig.add_scatter(name="EMoving average " + str(per), y=ma["c"].ewm(span=per, adjust=False).mean(),
        x=ma["time"])
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





