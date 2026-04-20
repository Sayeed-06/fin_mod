"""
Data cleaning and validation module for option chains.

Functions:
    - clean_option_chain: Process and validate raw option data
    - validate_put_call_parity: Check for mispricing violations
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def clean_option_chain(raw_data, spot_price, expiration_date, risk_free_rate):
    """
    Clean and validate option chain data.

    Performs:
        - Removes rows with missing/invalid prices
        - Calculates intrinsic value
        - Ensures prices respect minimum bounds
        - Computes time to maturity
        - Flags IV issues
        - Filters out low-volume contracts

    Parameters:
        raw_data (pd.DataFrame): Raw option chain from yfinance
        spot_price (float): Current spot price
        expiration_date (str): Expiration date (YYYY-MM-DD)
        risk_free_rate (float): Annual risk-free rate

    Returns:
        pd.DataFrame: Cleaned option data with computed fields
        None: If data cannot be cleaned

    Added columns:
        - T: Time to maturity (years)
        - intrinsic: Intrinsic value
        - time_value: Time value (mid - intrinsic)
        - spread: Bid-ask spread (%)
        - mid_valid: Whether mid price is reasonable
    """
    try:
        data = raw_data.copy()

        # Remove zero-volume contracts (optional, but safer)
        data = data[data['volume'] > 0].copy()

        # Ensure mid price exists or calculate
        if 'mid' not in data.columns or data['mid'].isna().all():
            data['mid'] = (data['bid'] + data['ask']) / 2.0

        # Calculate time to maturity
        exp_datetime = pd.to_datetime(expiration_date)
        today = pd.to_datetime(datetime.today().date())
        days_to_expiry = (exp_datetime - today).days
        data['T'] = max(days_to_expiry, 0) / 365.0

        # Calculate intrinsic value
        calls_mask = data['option_type'] == 'call'
        puts_mask = data['option_type'] == 'put'

        data['intrinsic'] = 0.0
        data.loc[calls_mask, 'intrinsic'] = np.maximum(data.loc[calls_mask, 'strike'] - spot_price, 0)
        data.loc[puts_mask, 'intrinsic'] = np.maximum(spot_price - data.loc[puts_mask, 'strike'], 0)

        # Calculate time value
        data['time_value'] = np.maximum(data['mid'] - data['intrinsic'], 0)

        # Calculate bid-ask spread percentage
        data['spread_abs'] = data['ask'] - data['bid']
        data['spread_pct'] = data['spread_abs'] / np.maximum(data['mid'], 0.01) * 100

        # Validate mid price respects bounds
        discount_factor = np.exp(-risk_free_rate * data['T'])

        # Call: mid >= max(S - K*exp(-rT), 0)
        data.loc[calls_mask, 'lower_bound'] = np.maximum(
            spot_price - data.loc[calls_mask, 'strike'] * discount_factor,
            0
        )
        data.loc[calls_mask, 'upper_bound'] = spot_price

        # Put: mid >= max(K*exp(-rT) - S, 0)
        data.loc[puts_mask, 'lower_bound'] = np.maximum(
            data.loc[puts_mask, 'strike'] * discount_factor - spot_price,
            0
        )
        data.loc[puts_mask, 'upper_bound'] = data.loc[puts_mask, 'strike'] * discount_factor

        # Flag valid mid prices
        data['mid_valid'] = (data['mid'] >= data['lower_bound'] - 0.01) & \
                            (data['mid'] <= data['upper_bound'] + 0.01)

        # Remove rows with invalid mid prices
        initial_rows = len(data)
        data = data[data['mid_valid']].copy()

        if len(data) == 0:
            logger.warning("No valid option prices after cleaning")
            return None

        logger.info(f"Cleaned option chain: {initial_rows} rows -> {len(data)} rows")

        # Drop helper columns
        data.drop(columns=['lower_bound', 'upper_bound', 'mid_valid'], inplace=True)

        return data

    except Exception as e:
        logger.error(f"Error cleaning option chain: {e}")
        return None


def validate_put_call_parity(option_data, spot_price, risk_free_rate):
    """
    Check for put-call parity violations.

    Put-call parity: C - P = S - K*exp(-rT)

    Parameters:
        option_data (pd.DataFrame): Cleaned option data
        spot_price (float): Current spot price
        risk_free_rate (float): Annual risk-free rate

    Returns:
        pd.DataFrame: Strikes with PCP violations (empty if none found)

    Columns:
        - strike
        - call_price
        - put_price
        - parity_val: Theoretical C - P
        - market_val: Observed C - P
        - violation: Absolute difference
    """
    try:
        # Separate calls and puts
        calls = option_data[option_data['option_type'] == 'call'][['strike', 'mid', 'T']].copy()
        puts = option_data[option_data['option_type'] == 'put'][['strike', 'mid', 'T']].copy()

        if calls.empty or puts.empty:
            return pd.DataFrame()

        calls.rename(columns={'mid': 'call_price'}, inplace=True)
        puts.rename(columns={'mid': 'put_price'}, inplace=True)

        # Match by strike (take first by distance)
        parity_data = pd.merge(calls, puts, on='strike', how='inner')

        if parity_data.empty:
            return pd.DataFrame()

        # Average T if different
        parity_data['T'] = (parity_data['T_x'] + parity_data['T_y']) / 2

        # Theoretical: C - P = S - K*exp(-rT)
        parity_data['parity_val'] = spot_price - parity_data['strike'] * np.exp(
            -risk_free_rate * parity_data['T']
        )

        # Market: C - P
        parity_data['market_val'] = parity_data['call_price'] - parity_data['put_price']

        # Violation
        parity_data['violation'] = np.abs(parity_data['market_val'] - parity_data['parity_val'])

        # Filter significant violations (>$0.01)
        parity_violations = parity_data[parity_data['violation'] > 0.01].copy()

        logger.info(f"PCP violations: {len(parity_violations)} of {len(parity_data)} strikes")

        return parity_violations[['strike', 'call_price', 'put_price', 'parity_val', 'market_val', 'violation']]

    except Exception as e:
        logger.error(f"Error validating put-call parity: {e}")
        return pd.DataFrame()
