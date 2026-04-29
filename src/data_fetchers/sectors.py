"""
Sector Performance Fetcher
Source: Yahoo Finance (Sector ETFs)

Tracks major sector ETFs to identify leading sectors:
- XLK: Technology
- XLF: Financials
- XLE: Energy
- XLV: Healthcare
- XLI: Industrials
- XLC: Communication Services
- XLY: Consumer Discretionary
- XLP: Consumer Staples
- XLB: Materials
- XLRE: Real Estate
- XLU: Utilities
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


def fetch_sector_performance() -> SectorData:
    """
    Fetch performance data for all major sector ETFs.
    Returns sectors ranked by various timeframes.
    """
    try:
        sectors: List[SectorPerformance] = []

        for ticker, name in SECTOR_ETFS.items():
            try:
                etf = yf.Ticker(ticker)
                hist = etf.history(period="3mo")

                if hist.empty:
                    continue

                current = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current

                # Calculate returns
                day_return = ((current - prev_close) / prev_close) * 100

                # Week return (5 trading days)
                week_price = hist['Close'].iloc[-6] if len(hist) > 5 else hist['Close'].iloc[0]
                week_return = ((current - week_price) / week_price) * 100

                # Month return (~21 trading days)
                month_price = hist['Close'].iloc[-22] if len(hist) > 21 else hist['Close'].iloc[0]
                month_return = ((current - month_price) / month_price) * 100

                # 3-month return
                three_month_price = hist['Close'].iloc[0]
                three_month_return = ((current - three_month_price) / three_month_price) * 100

                # Volume trend (average last 5 days vs prior 20 days)
                recent_vol = hist['Volume'].iloc[-5:].mean()
                prior_vol = hist['Volume'].iloc[-25:-5].mean() if len(hist) > 25 else hist['Volume'].mean()
                volume_trend = ((recent_vol - prior_vol) / prior_vol) * 100 if prior_vol > 0 else 0

                sectors.append(SectorPerformance(
                    ticker=ticker,
                    name=name,
                    current_price=round(current, 2),
                    day_return=round(day_return, 2),
                    week_return=round(week_return, 2),
                    month_return=round(month_return, 2),
                    three_month_return=round(three_month_return, 2),
                    volume_trend_pct=round(volume_trend, 2)
                ))

            except Exception as e:
                # Skip individual sector on error
                continue

        if not sectors:
            return SectorData(
                sectors=[],
                leading_sectors=[],
                lagging_sectors=[],
                error="Failed to fetch any sector data"
            )

        # Sort by month return to find leaders/laggers
        sorted_by_month = sorted(sectors, key=lambda x: x.month_return, reverse=True)

        # Top 3 leading sectors
        leading = sorted_by_month[:3]
        lagging = sorted_by_month[-3:]

        # Identify sectors with high volume (attention indicator)
        high_attention = [s for s in sectors if s.volume_trend_pct > 20]
        high_attention = sorted(high_attention, key=lambda x: x.volume_trend_pct, reverse=True)

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
