"""Contains useful functions for generating a yfinance dataset."""
from __future__ import annotations

import yfinance

from finance.utils import requests_

NAME = "yfinance"

__session = requests_.create_requests_session_from_cache_name(cache_name=NAME)


def get_ticker_obj(ticker: str) -> yfinance.Ticker:
    """Gets a yfinance ticker object.

    Args:
        ticker (str): The stock ticker to retrieve.

    Returns:
        yfinance.Ticker: The yfinance ticker object.
    """

    ticker = yfinance.Ticker(ticker, session=__session)

    return ticker


def get_maximum_daily_ohlc_history_from_ticker(ticker: str) -> pd.DataFrame:
    """Gets the maximum available history for a given ticker.

    The use of the session object enables caching.

    Args:
        ticker (str): The stock ticker to retrieve.

    Returns:
        pd.DataFrame: A Dataframe containing the OHLC (Open, High, Low, Close) data for a given stock.

        Example:
                    Open	    High	    Low	        Close	    Volume	Dividends	Stock Splits
        Date
        1962-01-02	0.000000	1.546186	1.537367	1.537367	55930	0.0	        0.0
        1962-01-03	1.537368	1.560884	1.534428	1.560884	74906	0.0	        0.0
        1962-01-04	1.560884	1.572642	1.560884	1.560884	80899	0.0	        0.0
        1962-01-05	1.560884	1.569702	1.555005	1.557944	70911	0.0	        0.0
        1962-01-08	1.552065	1.552065	1.493274	1.505032	93883	0.0	        0.0
    """

    ticker_obj = get_ticker_obj(ticker=ticker)
    ohlc_history = ticker_obj.history(period="max")

    return ohlc_history
