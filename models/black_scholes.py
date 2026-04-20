"""
Black-Scholes option pricing model and Greeks calculations.

Functions:
    - black_scholes: Price calls and puts using BS formula
    - delta, gamma, vega, theta, rho: Greeks calculations
"""

import numpy as np
from scipy.stats import norm
from config import MIN_VOLATILITY, MAX_VOLATILITY


def black_scholes(S, K, T, r, sigma, option_type='call'):
    """
    Black-Scholes European option pricing.

    Parameters:
        S (float): Current spot price
        K (float): Strike price
        T (float): Time to maturity (years)
        r (float): Risk-free rate (annualized)
        sigma (float): Volatility (annualized)
        option_type (str): 'call' or 'put'

    Returns:
        float: Option price

    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if S <= 0 or K <= 0 or T < 0 or sigma < 0:
        raise ValueError(f"Invalid inputs: S={S}, K={K}, T={T}, sigma={sigma}")

    if sigma < MIN_VOLATILITY or sigma > MAX_VOLATILITY:
        raise ValueError(f"Volatility {sigma:.4f} outside bounds [{MIN_VOLATILITY}, {MAX_VOLATILITY}]")

    # Handle edge case: T = 0
    if T < 1e-6:
        if option_type.lower() == 'call':
            return max(S - K, 0)
        else:
            return max(K - S, 0)

    # Calculate d1, d2
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # Calculate price
    if option_type.lower() == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type.lower() == 'put':
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError(f"Unknown option type: {option_type}")

    return price


def delta(S, K, T, r, sigma, option_type='call'):
    """
    Option Delta (Δ) - sensitivity to spot price changes.

    Parameters:
        S, K, T, r, sigma: See black_scholes
        option_type: 'call' or 'put'

    Returns:
        float: Delta (change in price per $1 move in spot)
    """
    if T < 1e-6 or sigma < MIN_VOLATILITY:
        return 1.0 if option_type.lower() == 'call' and S > K else 0.0

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    if option_type.lower() == 'call':
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1.0


def gamma(S, K, T, r, sigma):
    """
    Option Gamma (Γ) - second derivative, curvature of price.

    Parameters:
        S, K, T, r, sigma: See black_scholes

    Returns:
        float: Gamma (delta per $1 move in spot)
    """
    if T < 1e-6 or sigma < MIN_VOLATILITY:
        return 0.0

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))


def vega(S, K, T, r, sigma):
    """
    Option Vega (ν) - sensitivity to volatility changes.

    Parameters:
        S, K, T, r, sigma: See black_scholes

    Returns:
        float: Vega (change in price per 1% change in sigma)
    """
    if T < 1e-6 or sigma < MIN_VOLATILITY:
        return 0.0

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return S * norm.pdf(d1) * np.sqrt(T) / 100.0  # Divided by 100 for 1% change


def theta(S, K, T, r, sigma, option_type='call'):
    """
    Option Theta (Θ) - time decay (daily).

    Parameters:
        S, K, T, r, sigma: See black_scholes
        option_type: 'call' or 'put'

    Returns:
        float: Daily theta (price decay per day)
    """
    if T < 1e-6 or sigma < MIN_VOLATILITY:
        return 0.0

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type.lower() == 'call':
        theta_val = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                     - r * K * np.exp(-r * T) * norm.cdf(d2))
    else:
        theta_val = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                     + r * K * np.exp(-r * T) * norm.cdf(-d2))

    return theta_val / 365.0  # Convert to daily


def rho(S, K, T, r, sigma, option_type='call'):
    """
    Option Rho (ρ) - sensitivity to interest rate changes.

    Parameters:
        S, K, T, r, sigma: See black_scholes
        option_type: 'call' or 'put'

    Returns:
        float: Rho (change in price per 1% change in rate)
    """
    if T < 1e-6 or sigma < MIN_VOLATILITY:
        return 0.0

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type.lower() == 'call':
        return K * T * np.exp(-r * T) * norm.cdf(d2) / 100.0
    else:
        return -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100.0


def all_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Compute all Greeks at once.

    Parameters:
        S, K, T, r, sigma, option_type: See black_scholes

    Returns:
        dict: Dictionary with keys 'delta', 'gamma', 'vega', 'theta', 'rho'
    """
    return {
        'delta': delta(S, K, T, r, sigma, option_type),
        'gamma': gamma(S, K, T, r, sigma),
        'vega': vega(S, K, T, r, sigma),
        'theta': theta(S, K, T, r, sigma, option_type),
        'rho': rho(S, K, T, r, sigma, option_type),
    }
