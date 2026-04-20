"""
Configuration and constants for the options pricing application.
"""

# Default parameters
DEFAULT_RISK_FREE_RATE = 0.05  # 5% annual
DEFAULT_TICKERS = [
    # Major Indices & ETFs
    "SPY",      # S&P 500 ETF
    "QQQ",      # Nasdaq-100 ETF
    "IWM",      # Russell 2000 ETF
    "DIA",      # Dow Jones ETF
    "VOO",      # Vanguard S&P 500 ETF
    "VTI",      # Vanguard Total Market ETF
    "^GSPC",    # S&P 500 Index
    "^IXIC",    # Nasdaq Composite Index
    "^RUT",     # Russell 2000 Index
    "^DJIA",    # Dow Jones Industrial Average

    # Mega-cap Tech
    "AAPL",     # Apple
    "MSFT",     # Microsoft
    "GOOGL",    # Alphabet/Google
    "AMZN",     # Amazon
    "NVDA",     # Nvidia
    "TSLA",     # Tesla
    "META",     # Meta/Facebook

    # Financials
    "JPM",      # JPMorgan Chase
    "BAC",      # Bank of America
    "WFC",      # Wells Fargo
    "GS",       # Goldman Sachs

    # Energy & Commodities
    "XOM",      # ExxonMobil
    "CVX",      # Chevron
    "COP",      # ConocoPhillips
    "USO",      # Oil ETF
    "GLD",      # Gold ETF
    "SLV",      # Silver ETF
    "DBC",      # Commodities ETF

    # Consumer & Retail
    "AMZN",     # Amazon
    "WMT",      # Walmart
    "MCD",      # McDonald's
    "NFLX",     # Netflix

    # Healthcare & Pharma
    "JNJ",      # Johnson & Johnson
    "PFE",      # Pfizer
    "ABBV",     # AbbVie
    "LLY",      # Eli Lilly
    "MRK",      # Merck

    # Industrials
    "BA",       # Boeing
    "CAT",      # Caterpillar
    "GE",       # General Electric
    "HON",      # Honeywell

    # Consumer Staples
    "PG",       # Procter & Gamble
    "KO",       # Coca-Cola
    "PEP",      # PepsiCo
    "COST",     # Costco

    # Fixed Income & Bonds
    "TLT",      # 20+ Year Treasury ETF
    "BND",      # Total Bond Market ETF
    "LQD",      # Investment Grade Corporate Bonds
    "HYG",      # High Yield Bonds

    # International & Emerging
    "EEM",      # MSCI Emerging Markets ETF
    "VEA",      # MSCI EAFE ETF
    "EWJ",      # iShares MSCI Japan ETF
    "FXI",      # iShares China Large-Cap ETF

    # Semiconductors & Tech Hardware
    "CHIP",     # SOXX Semiconductor ETF
    "SMH",      # iShares Semiconductor ETF
    "AMD",      # Advanced Micro Devices
    "INTC",     # Intel
    "QCOM",     # Qualcomm

    # Communication Services
    "NFLX",     # Netflix
    "DIS",      # Disney
    "CMCSA",    # Comcast

    # Volatility
    "^VIX",     # VIX Volatility Index
    "UVXY",     # 3x Inverse VIX
    "VIXY",     # VIX Short-Term ETN
]

# Time bounds (in days)
MIN_TIME_TO_EXPIRY = 1
MAX_TIME_TO_EXPIRY = 730  # ~2 years

# Volatility bounds (annualized)
MIN_VOLATILITY = 0.001   # 0.1%
MAX_VOLATILITY = 3.0     # 300%

# IV solver parameters
IV_SOLVER_TOLERANCE = 1e-6
IV_SOLVER_MAX_ITERATIONS = 100
IV_SOLVER_BOUNDS = (0.0001, 3.0)

# Mispricing thresholds
MISPRICING_ZSCORE_THRESHOLD = 2.0  # 2 standard deviations
PCP_VIOLATION_THRESHOLD = 0.01     # $0.01 put-call parity violation

# Strategy parameters
STRADDLE_MIN_IV_PERCENTILE = 75
IRON_CONDOR_OTM_WIDTH = 0.10  # 10% OTM
SPREAD_WIDTH_FACTOR = 2

# Backtesting parameters
BACKTEST_LOOKBACK_YEARS = 2
BACKTEST_REBALANCE_FREQ = 5  # days
BACKTEST_TRANSACTION_COST = 0.0005  # 5 bps

# Display parameters
DP_PRICE = 2       # decimal places for prices
DP_PERCENT = 2     # decimal places for percentages
DP_DELTA = 4       # decimal places for Greeks
DP_VOLATILITY = 4  # decimal places for IV/sigma

# Visualization
CHART_HEIGHT_PX = 500
CHART_WIDTH_PX = 900
