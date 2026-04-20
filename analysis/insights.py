"""
Insight generation module - professional, data-driven insights.

Functions:
    - generate_insights: Generate text-based analysis
    - format_insights: Format insights for display
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def generate_insights(option_data, spot_price, pricing_summary, vol_consistency, pcp_violations):
    """
    Generate professional, structured insights.

    Parameters:
        option_data (pd.DataFrame): Complete processed option data
        spot_price (float): Current spot price
        pricing_summary (dict): From pricing.mispricing_summary()
        vol_consistency (dict): From arbitrage.check_volatility_consistency()
        pcp_violations (pd.DataFrame): From data.cleaner.validate_put_call_parity()

    Returns:
        list: Insights (strings), prioritized by importance
    """
    insights = []

    # 1. Mispricing pattern
    overpriced_pct = pricing_summary.get('overpriced_pct', 0)
    significant_count = pricing_summary.get('significant_mispricings', 0)
    total_options = pricing_summary.get('total_options', 1)

    if significant_count > 0:
        if overpriced_pct > 60:
            insights.append(
                f"Market appears biased toward overpricing. {overpriced_pct:.0f}% of options are overpriced; "
                f"{significant_count} exhibit significant ({pricing_summary.get('avg_error_pct', 0):.1f}% avg) mispricing."
            )
        elif overpriced_pct < 40:
            insights.append(
                f"Market appears biased toward underpricing. {100-overpriced_pct:.0f}% of options are underpriced; "
                f"{significant_count} exhibit significant mispricing."
            )
        else:
            insights.append(
                f"Mixed pricing patterns observed. {significant_count} options show significant mispricing "
                f"(avg {pricing_summary.get('avg_error_pct', 0):.1f}%)."
            )

    # 2. Implied vs Historical Volatility
    if vol_consistency.get('iv_vs_hv_ratio') is not None:
        ratio = vol_consistency['iv_vs_hv_ratio']
        high_iv_count = vol_consistency.get('high_iv_count', 0)

        if ratio > 1.5:
            insights.append(
                f"Implied volatility elevated ({vol_consistency['avg_iv']:.1%}) vs historical ({vol_consistency['hist_vol']:.1%}). "
                f"{high_iv_count} options priced for elevated future volatility; potential overpricing if realized vol remains low."
            )
        elif ratio < 0.75:
            insights.append(
                f"Implied volatility depressed ({vol_consistency['avg_iv']:.1%}) vs historical ({vol_consistency['hist_vol']:.1%}). "
                f"Options may offer value if historical volatility persists."
            )

    # 3. Put-call parity violations
    if not pcp_violations.empty:
        worst_violation = pcp_violations['violation'].max()
        insights.append(
            f"Put-call parity violations detected at {len(pcp_violations)} strikes (max: ${worst_violation:.2f}). "
            f"May indicate data quality issues or arbitrage opportunities."
        )

    # 4. Greeks patterns
    if len(option_data) > 0:
        calls = option_data[option_data['option_type'] == 'call']
        puts = option_data[option_data['option_type'] == 'put']

        if len(calls) > 0:
            avg_call_gamma = calls['greeks_gamma'].mean()
            avg_call_vega = calls['greeks_vega'].mean()

            if avg_call_gamma > 0.005:
                insights.append(
                    f"High gamma observed in calls (avg: {avg_call_gamma:.4f}). "
                    f"Expected move pricing may be tight; delta hedging costs could be significant."
                )

            if avg_call_vega > 0.20:
                insights.append(
                    f"High vega exposure in calls (avg: {avg_call_vega:.2f}). "
                    f"Option values highly sensitive to volatility changes."
                )

    # 5. Moneyness distribution
    calls = option_data[option_data['option_type'] == 'call'].copy()
    puts = option_data[option_data['option_type'] == 'put'].copy()

    if len(calls) > 0:
        calls['moneyness'] = calls['strike'] / spot_price
        calls['otm_pct'] = ((calls['strike'] - spot_price) / spot_price * 100).abs()

        far_otm = (calls['moneyness'] > 1.10).sum()
        itm = (calls['moneyness'] < 0.95).sum()

        if far_otm > len(calls) * 0.3:
            insights.append(
                f"Call skew biased toward OTM strikes ({far_otm} of {len(calls)}). "
                f"Market pricing elevated tail risk or crash protection is expensive."
            )

    # 6. Volume and liquidity
    high_volume = (option_data['volume'] > option_data['volume'].quantile(0.75)).sum()
    low_volume = (option_data['volume'] < option_data['volume'].quantile(0.25)).sum()

    if high_volume < len(option_data) * 0.2:
        insights.append(
            f"Low trading volume across chain ({high_volume} of {len(option_data)} options in top quartile). "
            f"Wide bid-ask spreads likely; execution costs high."
        )

    if insights:
        return insights[:5]  # Return top 5 insights
    else:
        return ["No significant patterns identified. Market pricing appears balanced."]


def format_insights(insights):
    """
    Format insights for display in Streamlit.

    Parameters:
        insights (list): List of insight strings

    Returns:
        str: Formatted insights for display
    """
    if not insights:
        return "No insights available."

    formatted = "\n\n".join([f"• {insight}" for insight in insights])
    return formatted


def get_strategy_insights(option_data, vol_consistency, spot_price):
    """
    Generate strategy recommendations based on market conditions.

    Parameters:
        option_data (pd.DataFrame): Option data
        vol_consistency (dict): IV vs HV comparison
        spot_price (float): Current spot price

    Returns:
        list: Strategy recommendations
    """
    recommendations = []

    # High IV check
    if vol_consistency.get('iv_vs_hv_ratio') and vol_consistency['iv_vs_hv_ratio'] > 1.3:
        recommendations.append(
            "High IV environment: Consider selling volatility (Iron Condor, Short Straddle) "
            "if you expect mean reversion or lower realized volatility."
        )

    # Low IV check
    if vol_consistency.get('iv_vs_hv_ratio') and vol_consistency['iv_vs_hv_ratio'] < 0.9:
        recommendations.append(
            "Low IV environment: Consider buying volatility (Long Straddle, Calendar Spreads) "
            "if you expect realized volatility to increase."
        )

    # ATM concentration
    calls = option_data[option_data['option_type'] == 'call'].copy()
    if len(calls) > 0:
        calls['moneyness'] = calls['strike'] / spot_price
        atm_count = ((calls['moneyness'] > 0.95) & (calls['moneyness'] < 1.05)).sum()

        if atm_count > len(calls) * 0.3:
            recommendations.append(
                "ATM liquidity high. Consider spreads (Bull Call, Bear Put) "
                "for reduced cost and directional exposure."
            )

    # Skew pattern (if data supports)
    if len(calls) > 5:
        far_otm_iv = calls[calls['strike'] > spot_price * 1.10]['impliedvolatility'].mean()
        itm_iv = calls[calls['strike'] < spot_price * 0.95]['impliedvolatility'].mean()

        if not np.isnan(far_otm_iv) and not np.isnan(itm_iv):
            if far_otm_iv > itm_iv * 1.15:
                recommendations.append(
                    "Volatility skew present (OTM calls elevated). Market pricing crash protection; "
                    "consider call spreads to sell expensive OTM vol."
                )

    return recommendations[:3]  # Top 3 recommendations
