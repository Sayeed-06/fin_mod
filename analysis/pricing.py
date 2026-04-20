"""
Pricing analysis module - compute mispricing metrics.

Functions:
    - compute_mispricing: Calculate pricing error and statistics
    - mispricing_summary: Aggregate mispricing across strikes
"""

import pandas as pd
import numpy as np
from models.black_scholes import black_scholes, all_greeks
from models.iv_solver import implied_volatility
import logging

logger = logging.getLogger(__name__)


def compute_theoretical_prices(option_data, spot_price, risk_free_rate, market_iv=None):
    """
    Compute theoretical option prices using Black-Scholes.

    Parameters:
        option_data (pd.DataFrame): Cleaned option data with T column
        spot_price (float): Current spot price
        risk_free_rate (float): Annual risk-free rate
        market_iv (pd.Series): Market implied volatility by strike/type (optional)

    Returns:
        pd.DataFrame: Input data with added columns:
            - theoretical_price: BS price using market IV
            - theo_call_price, theo_put_price: Per-type prices
            - greeks_delta, greeks_gamma, greeks_vega, greeks_theta, greeks_rho
    """
    data = option_data.copy()

    # Ensure IV is available
    if 'impliedvolatility' not in data.columns:
        data['impliedvolatility'] = np.nan

    # Use provided IV or fallback to market IV
    if market_iv is not None:
        data['sigma'] = data.index.map(market_iv).fillna(data['impliedvolatility'])
    else:
        data['sigma'] = data['impliedvolatility']

    # Fill missing IV with reasonable default (e.g., 0.25)
    data['sigma'] = data['sigma'].fillna(0.25)
    data['sigma'] = np.maximum(data['sigma'], 0.001)  # Ensure positive

    # Compute theoretical prices
    data['theoretical_price'] = data.apply(
        lambda row: black_scholes(
            S=spot_price,
            K=row['strike'],
            T=row['T'],
            r=risk_free_rate,
            sigma=row['sigma'],
            option_type=row['option_type']
        ),
        axis=1
    )

    # Compute Greeks
    greeks_list = data.apply(
        lambda row: all_greeks(
            S=spot_price,
            K=row['strike'],
            T=row['T'],
            r=risk_free_rate,
            sigma=row['sigma'],
            option_type=row['option_type']
        ),
        axis=1
    )

    greeks_df = pd.DataFrame(greeks_list.tolist())
    for col in ['delta', 'gamma', 'vega', 'theta', 'rho']:
        data[f'greeks_{col}'] = greeks_df[col]

    logger.info(f"Computed theoretical prices for {len(data)} options")
    return data


def compute_mispricing(option_data):
    """
    Compute pricing error and mispricing metrics.

    Parameters:
        option_data (pd.DataFrame): Data with 'mid' and 'theoretical_price' columns

    Returns:
        pd.DataFrame: Input data with added columns:
            - pricing_error: market - theoretical ($ amount)
            - mispricing_pct: pricing error / theoretical (%)
            - mispricing_zscore: z-score of error
    """
    data = option_data.copy()

    # Pricing error (positive = overpriced)
    data['pricing_error'] = data['mid'] - data['theoretical_price']

    # Percentage mispricing
    data['mispricing_pct'] = (data['pricing_error'] / np.maximum(data['theoretical_price'], 0.001)) * 100

    # Z-score of mispricing
    error_std = data['pricing_error'].std()
    error_mean = data['pricing_error'].mean()

    if error_std > 0:
        data['mispricing_zscore'] = (data['pricing_error'] - error_mean) / error_std
    else:
        data['mispricing_zscore'] = 0.0

    logger.info(f"Computed mispricing metrics for {len(data)} options")
    return data


def mispricing_summary(option_data, zscore_threshold=2.0):
    """
    Generate summary statistics of mispricing.

    Parameters:
        option_data (pd.DataFrame): Data with mispricing metrics
        zscore_threshold (float): Z-score threshold for significance

    Returns:
        dict: Summary statistics including:
            - total_options: Number of options
            - overpriced_count: Options with positive error
            - underpriced_count: Options with negative error
            - significant_mispricings: Count with |zscore| > threshold
            - avg_error: Mean pricing error
            - avg_error_pct: Mean percentage error
            - max_error: Largest absolute error
    """
    return {
        'total_options': len(option_data),
        'overpriced_count': (option_data['pricing_error'] > 0.01).sum(),
        'underpriced_count': (option_data['pricing_error'] < -0.01).sum(),
        'significant_mispricings': (np.abs(option_data['mispricing_zscore']) > zscore_threshold).sum(),
        'avg_error': option_data['pricing_error'].mean(),
        'avg_error_pct': option_data['mispricing_pct'].mean(),
        'std_error': option_data['pricing_error'].std(),
        'max_error': option_data['pricing_error'].abs().max(),
        'overpriced_pct': (option_data['pricing_error'] > 0.01).sum() / len(option_data) * 100,
    }
