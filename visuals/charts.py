"""
Visualization module for options analysis.

Functions:
    - plot_mispricing_scatter: Mispricing vs strike
    - plot_iv_smile: IV vs strike
    - plot_greeks_surface: Greeks across strikes
    - plot_strategy_payoff: Strategy P&L diagram
    - plot_backtest_performance: Cumulative P&L
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import logging

logger = logging.getLogger(__name__)


def plot_mispricing_scatter(option_data, title="Option Mispricing"):
    """
    Scatter plot of mispricing vs strike price.

    Parameters:
        option_data (pd.DataFrame): Data with strike, pricing_error, option_type
        title (str): Chart title

    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    try:
        fig = go.Figure()

        calls = option_data[option_data['option_type'] == 'call']
        puts = option_data[option_data['option_type'] == 'put']

        # Add calls
        fig.add_trace(go.Scatter(
            x=calls['strike'],
            y=calls['pricing_error'],
            mode='markers',
            name='Calls',
            marker=dict(size=8, color='#1f77b4', symbol='circle'),
            text=calls[['strike', 'pricing_error', 'mispricing_pct']].apply(
                lambda x: f"Strike: ${x['strike']:.2f}<br>Error: ${x['pricing_error']:.2f}<br>%: {x['mispricing_pct']:.1f}%",
                axis=1
            ),
            hovertemplate='%{text}<extra></extra>',
        ))

        # Add puts
        fig.add_trace(go.Scatter(
            x=puts['strike'],
            y=puts['pricing_error'],
            mode='markers',
            name='Puts',
            marker=dict(size=8, color='#ff7f0e', symbol='square'),
            text=puts[['strike', 'pricing_error', 'mispricing_pct']].apply(
                lambda x: f"Strike: ${x['strike']:.2f}<br>Error: ${x['pricing_error']:.2f}<br>%: {x['mispricing_pct']:.1f}%",
                axis=1
            ),
            hovertemplate='%{text}<extra></extra>',
        ))

        # Add zero line
        fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.5)

        fig.update_layout(
            title=title,
            xaxis_title="Strike Price",
            yaxis_title="Pricing Error ($)",
            hovermode='closest',
            template='plotly_white',
            height=500,
            font=dict(size=11),
        )

        return fig

    except Exception as e:
        logger.error(f"Error plotting mispricing: {e}")
        return None


def plot_iv_smile(option_data, title="Implied Volatility Smile"):
    """
    Plot IV smile (IV vs strike/moneyness).

    Parameters:
        option_data (pd.DataFrame): Data with strike, impliedvolatility, option_type
        title (str): Chart title

    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    try:
        fig = go.Figure()

        calls = option_data[option_data['option_type'] == 'call'].copy()
        puts = option_data[option_data['option_type'] == 'put'].copy()

        # Filter valid IV
        calls = calls[calls['impliedvolatility'] > 0]
        puts = puts[puts['impliedvolatility'] > 0]

        if len(calls) > 0:
            fig.add_trace(go.Scatter(
                x=calls['strike'],
                y=calls['impliedvolatility'] * 100,
                mode='lines+markers',
                name='Call IV',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=6),
            ))

        if len(puts) > 0:
            fig.add_trace(go.Scatter(
                x=puts['strike'],
                y=puts['impliedvolatility'] * 100,
                mode='lines+markers',
                name='Put IV',
                line=dict(color='#ff7f0e', width=2),
                marker=dict(size=6),
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Strike Price",
            yaxis_title="Implied Volatility (%)",
            hovermode='x unified',
            template='plotly_white',
            height=500,
            font=dict(size=11),
        )

        return fig

    except Exception as e:
        logger.error(f"Error plotting IV smile: {e}")
        return None


def plot_greeks_heatmap(option_data, greek='delta', title="Greeks Heatmap"):
    """
    Heatmap of Greeks vs strike.

    Parameters:
        option_data (pd.DataFrame): Data with strike, option_type, greek columns
        greek (str): Greek to plot ('delta', 'gamma', 'vega', 'theta')
        title (str): Chart title

    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    try:
        greek_col = f'greeks_{greek}'
        if greek_col not in option_data.columns:
            return None

        calls = option_data[option_data['option_type'] == 'call'].sort_values('strike')
        puts = option_data[option_data['option_type'] == 'put'].sort_values('strike')

        fig = go.Figure()

        # Calls
        if len(calls) > 0:
            fig.add_trace(go.Scatter(
                x=calls['strike'],
                y=calls[greek_col],
                mode='lines+markers',
                name='Call',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
            ))

        # Puts
        if len(puts) > 0:
            fig.add_trace(go.Scatter(
                x=puts['strike'],
                y=puts[greek_col],
                mode='lines+markers',
                name='Put',
                line=dict(color='#ff7f0e', width=2),
                fill='tozeroy',
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Strike Price",
            yaxis_title=greek.capitalize(),
            hovermode='x unified',
            template='plotly_white',
            height=500,
            font=dict(size=11),
        )

        return fig

    except Exception as e:
        logger.error(f"Error plotting Greeks: {e}")
        return None


def plot_strategy_payoff(payoff_data, breakevens=None, title="Strategy Payoff Diagram"):
    """
    Plot strategy payoff diagram.

    Parameters:
        payoff_data (pd.DataFrame): Data with 'spot' and 'payoff' columns
        breakevens (list): List of breakeven spot prices
        title (str): Chart title

    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    try:
        fig = go.Figure()

        # Payoff line
        fig.add_trace(go.Scatter(
            x=payoff_data['spot'],
            y=payoff_data['payoff'],
            mode='lines',
            name='Payoff',
            line=dict(color='#1f77b4', width=3),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.2)',
        ))

        # Add zero line
        fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.5)

        # Add breakevens if provided
        if breakevens:
            for be in breakevens:
                fig.add_vline(x=be, line_dash='dot', line_color='red', opacity=0.5)

        fig.update_layout(
            title=title,
            xaxis_title="Stock Price at Expiration",
            yaxis_title="Profit / Loss ($)",
            hovermode='x unified',
            template='plotly_white',
            height=500,
            font=dict(size=11),
        )

        return fig

    except Exception as e:
        logger.error(f"Error plotting payoff: {e}")
        return None


def plot_backtest_performance(backtest_results, title="Backtest Cumulative P&L"):
    """
    Plot cumulative P&L from backtest.

    Parameters:
        backtest_results (pd.DataFrame): Data with 'date' and 'cumul_pnl' columns
        title (str): Chart title

    Returns:
        plotly.graph_objects.Figure: Plotly figure
    """
    try:
        if backtest_results.empty:
            return None

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=backtest_results['date'],
            y=backtest_results['cumul_pnl'],
            mode='lines',
            name='Cumulative P&L',
            line=dict(color='#2ca02c', width=2),
            fill='tozeroy',
            fillcolor='rgba(44, 160, 44, 0.2)',
        ))

        # Add zero line
        fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.5)

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Cumulative P&L ($)",
            hovermode='x unified',
            template='plotly_white',
            height=500,
            font=dict(size=11),
        )

        return fig

    except Exception as e:
        logger.error(f"Error plotting backtest: {e}")
        return None
