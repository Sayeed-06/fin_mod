"""
Strategy selector and payoff calculator.

Functions:
    - suggest_strategies: Recommend strategies based on market conditions
    - calculate_payoff: Compute strategy payoff at various spot prices
    - strategy_breakevens: Calculate breakeven points
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def suggest_strategies(option_data, spot_price, vol_consistency):
    """
    Suggest trading strategies based on current market conditions.

    Parameters:
        option_data (pd.DataFrame): Option chain data
        spot_price (float): Current spot price
        vol_consistency (dict): IV vs historical vol comparison

    Returns:
        list: List of strategy dicts, each with:
            - name: Strategy name
            - description: Brief description
            - rationale: Why to use this strategy
            - condition: Market condition this targets
    """
    strategies = []

    iv_ratio = vol_consistency.get('iv_vs_hv_ratio', 1.0)
    avg_iv = vol_consistency.get('avg_iv', 0.25)

    # Strategy 1: Straddle / Strangle
    if iv_ratio < 0.9 or avg_iv < 0.20:
        strategies.append({
            'name': 'Long Straddle',
            'symbol': 'STRADDLE',
            'description': 'Buy ATM call and put',
            'rationale': 'Low IV: Options are cheap. Benefits from large move in either direction.',
            'condition': 'Low volatility expected to increase',
            'risk_profile': 'Limited downside (premium paid), unlimited profit',
        })

    # Strategy 2: Iron Condor
    if iv_ratio > 1.3 or avg_iv > 0.30:
        strategies.append({
            'name': 'Iron Condor',
            'symbol': 'IRON_CONDOR',
            'description': 'Sell OTM call spread + sell OTM put spread',
            'rationale': 'High IV: Volatility is expensive. Profit if price stays near current level.',
            'condition': 'High volatility expected to revert',
            'risk_profile': 'Limited profit (premium collected), defined risk',
        })

    # Strategy 3: Call Spread
    calls = option_data[option_data['option_type'] == 'call']
    if len(calls) > 0 and avg_iv < 0.35:
        strategies.append({
            'name': 'Bull Call Spread',
            'symbol': 'BULL_CALL',
            'description': 'Buy ATM call, sell OTM call',
            'rationale': 'Bullish outlook with reduced cost. Lower margin requirement.',
            'condition': 'Modest bullish move expected',
            'risk_profile': 'Limited risk (call spread max loss), limited profit',
        })

    # Strategy 4: Put Spread
    puts = option_data[option_data['option_type'] == 'put']
    if len(puts) > 0 and avg_iv < 0.35:
        strategies.append({
            'name': 'Bear Put Spread',
            'symbol': 'BEAR_PUT',
            'description': 'Sell OTM put, buy further OTM put',
            'rationale': 'Bearish outlook with income. Collects premium while defining risk.',
            'condition': 'Modest bearish move expected',
            'risk_profile': 'Limited risk (put spread max loss), defined profit',
        })

    # Strategy 5: Calendar Spread
    if avg_iv > 0.20:
        strategies.append({
            'name': 'Calendar Spread',
            'symbol': 'CALENDAR',
            'description': 'Sell near-term, buy longer-term (same strike)',
            'rationale': 'Profit from theta decay if IV stays elevated. Theta works in your favor.',
            'condition': 'IV stable or increasing, theta decay',
            'risk_profile': 'Defined risk, theta positive',
        })

    logger.info(f"Suggested {len(strategies)} strategies")
    return strategies


def calculate_payoff(spot_price, positions, spot_range=None):
    """
    Calculate strategy payoff across spot price range.

    Parameters:
        spot_price (float): Current spot price
        positions (list): List of position dicts, each with:
            - type (str): 'call' or 'put'
            - strike (float): Strike price
            - price (float): Price paid/received
            - quantity (int): Number of contracts
            - direction (str): 'long' or 'short'
        spot_range (tuple): (min_spot, max_spot) for calculation

    Returns:
        pd.DataFrame: Spot price range with payoff columns
    """
    if spot_range is None:
        # Default: ±20% of spot
        spot_range = (spot_price * 0.8, spot_price * 1.2)

    spots = np.linspace(spot_range[0], spot_range[1], 100)
    payoffs = {
        'spot': spots,
        'payoff': np.zeros_like(spots),
    }

    for pos in positions:
        strike = pos['strike']
        price = pos['price']
        qty = pos.get('quantity', 1)
        direction = pos.get('direction', 'long')

        if pos['type'] == 'call':
            intrinsic = np.maximum(spots - strike, 0)
        else:  # put
            intrinsic = np.maximum(strike - spots, 0)

        # P&L calculation
        if direction == 'long':
            pnl = (intrinsic - price) * qty
        else:  # short
            pnl = (price - intrinsic) * qty

        payoffs['payoff'] += pnl

    return pd.DataFrame(payoffs)


def strategy_breakevens(positions):
    """
    Calculate breakeven points for a strategy.

    Parameters:
        positions (list): List of position dicts

    Returns:
        list: Breakeven spot prices
    """
    # Simplified: find zeros of payoff (would need numerical solver for accuracy)
    # This is a placeholder; full implementation would use root-finding
    breakevens = []

    total_cost = sum(
        pos['price'] * pos.get('quantity', 1) *
        (-1 if pos.get('direction', 'long') == 'long' else 1)
        for pos in positions
    )

    # For simple strategies, breakeven is at strike +/- cost
    if len(positions) == 2:
        strikes = [pos['strike'] for pos in positions]
        avg_strike = np.mean(strikes)
        breakevens = [avg_strike - total_cost / 100, avg_strike + total_cost / 100]

    return breakevens


def visualize_payoff(payoff_df):
    """
    Generate payoff diagram data.

    Parameters:
        payoff_df (pd.DataFrame): From calculate_payoff()

    Returns:
        tuple: (spots, payoffs) for plotting
    """
    return payoff_df['spot'].values, payoff_df['payoff'].values
