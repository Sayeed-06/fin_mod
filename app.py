"""
Professional Options Pricing and Analysis Dashboard
Black-Scholes Model-based Options Analysis

A minimalistic Streamlit application for quantitative options analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Import modules
from config import (
    DEFAULT_TICKERS, DEFAULT_RISK_FREE_RATE, MIN_TIME_TO_EXPIRY, MAX_TIME_TO_EXPIRY,
    MISPRICING_ZSCORE_THRESHOLD, DP_PRICE, DP_PERCENT, DP_DELTA, DP_VOLATILITY
)
from data.fetcher import get_expirations, fetch_option_chain, get_current_price, get_historical_volatility
from data.cleaner import clean_option_chain, validate_put_call_parity
from analysis.pricing import compute_theoretical_prices, compute_mispricing, mispricing_summary
from analysis.arbitrage import check_price_bounds, check_volatility_consistency, detect_arbitrage_opportunities
from analysis.insights import generate_insights, format_insights, get_strategy_insights
from strategy.selector import suggest_strategies, calculate_payoff
from backtest.engine import run_backtest, compute_backtest_metrics
from visuals.charts import (
    plot_mispricing_scatter, plot_iv_smile, plot_greeks_heatmap,
    plot_strategy_payoff, plot_backtest_performance
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page config
st.set_page_config(
    page_title="Options Pricing Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Remove Streamlit branding
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=300)
def fetch_and_clean_data(ticker, expiration, risk_free_rate):
    """Fetch and clean option chain data."""
    spot = get_current_price(ticker)
    if spot is None:
        return None, None, None, None

    raw_chain = fetch_option_chain(ticker, expiration)
    if raw_chain is None or raw_chain.empty:
        return spot, None, None, None

    cleaned_chain = clean_option_chain(raw_chain, spot, expiration, risk_free_rate)
    if cleaned_chain is None or cleaned_chain.empty:
        return spot, raw_chain, None, None

    hist_vol = get_historical_volatility(ticker, lookback_days=30)
    return spot, cleaned_chain, hist_vol, None


def main():
    """Main application."""
    st.title("Options Pricing Dashboard")
    st.markdown("Professional quantitative analysis using the Black-Scholes model")

    # Sidebar controls
    st.sidebar.header("Configuration")

    ticker = st.sidebar.selectbox(
        "Select Symbol",
        DEFAULT_TICKERS,
        index=0,
        help="Stock or ETF ticker symbol"
    )

    expirations = get_expirations(ticker, limit=20)
    if expirations is None or len(expirations) == 0:
        st.error(f"No options available for {ticker}. Please select a different symbol.")
        return

    expiration = st.sidebar.selectbox(
        "Select Expiration",
        expirations,
        index=0,
        help="Option expiration date"
    )

    risk_free_rate = st.sidebar.slider(
        "Risk-Free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=DEFAULT_RISK_FREE_RATE * 100,
        step=0.1,
        help="Annual risk-free rate (Treasury yield)"
    ) / 100.0

    # Fetch data
    with st.spinner("Fetching data..."):
        spot_price, option_data, hist_vol, _ = fetch_and_clean_data(ticker, expiration, risk_free_rate)

    if option_data is None or option_data.empty:
        st.error("Unable to fetch or process option data. Please try a different symbol or expiration.")
        return

    # Compute theoretical prices and Greeks
    option_data = compute_theoretical_prices(option_data, spot_price, risk_free_rate)
    option_data = compute_mispricing(option_data)

    # Compute analysis metrics
    pricing_summary = mispricing_summary(option_data, MISPRICING_ZSCORE_THRESHOLD)
    vol_consistency = check_volatility_consistency(option_data, hist_vol)
    pcp_violations = validate_put_call_parity(option_data, spot_price, risk_free_rate)

    # Display header metrics
    st.subheader("Market Snapshot")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Spot Price", f"${spot_price:.2f}")
    with col2:
        st.metric("Options Analyzed", pricing_summary['total_options'])
    with col3:
        st.metric("Avg Mispricing", f"{pricing_summary['avg_error_pct']:.2f}%")
    with col4:
        st.metric("Market IV", f"{vol_consistency.get('avg_iv', 0):.2%}")
    with col5:
        if vol_consistency.get('hist_vol'):
            st.metric("Historical Vol", f"{vol_consistency['hist_vol']:.2%}")

    # Insights section
    st.subheader("Market Insights")
    insights = generate_insights(option_data, spot_price, pricing_summary, vol_consistency, pcp_violations)
    st.markdown(format_insights(insights))

    # Tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Option Chain", "Greeks", "Arbitrage", "Strategies", "Backtest"])

    # Tab 1: Option Chain
    with tab1:
        st.subheader("Option Chain Analysis")

        calls = option_data[option_data['option_type'] == 'call'].copy()
        puts = option_data[option_data['option_type'] == 'put'].copy()

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Calls**")
            calls_display = calls[[
                'strike', 'bid', 'ask', 'mid', 'impliedvolatility', 'theoretical_price',
                'pricing_error', 'greeks_delta', 'greeks_gamma', 'volume'
            ]].copy()
            calls_display.columns = [
                'Strike', 'Bid', 'Ask', 'Mid', 'IV', 'Theo', 'Error', 'Δ', 'Γ', 'Volume'
            ]
            calls_display = calls_display.round({
                'Bid': DP_PRICE, 'Ask': DP_PRICE, 'Mid': DP_PRICE, 'Theo': DP_PRICE,
                'IV': DP_VOLATILITY, 'Error': DP_PRICE, 'Δ': DP_DELTA,
                'Γ': 6, 'Volume': 0,
            })
            st.dataframe(calls_display, use_container_width=True, height=400)

        with col2:
            st.write("**Puts**")
            puts_display = puts[[
                'strike', 'bid', 'ask', 'mid', 'impliedvolatility', 'theoretical_price',
                'pricing_error', 'greeks_delta', 'greeks_gamma', 'volume'
            ]].copy()
            puts_display.columns = [
                'Strike', 'Bid', 'Ask', 'Mid', 'IV', 'Theo', 'Error', 'Δ', 'Γ', 'Volume'
            ]
            puts_display = puts_display.round({
                'Bid': DP_PRICE, 'Ask': DP_PRICE, 'Mid': DP_PRICE, 'Theo': DP_PRICE,
                'IV': DP_VOLATILITY, 'Error': DP_PRICE, 'Δ': DP_DELTA,
                'Γ': 6, 'Volume': 0,
            })
            st.dataframe(puts_display, use_container_width=True, height=400)

        # Visualizations
        st.write("**Pricing Analysis**")
        col1, col2 = st.columns(2)

        with col1:
            fig_mispricing = plot_mispricing_scatter(option_data, "Mispricing vs Strike")
            if fig_mispricing:
                st.plotly_chart(fig_mispricing, use_container_width=True)

        with col2:
            fig_iv = plot_iv_smile(option_data, "Implied Volatility Smile")
            if fig_iv:
                st.plotly_chart(fig_iv, use_container_width=True)

    # Tab 2: Greeks
    with tab2:
        st.subheader("Greeks Analysis")

        greek_selector = st.selectbox(
            "Select Greek",
            ['delta', 'gamma', 'vega', 'theta'],
            key='greeks_selector'
        )

        col1, col2 = st.columns(2)

        with col1:
            fig_delta = plot_greeks_heatmap(option_data, greek_selector, f"{greek_selector.upper()} vs Strike")
            if fig_delta:
                st.plotly_chart(fig_delta, use_container_width=True)

        with col2:
            st.write(f"**{greek_selector.upper()} Summary**")
            greeks_summary = {
                'Calls Avg': option_data[option_data['option_type'] == 'call'][f'greeks_{greek_selector}'].mean(),
                'Puts Avg': option_data[option_data['option_type'] == 'put'][f'greeks_{greek_selector}'].mean(),
                'Max': option_data[f'greeks_{greek_selector}'].max(),
                'Min': option_data[f'greeks_{greek_selector}'].min(),
                'Std Dev': option_data[f'greeks_{greek_selector}'].std(),
            }
            st.json({k: f"{v:.4f}" for k, v in greeks_summary.items()})

    # Tab 3: Arbitrage
    with tab3:
        st.subheader("Arbitrage Detection")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Price Bound Violations**")
            bound_violations = check_price_bounds(option_data, spot_price, risk_free_rate)
            if not bound_violations.empty:
                st.dataframe(bound_violations, use_container_width=True, height=300)
            else:
                st.info("No price bound violations detected.")

        with col2:
            st.write("**Put-Call Parity Violations**")
            if not pcp_violations.empty:
                st.dataframe(pcp_violations.round(2), use_container_width=True, height=300)
            else:
                st.info("No put-call parity violations detected.")

        st.write("**Mispricing Opportunities**")
        arb_opps = detect_arbitrage_opportunities(option_data, spot_price, risk_free_rate, threshold_percent=1.0)
        if not arb_opps.empty:
            st.dataframe(arb_opps.round(DP_PRICE), use_container_width=True)
        else:
            st.info("No significant arbitrage opportunities detected.")

    # Tab 4: Strategies
    with tab4:
        st.subheader("Strategy Recommendations")

        strategies = suggest_strategies(option_data, spot_price, vol_consistency)
        strategy_recommendations = get_strategy_insights(option_data, vol_consistency, spot_price)

        if strategy_recommendations:
            st.write("**Suggested Approaches**")
            for rec in strategy_recommendations:
                st.markdown(f"• {rec}")

        st.write("**Detailed Strategies**")
        for i, strategy in enumerate(strategies):
            with st.expander(f"{strategy['name']}", expanded=(i == 0)):
                st.write(f"**Description:** {strategy['description']}")
                st.write(f"**Rationale:** {strategy['rationale']}")
                st.write(f"**Condition:** {strategy['condition']}")
                st.write(f"**Risk Profile:** {strategy['risk_profile']}")

                # Simple payoff diagram for straddle
                if strategy['symbol'] == 'STRADDLE':
                    calls_atm = option_data[
                        (option_data['option_type'] == 'call') &
                        (option_data['strike'] >= spot_price * 0.99) &
                        (option_data['strike'] <= spot_price * 1.01)
                    ]
                    puts_atm = option_data[
                        (option_data['option_type'] == 'put') &
                        (option_data['strike'] >= spot_price * 0.99) &
                        (option_data['strike'] <= spot_price * 1.01)
                    ]

                    if not calls_atm.empty and not puts_atm.empty:
                        call_strike = calls_atm['strike'].iloc[0]
                        put_strike = puts_atm['strike'].iloc[0]
                        call_price = calls_atm['mid'].iloc[0]
                        put_price = puts_atm['mid'].iloc[0]

                        positions = [
                            {'type': 'call', 'strike': call_strike, 'price': call_price, 'quantity': 1, 'direction': 'long'},
                            {'type': 'put', 'strike': put_strike, 'price': put_price, 'quantity': 1, 'direction': 'long'},
                        ]

                        payoff_df = calculate_payoff(spot_price, positions)
                        fig_payoff = plot_strategy_payoff(payoff_df, title=f"{strategy['name']} Payoff")
                        if fig_payoff:
                            st.plotly_chart(fig_payoff, use_container_width=True)

    # Tab 5: Backtest
    with tab5:
        st.subheader("Strategy Backtesting")

        st.info("Simple backtest: Buy underpriced options, sell overpriced options. Assumes entry at mid price, exit at theoretical.")

        strategy_choice = st.radio("Strategy:", ["Long Underpriced", "Short Overpriced"])
        strategy_name = 'long_mispriced' if strategy_choice == "Long Underpriced" else 'short_mispriced'

        if st.button("Run Backtest"):
            with st.spinner("Running backtest..."):
                # Generate dummy historical data (in production, use real historical data)
                dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
                spot_hist = pd.Series(
                    spot_price * (1 + np.cumsum(np.random.randn(60) * 0.01)),
                    index=dates
                )

                backtest_results = run_backtest(option_data, spot_hist, strategy_name)

                if not backtest_results.empty:
                    metrics = compute_backtest_metrics(backtest_results)

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total P&L", f"${metrics['total_pnl']:.2f}")
                    with col2:
                        st.metric("Total Return", f"{metrics['total_return']:.2f}%")
                    with col3:
                        st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
                    with col4:
                        st.metric("Max Drawdown", f"{metrics['max_drawdown']:.2f}%")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
                    with col2:
                        st.metric("Avg Win/Loss", f"{metrics['avg_win']:.2f}% / {metrics['avg_loss']:.2f}%")

                    fig_bt = plot_backtest_performance(backtest_results, f"{strategy_choice} - Cumulative P&L")
                    if fig_bt:
                        st.plotly_chart(fig_bt, use_container_width=True)
                else:
                    st.warning("No backtest data available.")


if __name__ == "__main__":
    main()
