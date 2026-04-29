# Pulse — Portfolio Risk Intelligence Platform

Pulse is a real-time portfolio risk analytics dashboard built with Python and Streamlit. It allows users to track their holdings, monitor asset correlations, visualize 30-day volatility, and receive AI-generated diversification advice when portfolio risk is elevated.

## Features

### Portfolio Management
- Add holdings by entering a ticker symbol and the number of shares or tokens held
- Supports stocks, ETFs, and major cryptocurrencies (BTC, ETH, SOL, and more)
- Real-time prices fetched from Yahoo Finance and refreshed every 60 seconds
- Exposure percentage calculated from current market value (quantity × price)
- Inline portfolio editor for updating quantities or removing positions
- Default sort by highest exposure

### Risk Correlation Graph
- Plots a 30-day rolling weighted-average pairwise correlation index across all portfolio holdings
- Weights are proportional to each asset's current market value
- Timeframe selector: 7 Days, 30 Days, 90 Days, 1 Year
- Pink dotted threshold line at 0.70, which is the level at which a HIGH correlation alert is triggered
- Y-axis spans -1.0 to 1.0 to correctly display negatively correlated portfolios

### Volatility Gauges
- Displays 30-day annualised volatility for the two largest holdings by exposure
- Semi-circular gauge with colour gradient (deep purple → red) and a needle indicator
- Gauges update automatically with the 60-second data refresh

### Risk Alert Feed
- Below the 0.70 threshold: displays a green "Your portfolio is sufficiently diversified." card
- Above 0.70: displays a HIGH CORRELATION ALERT card with the top two correlated tickers
- Clicking the alert opens a modal with an AI-generated diversification recommendation (powered by Groq / Llama 3)

### Authentication & User Accounts
- Secure registration and login with password hashing (Werkzeug + bcrypt)
- Persistent sessions via browser cookies (30-day token)
- Per-user nickname (up to 12 characters) and role displayed in the top-right profile dropdown
- Profile picture upload with automatic square crop, resize to 256×256, and circular mask
- Password reset via email (Resend API)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / Server | Streamlit 1.55 |
| Charts | Plotly |
| Market Data | yfinance |
| AI Advice | Groq API (Llama 3.3 70B) |
| Database | PostgreSQL via Supabase |
| DB Driver | psycopg2 |
| Auth Persistence | extra-streamlit-components (CookieManager) |
| Password Security | Werkzeug / bcrypt |
| Image Processing | Pillow |
| Email | Resend API |
| Hosting | Streamlit Community Cloud |

## Project Structure

```
Pulse/
├── app.py              # Entry point: page config, global CSS, auth flow
├── dashboard.py        # Main dashboard UI and all rendering logic
├── db_ops.py           # All PostgreSQL database operations
├── market_data.py      # yfinance data-fetching utilities (prices, volatility, correlation)
├── llm_utils.py        # Groq API integration for AI diversification advice
├── cookie_utils.py     # Browser cookie manager initialisation
├── requirements.txt    # Python dependencies
└── .streamlit/
    └── secrets.toml    # API keys and database URL (not committed)
```

## Local Development Setup

**Prerequisites:** Python 3.10+

```bash
# 1. Clone the repository
git clone https://github.com/Dimitri-Lugo/Pulse.git
cd Pulse

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the secrets file
mkdir .streamlit
```

Create `.streamlit/secrets.toml` with the following keys:

```toml
DATABASE_URL  = "postgresql://..."   # Supabase connection string (transaction pooler)
GROQ_API_KEY  = "gsk_..."
RESEND_API_KEY = "re_..."
APP_URL       = "http://localhost:8501"
EMAIL_ADDRESS = "your-sender@email.com"
EMAIL_PASSWORD = "..."
```

```bash
# 5. Run the app
streamlit run app.py
```

## Deployment (Streamlit Community Cloud)

1. Push the repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set **Main file path** to `app.py`
4. Under **Advanced settings → Secrets**, paste all keys from `secrets.toml`
   - Use the Supabase **Transaction Pooler** URL (port 6543) — not the direct connection URL
5. Click **Deploy**

The database schema is initialised automatically on first run via `db_ops.init_db()`.

## Key Calculations

**Exposure %**
```
Market Value  = Quantity × Current Price
Exposure (%)  = (Asset Market Value / Total Portfolio Market Value) × 100
```

**30-Day Annualised Volatility**
```
Daily Returns = pct_change() on closing prices
Volatility    = std(last 30 returns) × √252 × 100   [capped at 100%]
```

**Weighted Correlation Index**
```
For each trading date, compute the 30-day rolling pairwise correlation matrix.
Weighted average = Σ(wᵢ × wⱼ × corrᵢⱼ) / Σ(wᵢ × wⱼ)   for i ≠ j
where wᵢ = Asset i Market Value / Total Portfolio Market Value
```
