"""
VIX (Volatility Index) Fetcher
Source: Yahoo Finance (^VIX)

VIX > 30 indicates high fear/volatility in the market
VIX 20-30 is elevated concern
VIX < 20 is relatively calm
"""

import yfinance as yf
from datetime import datetime, timedelta
from ..models.metrics import VIXData


def fetch_vix() -> VIXData:
    """
    Fetch current VIX value and recent history.
    Returns VIXData with current value, trend, and fear level assessment.
    """
    try:
        vix = yf.Ticker("^VIX")

        # Get current data
        hist = vix.history(period="1mo")

        if hist.empty:
            return VIXData(
                current=None,
                previous_close=None,
                week_ago=None,
                month_high=None,
                month_low=None,
                fear_level="unknown",
                error="No data available"
            )

        current = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current

        # Get week ago value (5 trading days)
        week_ago = hist['Close'].iloc[-6] if len(hist) > 5 else hist['Close'].iloc[0]

        month_high = hist['Close'].max()
        month_low = hist['Close'].min()

        # Determine fear level
        if current > 30:
            fear_level = "extreme_fear"
        elif current > 25:
            fear_level = "high_fear"
        elif current > 20:
            fear_level = "elevated"
        elif current > 15:
            fear_level = "moderate"
        else:
            fear_level = "low_fear"

        return VIXData(
            current=round(current, 2),
            previous_close=round(previous_close, 2),
            week_ago=round(week_ago, 2),
            month_high=round(month_high, 2),
            month_low=round(month_low, 2),
            fear_level=fear_level,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        return VIXData(
            current=None,
            fear_level="unknown",
            error=str(e)
        )
