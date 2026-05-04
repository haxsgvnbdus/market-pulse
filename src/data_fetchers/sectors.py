"""
Sector Performance Fetcher
Source: Yahoo Finance (Sector ETFs)
"""

import yfinance as yf
from datetime import datetime
from typing import List
from ..models.metrics import SectorData, SectorPerformance


SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLC": "Communication Services",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLU": "Utilities"
}


def _pct_return(current: float, past: float) -> float:
    return round(((current - past) / past) * 100, 2) if past else 0.0


def _price_n_ago(hist, n: int) -> float:
    """Return closing price n trading days ago."""
    idx = -(n + 1)
    if abs(idx) <= len(hist):
        return float(hist['Close'].iloc[idx])
    return float(hist['Close'].iloc[0])


def fetch_sector_performance() -> SectorData:
    try:
        sectors: List[SectorPerformance] = []

        for ticker, name in SECTOR_ETFS.items():
            try:
                etf = yf.Ticker(ticker)
                hist = etf.history(period="2y")

                if hist.empty:
                    continue

                current = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current

                # Volume trend: avg last 5 days vs prior 20 days
                recent_vol = hist['Volume'].iloc[-5:].mean()
                prior_vol = hist['Volume'].iloc[-25:-5].mean() if len(hist) > 25 else hist['Volume'].mean()
                volume_trend = ((recent_vol - prior_vol) / prior_vol) * 100 if prior_vol > 0 else 0

                sectors.append(SectorPerformance(
                    ticker=ticker,
                    name=name,
                    current_price=round(current, 2),
                    day_return=_pct_return(current, prev_close),
                    day_5_return=_pct_return(current, _price_n_ago(hist, 5)),
                    day_20_return=_pct_return(current, _price_n_ago(hist, 20)),
                    day_60_return=_pct_return(current, _price_n_ago(hist, 60)),
                    day_90_return=_pct_return(current, _price_n_ago(hist, 90)),
                    day_180_return=_pct_return(current, _price_n_ago(hist, 180)),
                    year_return=_pct_return(current, _price_n_ago(hist, 252)),
                    volume_trend_pct=round(volume_trend, 2)
                ))

            except Exception:
                continue

        if not sectors:
            return SectorData(
                sectors=[],
                leading_sectors=[],
                lagging_sectors=[],
                error="Failed to fetch any sector data"
            )

        sorted_by_month = sorted(sectors, key=lambda x: x.day_20_return, reverse=True)

        leading = sorted_by_month[:3]
        lagging = sorted_by_month[-3:]

        high_attention = sorted(
            [s for s in sectors if s.volume_trend_pct > 20],
            key=lambda x: x.volume_trend_pct, reverse=True
        )

        return SectorData(
            sectors=sectors,
            leading_sectors=[s.name for s in leading],
            lagging_sectors=[s.name for s in lagging],
            high_attention_sectors=[s.name for s in high_attention[:3]],
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        return SectorData(
            sectors=[],
            leading_sectors=[],
            lagging_sectors=[],
            error=str(e)
        )
