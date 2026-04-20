"""
Backtesting engine for simple option strategies.

Functions:
    - run_backtest: Run historical simulation
    - compute_metrics: Calculate Sharpe ratio, max drawdown, win rate
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def run_backtest(option_data, spot_prices, strategy_name='long_mispriced'):
    """
    Run historical backtest of a strategy.

    Strategy Logic:
        - long_mispriced: Buy underpriced options (pricing_error < -1%)
        - short_mispriced: Sell overpriced options (pricing_error > 1%)

    Parameters:
        option_data (pd.DataFrame): Option chain with mispricing metrics
        spot_prices (pd.Series): Historical spot prices (index: dates)
        strategy_name (str): 'long_mispriced' or 'short_mispriced'

    Returns:
        pd.DataFrame: Backtest results
        Columns: date, spot_price, pnl, cumul_pnl, daily_return
    """
    if len(spot_prices) < 2:
        logger.warning("Insufficient price data for backtest")
        return pd.DataFrame()

    try:
        # Identify candidates
        if strategy_name == 'long_mispriced':
            candidates = option_data[option_data['pricing_error'] < -0.01].copy()
        else:  # short_mispriced
            candidates = option_data[option_data['pricing_error'] > 0.01].copy()

        if candidates.empty:
            logger.warning(f"No candidates found for {strategy_name}")
            return pd.DataFrame()

        # Simple backtest: assume we enter at mid price and exit at theoretical
        # This is a simplified model; real backtest would track Greeks and decay

        entry_prices = candidates['mid'].values
        exit_prices = candidates['theoretical_price'].values

        if strategy_name == 'long_mispriced':
            pnl_per_contract = exit_prices - entry_prices
        else:
            pnl_per_contract = entry_prices - exit_prices

        # Simulate across time horizon
        total_pnl = pnl_per_contract.sum()
        daily_pnl = total_pnl / len(spot_prices)

        # Build results
        results = []
        cumul_pnl = 0
        for i, (date, spot) in enumerate(spot_prices.items()):
            cumul_pnl += daily_pnl
            daily_return = daily_pnl / np.abs(entry_prices.mean()) if entry_prices.mean() != 0 else 0

            results.append({
                'date': date,
                'spot_price': spot,
                'pnl': daily_pnl,
                'cumul_pnl': cumul_pnl,
                'daily_return': daily_return,
            })

        backtest_df = pd.DataFrame(results)
        logger.info(f"Backtest completed: {strategy_name}, total PnL: ${total_pnl:.2f}")
        return backtest_df

    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return pd.DataFrame()


def compute_backtest_metrics(backtest_results):
    """
    Compute performance metrics from backtest results.

    Parameters:
        backtest_results (pd.DataFrame): From run_backtest()

    Returns:
        dict: Performance metrics
            - total_return: Total return (%)
            - total_pnl: Total P&L ($)
            - annual_return: Annualized return (%)
            - win_rate: % of profitable days
            - max_drawdown: Largest peak-to-trough loss
            - sharpe_ratio: Sharpe ratio (252-day annualization)
            - sortino_ratio: Sortino ratio
            - avg_win: Average winning day
            - avg_loss: Average losing day
    """
    if backtest_results.empty:
        return {
            'total_return': 0,
            'total_pnl': 0,
            'annual_return': 0,
            'win_rate': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'avg_win': 0,
            'avg_loss': 0,
        }

    daily_returns = backtest_results['daily_return'].values
    cumul_pnl = backtest_results['cumul_pnl'].values

    # Total return
    total_return = (cumul_pnl[-1] - cumul_pnl[0]) / abs(cumul_pnl[0]) if cumul_pnl[0] != 0 else 0
    total_pnl = cumul_pnl[-1] - cumul_pnl[0]

    # Annualized return
    trading_days = len(daily_returns)
    annual_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0

    # Win rate
    wins = (daily_returns > 0).sum()
    win_rate = wins / len(daily_returns) if len(daily_returns) > 0 else 0

    # Max drawdown
    cumulative = np.cumprod(1 + daily_returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

    # Sharpe ratio
    if len(daily_returns) > 1:
        excess_returns = daily_returns - 0  # Assume 0% risk-free rate
        sharpe_ratio = np.mean(excess_returns) / (np.std(excess_returns) + 1e-8) * np.sqrt(252)
    else:
        sharpe_ratio = 0

    # Sortino ratio
    downside_returns = daily_returns[daily_returns < 0]
    if len(downside_returns) > 0:
        downside_std = np.std(downside_returns)
        sortino_ratio = np.mean(daily_returns) / (downside_std + 1e-8) * np.sqrt(252)
    else:
        sortino_ratio = sharpe_ratio

    # Average win/loss
    winning_days = daily_returns[daily_returns > 0]
    losing_days = daily_returns[daily_returns < 0]
    avg_win = np.mean(winning_days) if len(winning_days) > 0 else 0
    avg_loss = np.mean(losing_days) if len(losing_days) > 0 else 0

    return {
        'total_return': total_return * 100,
        'total_pnl': total_pnl,
        'annual_return': annual_return * 100,
        'win_rate': win_rate * 100,
        'max_drawdown': max_drawdown * 100,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'avg_win': avg_win * 100,
        'avg_loss': avg_loss * 100,
    }
