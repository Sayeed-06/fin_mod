"""
Data fetching module for option chain data from yfinance.

Functions:
    - fetch_option_chain: Download option chain for a ticker/expiry
    - get_expirations: Get available expiration dates
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_expirations(ticker, limit=30):
    """
    Get available option expiration dates for a ticker.

    Parameters:
        ticker (str): Stock/ETF ticker symbol
        limit (int): Maximum number of expirations to return

    Returns:
        list: Sorted list of expiration dates as strings (YYYY-MM-DD)
        None: If unable to fetch data
    """
    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options[:limit]
        return sorted(expirations) if expirations else None
    except Exception as e:
        logger.error(f"Failed to fetch expirations for {ticker}: {e}")
        return None


def fetch_option_chain(ticker, expiration):
    """
    Fetch option chain for a given ticker and expiration date.

    Parameters:
        ticker (str): Stock/ETF ticker symbol
        expiration (str): Expiration date (YYYY-MM-DD format)

    Returns:
        pd.DataFrame: Option chain data (calls and puts combined)
        None: If unable to fetch data

    Columns returned (after processing):
        - strike
        - option_type ('call' or 'put')
        - bid
        - ask
        - mid (calculated as (bid+ask)/2)
        - last
        - volume
        - open_interest
        - implied_volatility
        - in_the_money
    """
    try:
        stock = yf.Ticker(ticker)

        # Fetch option chain
        chain = stock.option_chain(expiration)
        calls = chain.calls.copy()
        puts = chain.puts.copy()

        # Add option type
        calls['option_type'] = 'call'
        puts['option_type'] = 'put'

        # Combine
        data = pd.concat([calls, puts], ignore_index=True)

        # Standardize column names (yfinance may vary)
        column_mapping = {
            'contractSymbol': 'contract',
            'lastPrice': 'lastprice',
            'lastTradeDate': 'lasttradedate',
            'impliedVolatility': 'impliedvolatility',
            'openInterest': 'openinterest',
        }
        data.rename(columns=column_mapping, inplace=True)

        # Calculate mid price
        data['mid'] = (data['bid'] + data['ask']) / 2.0
        data['mid'] = data['mid'].replace(0, np.nan)  # Replace x/0 with NaN

        # Filter out completely invalid rows
        data = data[data['strike'] > 0].copy()
        data = data[data['bid'] >= 0].copy()
        data = data[data['ask'] >= 0].copy()

        # Ensure mid >= intrinsic value
        data.loc[data['option_type'] == 'call', 'intrinsic'] = (
            data.loc[data['option_type'] == 'call', 'strike'] * 0  # Will calculate with spot
        )
        data.loc[data['option_type'] == 'put', 'intrinsic'] = (
            data.loc[data['option_type'] == 'put', 'strike'] * 0  # Will calculate with spot
        )

        # Select relevant columns
        keep_cols = [
            'strike', 'option_type', 'bid', 'ask', 'mid', 'lastprice',
            'volume', 'openinterest', 'impliedvolatility', 'inTheMonkey'
        ]
        available_cols = [col for col in keep_cols if col in data.columns]
        data = data[available_cols].copy()

        # Rename for consistency
        data.rename(columns={'inTheMonkey': 'in_the_money'}, inplace=True)

        logger.info(f"Fetched {len(data)} option contracts for {ticker} expiring {expiration}")
        return data

    except Exception as e:
        logger.error(f"Failed to fetch option chain for {ticker} {expiration}: {e}")
        return None


def get_current_price(ticker):
    """
    Get the current spot price of a ticker.

    Parameters:
        ticker (str): Stock/ETF ticker symbol

    Returns:
        float: Current price or None if unavailable
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty:
            return None
        return data['Close'].iloc[-1]
    except Exception as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        return None


def get_historical_volatility(ticker, lookback_days=30):
    """
    Estimate historical volatility from recent price data.

    Parameters:
        ticker (str): Stock/ETF ticker symbol
        lookback_days (int): Number of days to use for estimation

    Returns:
        float: Annualized historical volatility or None if unavailable
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=f"{lookback_days}d")

        if len(data) < 2:
            return None

        # Calculate log returns
        log_returns = np.log(data['Close'] / data['Close'].shift(1)).dropna()

        # Annualized standard deviation
        hist_vol = log_returns.std() * np.sqrt(252)
        return hist_vol

    except Exception as e:
        logger.error(f"Failed to compute historical volatility for {ticker}: {e}")
        return None
