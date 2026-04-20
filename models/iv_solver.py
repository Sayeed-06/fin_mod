"""
Implied Volatility solver using Newton-Raphson and Bisection methods.

Functions:
    - implied_volatility: Main solver
    - _newton_raphson_iv: Newton-Raphson method
    - _bisection_iv: Bisection method fallback
"""

import numpy as np
from models.black_scholes import black_scholes, vega
from config import (
    IV_SOLVER_TOLERANCE,
    IV_SOLVER_MAX_ITERATIONS,
    IV_SOLVER_BOUNDS,
    MIN_VOLATILITY,
)


def implied_volatility(S, K, T, r, market_price, option_type='call'):
    """
    Compute implied volatility from market price.

    Uses Newton-Raphson with bisection fallback for robustness.

    Parameters:
        S (float): Current spot price
        K (float): Strike price
        T (float): Time to maturity (years)
        r (float): Risk-free rate
        market_price (float): Observed option price
        option_type (str): 'call' or 'put'

    Returns:
        float: Implied volatility (annualized)
        None: If IV cannot be computed

    Notes:
        - Returns None if market price violates option price bounds
        - Returns None if convergence fails
    """
    # Validate market price
    if option_type.lower() == 'call':
        lower_bound = max(0, S - K * np.exp(-r * T))
        upper_bound = S
    else:
        lower_bound = max(0, K * np.exp(-r * T) - S)
        upper_bound = K * np.exp(-r * T)

    if market_price < lower_bound or market_price > upper_bound:
        return None

    # Try Newton-Raphson first
    iv = _newton_raphson_iv(S, K, T, r, market_price, option_type)

    # Fallback to Bisection if NR fails
    if iv is None:
        iv = _bisection_iv(S, K, T, r, market_price, option_type)

    return iv


def _newton_raphson_iv(S, K, T, r, market_price, option_type='call'):
    """
    Newton-Raphson solver for implied volatility.

    Uses vega as the derivative for faster convergence.

    Parameters:
        S, K, T, r, market_price, option_type: See implied_volatility

    Returns:
        float: IV or None if failed
    """
    # Initial guess: Brenner-Subrahmanyam approximation
    sigma = np.sqrt(2 * np.pi / T) * (market_price / S)
    sigma = max(MIN_VOLATILITY, min(IV_SOLVER_BOUNDS[1], sigma))

    for iteration in range(IV_SOLVER_MAX_ITERATIONS):
        try:
            bs_price = black_scholes(S, K, T, r, sigma, option_type)
            price_diff = bs_price - market_price

            # Check convergence
            if abs(price_diff) < IV_SOLVER_TOLERANCE:
                return sigma

            # Calculate vega (derivative)
            v = vega(S, K, T, r, sigma)
            if abs(v) < 1e-8:  # Vega too small, Newton-Raphson ineffective
                return None

            # Newton-Raphson step
            sigma_new = sigma - price_diff / v

            # Ensure sigma stays in bounds
            sigma_new = max(IV_SOLVER_BOUNDS[0], min(IV_SOLVER_BOUNDS[1], sigma_new))

            # Check for no progress
            if abs(sigma_new - sigma) < 1e-8:
                return sigma_new

            sigma = sigma_new

        except (ValueError, RuntimeWarning):
            return None

    return None


def _bisection_iv(S, K, T, r, market_price, option_type='call'):
    """
    Bisection solver for implied volatility.

    More robust than Newton-Raphson, slower convergence.

    Parameters:
        S, K, T, r, market_price, option_type: See implied_volatility

    Returns:
        float: IV or None if failed
    """
    low, high = IV_SOLVER_BOUNDS

    # Verify bounds have opposite signs
    try:
        bs_low = black_scholes(S, K, T, r, low, option_type)
        bs_high = black_scholes(S, K, T, r, high, option_type)
    except (ValueError, RuntimeWarning):
        return None

    if (bs_low - market_price) * (bs_high - market_price) > 0:
        # Market price outside bounds, cannot solve
        return None

    for iteration in range(IV_SOLVER_MAX_ITERATIONS):
        mid = (low + high) / 2.0

        try:
            bs_mid = black_scholes(S, K, T, r, mid, option_type)
            price_diff = bs_mid - market_price

            if abs(price_diff) < IV_SOLVER_TOLERANCE:
                return mid

            if price_diff > 0:
                high = mid
            else:
                low = mid

            if (high - low) < IV_SOLVER_TOLERANCE:
                return (low + high) / 2.0

        except (ValueError, RuntimeWarning):
            return None

    return (low + high) / 2.0
