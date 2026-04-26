import math

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# yfinance needs crypto tickers formatted as BTC-USD, ETH-USD, etc.
# I chose to maintain this list so crypto symbols get normalized automatically without any extra user input
_CRYPTO_BASES = {
    "BTC","ETH","SOL","BNB","XRP","ADA","DOGE","DOT","AVAX","MATIC","LTC",
    "LINK","UNI","ATOM","XLM","ALGO","VET","FIL","TRX","ETC","XMR","EOS",
    "AAVE","COMP","MKR","SNX","SUSHI","YFI","CRV","BAL","NEAR","FTM","ONE",
    "SAND","MANA","AXS","ENJ","CHZ","HBAR","EGLD","THETA","KSM","RUNE","ZEC",
    "DASH","WAVES","ZIL","ICX","ONT","QTUM","BCH","BSV","IOTA","NEO",
    "SHIB","PEPE","FLOKI","WIF","BONK","JTO","PYTH","JUP","RAY","ORCA",
    "SUI","APT","SEI","INJ","TIA","DYM","STRK","ARB","OP","BASE",
}

# Appends -USD to crypto tickers so yfinance can find them
def _normalize_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    if s in _CRYPTO_BASES and not s.endswith("-USD"):
        return f"{s}-USD"
    return s


# Makes sure the price coming back from yfinance is a valid, usable number before it gets displayed
def _safe_price(raw) -> float | None:
    try:
        p = float(raw)
        return p if not math.isnan(p) and p > 0 else None
    except (TypeError, ValueError):
        return None


# Checks if a ticker is real before allowing it to be saved to the portfolio
# I chose not to cache this one so it always hits the live API for accuracy
def validate_ticker(symbol: str) -> bool:
    if not symbol:
        return False
    try:
        t = yf.Ticker(_normalize_symbol(symbol))
        return _safe_price(t.fast_info.last_price) is not None
    except Exception:
        return False


# Pulls the current price for a single ticker, cached for 60 seconds
@st.cache_data(ttl=60, show_spinner=False)
def get_current_price(symbol: str) -> float | None:
    try:
        t = yf.Ticker(_normalize_symbol(symbol))
        return _safe_price(t.fast_info.last_price)
    except Exception:
        return None


# Fetches prices for every ticker in the portfolio in one API call instead of one per ticker
# I chose to do it this way since it is much faster and reduces the number of network requests
@st.cache_data(ttl=60, show_spinner=False)
def get_batch_prices(symbols: tuple) -> dict:
    if not symbols:
        return {}
    norm_map = {s: _normalize_symbol(s) for s in symbols}
    norm_list = list(norm_map.values())
    try:
        raw = yf.download(norm_list, period="2d", progress=False, auto_adjust=True)
        if raw.empty:
            return {s: None for s in symbols}
        close = raw["Close"]
        # When only one ticker is downloaded yfinance returns a Series instead of a DataFrame
        if isinstance(close, pd.Series):
            close = close.to_frame(norm_list[0])
        result = {}
        for orig, norm in norm_map.items():
            try:
                price = float(close[norm].dropna().iloc[-1])
                result[orig] = price if price > 0 else None
            except Exception:
                result[orig] = None
        return result
    except Exception:
        return {s: None for s in symbols}


# Pulls historical OHLCV data for a single ticker, cached for 5 minutes
@st.cache_data(ttl=300, show_spinner=False)
def get_price_history(symbol: str, period: str = "1mo") -> pd.DataFrame | None:
    try:
        df = yf.download(_normalize_symbol(symbol), period=period, progress=False, auto_adjust=True)
        return df if not df.empty else None
    except Exception:
        return None


# Calculates 30-day annualized volatility for the volatility gauges
# Takes the standard deviation of daily returns over the last 30 trading days and annualizes it
@st.cache_data(ttl=300, show_spinner=False)
def get_volatility_30d(symbol: str) -> float:
    try:
        df = yf.download(_normalize_symbol(symbol), period="2mo", progress=False, auto_adjust=True)
        if df.empty or len(df) < 5:
            return 0.0
        close = df["Close"].squeeze()
        returns = close.pct_change().dropna()
        vol = float(returns.tail(30).std() * np.sqrt(252) * 100)
        return min(round(vol, 1), 100.0)
    except Exception:
        return 0.0


# Builds the correlation index line shown in the analytics graph
# Uses a 30-day rolling window and weights each ticker pair by its share of the total portfolio value
@st.cache_data(ttl=300, show_spinner=False)
def get_weighted_correlation_series(symbols: tuple, weights: tuple) -> "pd.Series | None":
    if len(symbols) < 2:
        return None
    try:
        norm_symbols = tuple(_normalize_symbol(s) for s in symbols)
        # Pulls ~15 months of history so even the 1 Year view has enough data to display
        start = (pd.Timestamp.today() - pd.Timedelta(days=460)).strftime("%Y-%m-%d")
        raw = yf.download(list(norm_symbols), start=start, progress=False, auto_adjust=True)
        if raw.empty:
            return None

        close = raw["Close"]
        if isinstance(close, pd.Series):
            close = close.to_frame(norm_symbols[0])

        # Only keeps tickers that actually returned data from yfinance
        available = [s for s in norm_symbols if s in close.columns]
        if len(available) < 2:
            return None

        close = close[available].dropna(how="all")
        returns = close.pct_change().dropna(how="all")

        # Normalizes weights to sum to 1 using only the tickers that returned data
        w = np.array([weights[norm_symbols.index(s)] for s in available], dtype=float)
        w /= w.sum()

        # Rolling 30-day correlation matrix across all trading days
        roll_corr = returns.rolling(30).corr()
        valid_dates = returns.index[29:]

        # Weight matrix for each ticker pair — diagonal zeroed out to exclude self-correlations
        w_mat = np.outer(w, w)
        np.fill_diagonal(w_mat, 0.0)

        # Computes the weighted average correlation for every date using NumPy instead of a Python loop
        # I chose to vectorize this because the Python loop version was noticeably slow with larger portfolios
        corr_us = roll_corr.loc[valid_dates].unstack(level=-1)
        vals_arr = np.zeros(len(valid_dates))
        den_arr  = np.zeros(len(valid_dates))
        n = len(available)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                try:
                    col = corr_us[(available[i], available[j])].values.astype(float)
                    valid = ~np.isnan(col)
                    wij = w_mat[i, j]
                    vals_arr += np.where(valid, wij * col, 0.0)
                    den_arr  += np.where(valid, wij,       0.0)
                except KeyError:
                    pass

        result = np.where(den_arr > 0, vals_arr / den_arr, np.nan)
        s = pd.Series(result, index=pd.DatetimeIndex(valid_dates)).dropna()
        return s if not s.empty else None
    except Exception:
        return None


# Pulls closing prices for multiple tickers at once, used for multi-asset charts
@st.cache_data(ttl=300, show_spinner=False)
def get_multi_close(symbols: tuple, period: str = "1mo") -> pd.DataFrame | None:
    if not symbols:
        return None
    try:
        norm = tuple(_normalize_symbol(s) for s in symbols)
        raw = yf.download(
            list(norm), period=period, progress=False, auto_adjust=True
        )
        close = raw["Close"] if len(norm) > 1 else raw[["Close"]].rename(
            columns={"Close": norm[0]}
        )
        return close if not close.empty else None
    except Exception:
        return None
