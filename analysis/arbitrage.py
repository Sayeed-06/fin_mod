"""
Arbitrage detection module - identify pricing violations and opportunities.

Functions:
    - check_price_bounds: Verify intrinsic/time value bounds
    - check_volatility_consistency: Compare IV to historical volatility
    - early_exercise_value: Check for early exercise violation
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def check_price_bounds(option_data, spot_price, risk_free_rate):
    """
    Check if option prices respect basic arbitrage-free bounds.

    Bounds:
        Call: max(0, S - K*exp(-rT)) <= C <= S
        Put: max(0, K*exp(-rT) - S) <= P <= K*exp(-rT)

    Parameters:
        option_data (pd.DataFrame): Option data with strike, mid, option_type, T
        spot_price (float): Spot price
        risk_free_rate (float): Risk-free rate

    Returns:
        pd.DataFrame: Violations found (empty if all valid)
        Columns: strike, option_type, mid, lower_bound, upper_bound, violation_type
    """
    data = option_data.copy()
    violations = []

    calls = data[data['option_type'] == 'call']
    for idx, row in calls.iterrows():
        discount = np.exp(-risk_free_rate * float(row['T']))
        lower = max(0.0, float(spot_price - row['strike'] * discount))
        upper = float(spot_price)

        if float(row['mid']) < lower - 0.01:  # Allow $0.01 tolerance
            violations.append({
                'strike': float(row['strike']),
                'option_type': 'call',
                'mid': float(row['mid']),
                'lower_bound': lower,
                'upper_bound': upper,
                'violation_type': 'Below Lower Bound',
            })
        elif float(row['mid']) > upper + 0.01:
            violations.append({
                'strike': float(row['strike']),
                'option_type': 'call',
                'mid': float(row['mid']),
                'lower_bound': lower,
                'upper_bound': upper,
                'violation_type': 'Above Upper Bound',
            })

    puts = data[data['option_type'] == 'put']
    for idx, row in puts.iterrows():
        discount = np.exp(-risk_free_rate * float(row['T']))
        lower = max(0.0, float(row['strike'] * discount - spot_price))
        upper = float(row['strike'] * discount)

        if float(row['mid']) < lower - 0.01:
            violations.append({
                'strike': float(row['strike']),
                'option_type': 'put',
                'mid': float(row['mid']),
                'lower_bound': lower,
                'upper_bound': upper,
                'violation_type': 'Below Lower Bound',
            })
        elif float(row['mid']) > upper + 0.01:
            violations.append({
                'strike': float(row['strike']),
                'option_type': 'put',
                'mid': float(row['mid']),
                'lower_bound': lower,
                'upper_bound': upper,
                'violation_type': 'Above Upper Bound',
            })

    logger.info(f"Found {len(violations)} price bound violations")
    return pd.DataFrame(violations)


def check_volatility_consistency(option_data, historical_vol):
    """
    Compare market IV to historical volatility.

    Anomalies:
        - Market IV >> historical vol: IV priced in future shock
        - Market IV << historical vol: Options may be cheap

    Parameters:
        option_data (pd.DataFrame): Option data with impliedvolatility
        historical_vol (float): Historical volatility (annualized)

    Returns:
        dict: Summary statistics
            - avg_iv: Average market IV
            - hist_vol: Historical volatility
            - iv_vs_hv_ratio: IV / HV
            - high_iv_count: # of options with IV > 1.5 * HV
            - low_iv_count: # of options with IV < 0.75 * HV
    """
    if historical_vol is None or historical_vol < 0.001:
        return {
            'avg_iv': option_data['impliedvolatility'].mean(),
            'hist_vol': None,
            'iv_vs_hv_ratio': None,
            'high_iv_count': None,
            'low_iv_count': None,
        }

    iv_data = option_data['impliedvolatility'].dropna()
    avg_iv = iv_data.mean()

    high_iv = (iv_data > 1.5 * historical_vol).sum()
    low_iv = (iv_data < 0.75 * historical_vol).sum()

    return {
        'avg_iv': avg_iv,
        'hist_vol': historical_vol,
        'iv_vs_hv_ratio': avg_iv / historical_vol if historical_vol > 0 else None,
        'high_iv_count': high_iv,
        'low_iv_count': low_iv,
    }


def detect_arbitrage_opportunities(option_data, spot_price, risk_free_rate, threshold_percent=0.5):
    """
    Detect potential arbitrage opportunities based on mispricing.

    Strategy:
        - If overpriced: Sell (short) the option, hedge with spot
        - If underpriced: Buy the option, hedge with spot

    Parameters:
        option_data (pd.DataFrame): Data with pricing_error, theoretical_price
        spot_price (float): Current spot
        risk_free_rate (float): Risk-free rate
        threshold_percent (float): Minimum mispricing % to flag

    Returns:
        pd.DataFrame: Arbitrage opportunities
        Columns: strike, option_type, theoretical, market, error, error_pct, action
    """
    data = option_data.copy()

    if 'pricing_error' not in data.columns or 'mispricing_pct' not in data.columns:
        return pd.DataFrame()

    # Filter by threshold
    arb_data = data[np.abs(data['mispricing_pct']) > threshold_percent].copy()

    arb_data['action'] = arb_data['pricing_error'].apply(
        lambda x: 'SELL (overpriced)' if x > 0 else 'BUY (underpriced)'
    )

    arb_data = arb_data[[
        'strike', 'option_type', 'theoretical_price', 'mid', 'pricing_error', 'mispricing_pct', 'action'
    ]].copy()

    arb_data.rename(columns={
        'theoretical_price': 'theoretical',
        'mid': 'market',
        'pricing_error': 'error',
        'mispricing_pct': 'error_pct',
    }, inplace=True)

    logger.info(f"Detected {len(arb_data)} arbitrage opportunities")
    return arb_data
