# Options Pricing and Analysis Dashboard

A professional, minimalistic Streamlit application for quantitative options analysis using the Black-Scholes model.

## Overview

This dashboard provides comprehensive options pricing analysis with a focus on clarity, numerical accuracy, and actionable insights. It features:

- **Black-Scholes Pricing**: Theoretical option pricing with automatic Greeks calculation
- **Implied Volatility**: Newton-Raphson solver with bisection fallback
- **Arbitrage Detection**: Identifies put-call parity violations and pricing anomalies
- **Greeks Analysis**: Delta, Gamma, Vega, and Theta across the entire option chain
- **Strategy Recommendations**: Automated suggestions based on volatility environment
- **Backtesting**: Simple historical simulation of pricing strategies
- **Professional Visualizations**: Minimalistic charts using Plotly and Matplotlib

## Installation

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

1. Clone the repository and navigate to the directory:
```bash
cd /Users/sayeed/finmod
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The dashboard will open in your default browser at `http://localhost:8501`.

### Features

#### 1. Market Snapshot
- Current spot price
- Number of options analyzed
- Average mispricing
- Market IV vs Historical IV

#### 2. Market Insights
Professional text-based analysis covering:
- Mispricing patterns (overpriced vs underpriced bias)
- Implied vs Historical volatility comparison
- Put-call parity violations
- Greeks patterns (gamma, vega exposure)
- Volume and liquidity conditions

#### 3. Option Chain Tab
Detailed call and put option data:
- Strike price, bid/ask prices, mid price
- Implied volatility
- Theoretical vs market prices
- Greeks (Delta, Gamma)
- Trading volume

Visualizations:
- Mispricing scatter plot (market error vs strike)
- IV smile (volatility curve)

#### 4. Greeks Tab
Interactive Greeks analysis:
- Select any Greek (Delta, Gamma, Vega, Theta)
- View Greeks across strikes
- Summary statistics (mean, max, min, std dev)

#### 5. Arbitrage Tab
Identify trading opportunities:
- Price bound violations (boxes arbitrage)
- Put-call parity violations (conversion/reversal arbitrage)
- Mispricing opportunities (market vs theoretical)

#### 6. Strategies Tab
Automated strategy recommendations:
- Long Straddle (low IV environment)
- Iron Condor (high IV environment)
- Bull Call Spread (bullish directional)
- Bear Put Spread (bearish income)
- Calendar Spread (theta decay play)

Each strategy includes:
- Description and rationale
- Market conditions
- Risk profile
- Payoff diagrams (where applicable)

#### 7. Backtest Tab
Historical simulation:
- Strategy: Buy underpriced options or sell overpriced options
- Performance metrics:
  - Total P&L and return
  - Sharpe ratio and Sortino ratio
  - Max drawdown and win rate
  - Average win/loss per trade
- Cumulative P&L chart

## Configuration

Key parameters are in `config.py`:

```python
DEFAULT_RISK_FREE_RATE = 0.05          # 5% risk-free rate
DEFAULT_TICKERS = ["SPY", "QQQ", ...]  # Available symbols
MISPRICING_ZSCORE_THRESHOLD = 2.0      # Significance threshold
IV_SOLVER_TOLERANCE = 1e-6             # Implied vol precision
```

## Project Structure

```
finmod/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration and constants
├── requirements.txt          # Python dependencies
├── models/
│   ├── black_scholes.py     # BS pricing and Greeks
│   └── iv_solver.py         # Implied volatility calculation
├── data/
│   ├── fetcher.py           # yfinance data retrieval
│   └── cleaner.py           # Data validation and cleaning
├── analysis/
│   ├── pricing.py           # Pricing error analysis
│   ├── arbitrage.py         # Arbitrage detection
│   └── insights.py          # Insight generation
├── strategy/
│   └── selector.py          # Strategy recommendations
├── backtest/
│   └── engine.py            # Historical simulation
└── visuals/
    └── charts.py            # Plotting and visualization
```

## Mathematical Foundation

### Black-Scholes Formula

Call Option:
```
C = S₀ × N(d₁) - K × e^(-rT) × N(d₂)
```

Put Option:
```
P = K × e^(-rT) × N(-d₂) - S₀ × N(-d₁)
```

Where:
- d₁ = [ln(S₀/K) + (r + σ²/2)T] / (σ√T)
- d₂ = d₁ - σ√T
- N(x) = cumulative standard normal distribution

### Greeks

- **Delta (Δ)**: Price sensitivity to spot moves
- **Gamma (Γ)**: Delta sensitivity (convexity)
- **Vega (ν)**: Volatility sensitivity
- **Theta (Θ)**: Time decay (daily)
- **Rho (ρ)**: Interest rate sensitivity

### Implied Volatility

Calculated using:
1. **Newton-Raphson**: Fast convergence, uses vega as derivative
2. **Bisection**: Robust fallback method

## Data Sources

Option chain data is fetched from **Yahoo Finance** via the `yfinance` library, including:
- Strike prices
- Bid/Ask prices
- Implied volatility (where available)
- Trading volume
- Open interest

Historical price data is used to calculate:
- Historical volatility (30-day rolling)
- For comparison with market IV

## Disclaimer

This application is for educational and research purposes only. It is not intended as financial advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.

The Black-Scholes model assumes:
- European-style options (exercise only at expiration)
- No dividends
- Constant volatility
- Log-normal price distribution
- No transaction costs

Real options may violate these assumptions, affecting pricing accuracy.

## Performance Considerations

- **Data Caching**: Option chain data is cached for 5 minutes to improve performance
- **IV Tolerance**: Set to 1e-6 for high precision; increase for faster computation
- **Backtest**: Limited to 60 trading days by default; extend as needed

## Troubleshooting

### No options available
- Try a different symbol (SPY, QQQ, etc.)
- Ensure expiration date is valid (typically 30+ days out)

### Implied volatility solver fails
- Reduce IV_SOLVER_TOLERANCE in config.py if bisection method is used
- Ensure market prices are within theoretical bounds

### Slow performance
- Increase data caching TTL in app.py (line ~115)
- Reduce number of expirations fetched (config.py)
- Run on a machine with more resources

## License

Open source for educational use.

## Support

For issues or feature requests, check the code comments or adjust configuration parameters in `config.py`.
