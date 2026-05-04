"""
VIX (Volatility Index) Fetcher
Source: Yahoo Finance (^VIX)
"""

import yfinance as yf
from datetime import datetime
from ..models.metrics import VIXData
from ..thresholds import VIX_BUY_SIGNAL, VIX_HIGH_FEAR, VIX_ELEVATED, VIX_MODERATE


def _price_n_ago(hist, n: int) -> float:
    """Return closing price n trading days ago (n=1 is previous close)."""
    idx = -(n + 1)
    if abs(idx) <= len(hist):
        return round(float(hist['Close'].iloc[idx]), 2)
    return round(float(hist['Close'].iloc[0]), 2)


def fetch_vix() -> VIXData:
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="2y")

        if hist.empty:
            return VIXData(fear_level="unknown", error="No data available")

        current = round(float(hist['Close'].iloc[-1]), 2)
        previous_close = round(float(hist['Close'].iloc[-2]), 2) if len(hist) > 1 else current

        if current > VIX_BUY_SIGNAL:
            fear_level = "extreme_fear"
        elif current > VIX_HIGH_FEAR:
            fear_level = "high_fear"
        elif current > VIX_ELEVATED:
            fear_level = "elevated"
        elif current > VIX_MODERATE:
            fear_level = "moderate"
        else:
            fear_level = "low_fear"

        return VIXData(
            current=current,
            previous_close=previous_close,
            day_5_ago=_price_n_ago(hist, 5),
            day_20_ago=_price_n_ago(hist, 20),
            day_60_ago=_price_n_ago(hist, 60),
            day_90_ago=_price_n_ago(hist, 90),
            day_180_ago=_price_n_ago(hist, 180),
            year_ago=_price_n_ago(hist, 252),
            month_high=round(float(hist['Close'].iloc[-21:].max()), 2),
            month_low=round(float(hist['Close'].iloc[-21:].min()), 2),
            fear_level=fear_level,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        return VIXData(fear_level="unknown", error=str(e))
