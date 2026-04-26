"""
market_data.py — yfinance data-fetching utilities for Pulse.

Architecture note
-----------------
All network calls are isolated here so the rest of the codebase never imports
yfinance directly.  Each function is either cached with a TTL (safe for repeated
dashboard renders) or uncached (used only on explicit user actions such as
ticker submission).

Current public surface
  validate_ticker(symbol)          → bool
  get_current_price(symbol)        → float | None
  get_price_history(symbol, period)→ pd.DataFrame | None
  get_multi_close(symbols, period) → pd.DataFrame | None   (multi-ticker close)
"""

import math

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Known crypto base symbols that yfinance requires as SYMBOL-USD
_CRYPTO_BASES = {
    "BTC","ETH","SOL","BNB","XRP","ADA","DOGE","DOT","AVAX","MATIC","LTC",
    "LINK","UNI","ATOM","XLM","ALGO","VET","FIL","TRX","ETC","XMR","EOS",
    "AAVE","COMP","MKR","SNX","SUSHI","YFI","CRV","BAL","NEAR","FTM","ONE",
    "SAND","MANA","AXS","ENJ","CHZ","HBAR","EGLD","THETA","KSM","RUNE","ZEC",
    "DASH","WAVES","ZIL","ICX","ONT","QTUM","BCH","BSV","IOTA","NEO",
    "SHIB","PEPE","FLOKI","WIF","BONK","JTO","PYTH","JUP","RAY","ORCA",
    "SUI","APT","SEI","INJ","TIA","DYM","STRK","ARB","OP","BASE",
}

def _normalize_symbol(symbol: str) -> str:
    """Auto-append -USD for known crypto base tickers so yfinance resolves them."""
    s = symbol.upper().strip()
    if s in _CRYPTO_BASES and not s.endswith("-USD"):
        return f"{s}-USD"
    return s


def _safe_price(raw) -> float | None:
    """Convert a raw fast_info price to float, returning None on NaN / zero."""
    try:
        p = float(raw)
        return p if not math.isnan(p) and p > 0 else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Validation  (intentionally NOT cached — always fresh on user action)
# ---------------------------------------------------------------------------

def validate_ticker(symbol: str) -> bool:
    """Return True only if *symbol* resolves to a real, actively-traded security.

    Uses fast_info.last_price which is a lightweight one-shot HTTP call.
    Returns False for empty strings, unknown symbols, or network errors.
    """
    if not symbol:
        return False
    try:
        t = yf.Ticker(_normalize_symbol(symbol))
        return _safe_price(t.fast_info.last_price) is not None
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Single-ticker price  (cached 60 s — suitable for dashboard renders)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def get_current_price(symbol: str) -> float | None:
    """Return the latest trade price for *symbol*, or None on failure.

    Cached for 60 seconds so repeated renders don't hammer the API.
    """
    try:
        t = yf.Ticker(_normalize_symbol(symbol))
        return _safe_price(t.fast_info.last_price)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Historical OHLCV  (cached 5 min — used for charts / volatility)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def get_price_history(symbol: str, period: str = "1mo") -> pd.DataFrame | None:
    """Fetch adjusted OHLCV history for a single *symbol*.

    Parameters
    ----------
    symbol : str
        Ticker symbol, e.g. "AAPL".
    period : str
        yfinance period string: "7d", "1mo", "3mo", "1y", etc.

    Returns
    -------
    pd.DataFrame with DatetimeIndex and columns [Open, High, Low, Close, Volume],
    or None on failure / empty result.
    """
    try:
        df = yf.download(_normalize_symbol(symbol), period=period, progress=False, auto_adjust=True)
        return df if not df.empty else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Multi-ticker closing prices  (cached 5 min — used for correlation charts)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def get_volatility_30d(symbol: str) -> float:
    """Return the 30-trading-day annualised volatility as a 0–100 capped percentage.

    Fetches ~2 months of daily close prices, computes daily % returns, takes the
    std of the last 30 trading days, and annualises by sqrt(252).
    Returns 0.0 on any failure.
    """
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


@st.cache_data(ttl=300, show_spinner=False)
def get_weighted_correlation_series(symbols: tuple, weights: tuple) -> "pd.Series | None":
    """30-day rolling weighted-average pairwise correlation for portfolio tickers.

    Parameters
    ----------
    symbols : tuple[str, ...]
        Ticker symbols — must be a tuple so Streamlit can hash for caching.
    weights : tuple[float, ...]
        Portfolio weight for each symbol (fractions that sum to 1).

    Returns
    -------
    pd.Series indexed by date with values in [-1, 1], or None on any failure /
    insufficient data.
    """
    if len(symbols) < 2:
        return None
    try:
        norm_symbols = tuple(_normalize_symbol(s) for s in symbols)
        start = (pd.Timestamp.today() - pd.Timedelta(days=460)).strftime("%Y-%m-%d")
        raw = yf.download(list(norm_symbols), start=start, progress=False, auto_adjust=True)
        if raw.empty:
            return None

        close = raw["Close"]
        if isinstance(close, pd.Series):
            close = close.to_frame(norm_symbols[0])

        available = [s for s in norm_symbols if s in close.columns]
        if len(available) < 2:
            return None

        close = close[available].dropna(how="all")
        returns = close.pct_change().dropna(how="all")

        # Weights aligned to the tickers that actually have data
        w = np.array([weights[norm_symbols.index(s)] for s in available], dtype=float)
        w /= w.sum()

        # 30-day rolling correlation matrix (pandas MultiIndex result)
        roll_corr = returns.rolling(30).corr()
        valid_dates = returns.index[29:]

        vals = []
        for date in valid_dates:
            try:
                mat = roll_corr.loc[date].reindex(index=available, columns=available).values
                num, den = 0.0, 0.0
                for i in range(len(available)):
                    for j in range(len(available)):
                        if i != j and not np.isnan(mat[i, j]):
                            num += w[i] * w[j] * mat[i, j]
                            den += w[i] * w[j]
                vals.append(num / den if den > 0 else np.nan)
            except Exception:
                vals.append(np.nan)

        s = pd.Series(vals, index=pd.DatetimeIndex(valid_dates)).dropna()
        return s if not s.empty else None
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def get_multi_close(symbols: tuple, period: str = "1mo") -> pd.DataFrame | None:
    """Fetch daily closing prices for multiple tickers in one API call.

    Parameters
    ----------
    symbols : tuple[str, ...]
        Ticker symbols.  A tuple (not list) is required so Streamlit can hash
        the argument for cache keying.
    period : str
        yfinance period string.

    Returns
    -------
    pd.DataFrame with DatetimeIndex and one column per symbol, or None.
    """
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
