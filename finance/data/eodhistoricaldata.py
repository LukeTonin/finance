"""Contains useful functions to download ticker and exchange data from eobhistoricaldata.com
"""
from __future__ import annotations
import urllib

import pandas as pd

from finance.config import config
from finance.utils import requests_

NAME = __name__.split(".")[-1]
BASE_URL = f"https://{NAME}.com"

__session = requests_.create_requests_session_from_cache_name(cache_name=NAME)

# The following dictionary is used to filter the tickers after downloading them from EOBHistorical data.
# The EOBHistoricaldata api has a quirk that only allows to download all US tickers at the same time.
# They then need to be filtered based on the name of the associated exchange.
MIC_CODE_TO_EXCHANGE_NAME = {"XNYS": "NYSE", "XNAS": "NASDAQ"}


def get_exchange_mic_to_code(
    exchange_mics: Union[List[str], Set[str]], exchanges_df: pd.DataFrame = None
) -> Dict[str, Set[str]]:
    """Returns a dictionary that maps exchange codes (used by eodhistoricaldata.com) and the corresponding exchange MICS

    Args:
        exchange_mics (Union[List[str], Set[str]]): The MICs of the exchanges.
        exchanges_df (pd.DataFrame): The exchanges dataframe provided by the eobhistoricaldata.com.

    Returns:
        Dict[str, Set[str]]: A mapping between MIC code and exchange codes.
    """

    exchange_mics = set(exchange_mics)

    if exchanges_df is None:
        exchanges_df = get_exchanges()

    exchanges_df["OperatingMIC"] = exchanges_df["OperatingMIC"].apply(lambda x: set(x.split(", ")) if x else set())
    exchanges_df = exchanges_df.explode(column="OperatingMIC")
    exchanges_df_filtered = exchanges_df[exchanges_df["OperatingMIC"].isin(exchange_mics)]

    exchange_mics_to_code = dict(zip(exchanges_df_filtered["OperatingMIC"], exchanges_df_filtered["Code"]))

    return exchange_mics_to_code


def get_exchanges() -> pd.DataFrame:
    """Gets all the names and codes of the exchanges provided by eobhistoricaldata.

    In total about 70 exchanges are returned from all over the world (LSE, NYSE, DAX etc...).

    Returns:
        pd.DataFrame: The list of exchanges (the US exchanges are grouped under the "US" code.)

        Example:
                Name	                Code	    OperatingMIC	Country	Currency
            0	USA Stocks	            US	        XNAS, XNYS	    USA	    USD
            1	London Exchange	        LSE	        XLON	        UK	    GBP
            2	Toronto Exchange	    TO	        XTSE	        Canada	CAD
    """

    credentials = config.get_credentials()

    url = urllib.parse.urljoin(base=BASE_URL, url="api/exchanges-list")
    params = {"api_token": credentials[NAME]["api_key"], "fmt": "json"}

    output = __session.get(url=url, params=params)

    exchanges = pd.DataFrame(output.json())

    return exchanges


def get_tickers(exchange_code: str) -> pd.DataFrame:
    """Get the ticker symbols from a given echange.

    The possible exchanges are provided by the "Code" column of the dataframe returned
    by get_exchanges
    """
    credentials = config.get_credentials()

    url = urllib.parse.urljoin(base=BASE_URL, url=f"api/exchange-symbol-list/{exchange_code}")
    params = {"api_token": credentials[NAME]["api_key"], "fmt": "json"}

    output = __session.get(url=url, params=params)

    tickers_df = pd.DataFrame(output.json())

    return tickers_df


def get_tickers_from_exchange_mics(
    exchange_mics: Union[List[str], Set[str]],
    exchanges_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """Get all the tickers from the provided exchanges.

    Args:
        exchange_mics (Union[List[str], Set[str]]): The MIC codes of the exchanges.
        exchanges_df (pd.DataFrame, optional): A dataframe containing the exchange codes (result of get_exchanges).
            If not provided, it will be downloaded. Defaults to None.
        usa_exchange_filters (Set[str]): If provided, filter all tickers retrieved from 'US' code to only
            return those from the provided exchanges. This is necessary because eobhistoricaldata does not
            allow one to filter on

    Returns:
        pd.DataFrame: A DataFrame containing the tickers and their data.
    """

    exchange_mic_to_code = get_exchange_mic_to_code(exchange_mics=exchange_mics, exchanges_df=exchanges_df)

    tickers_dfs = []
    for exchange_mic, exchange_code in exchange_mic_to_code.items():

        tickers_df = get_tickers(exchange_code=exchange_code)

        if exchange_mic in MIC_CODE_TO_EXCHANGE_NAME:
            tickers_df = tickers_df.loc[tickers_df["Exchange"] == MIC_CODE_TO_EXCHANGE_NAME[exchange_mic]]

        if len(tickers_df) == 0:
            raise ValueError(
                "Could not find any tickers for exchange mic: {exchange_mic} and exchange code: {exchange_code}"
            )

        tickers_df["MIC"] = [exchange_mic for _ in range(len(tickers_df))]
        tickers_df["Eodhistoricaldata Code"] = [exchange_code for _ in range(len(tickers_df))]
        tickers_dfs.append(tickers_df)

    tickers_df = pd.concat(tickers_dfs, axis=0)

    return tickers_df
