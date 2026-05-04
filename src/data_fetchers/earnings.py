"""
Sector Earnings Data Fetcher

Fetches earnings-related metrics for leading sectors.
Uses major companies in each sector as proxies.

Note: Free APIs have limitations. For production, consider:
- Finnhub (free tier)
- Alpha Vantage (free tier)
- Yahoo Finance (yfinance)
"""

import yfinance as yf
from datetime import datetime
from typing import List, Dict
from ..models.metrics import EarningsData, CompanyEarnings, QuarterlySnapshot
from ..thresholds import EARNINGS_HEALTHY_GROWTH_MIN


# Representative companies for each sector (large caps)
SECTOR_REPRESENTATIVES = {
    "Technology": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    "Financials": ["JPM", "BAC", "WFC", "GS", "MS"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "Healthcare": ["UNH", "JNJ", "PFE", "ABBV", "MRK"],
    "Industrials": ["CAT", "HON", "UNP", "GE", "RTX"],
    "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "T"],
    "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
    "Consumer Staples": ["PG", "KO", "PEP", "WMT", "COST"],
    "Materials": ["LIN", "APD", "SHW", "FCX", "NEM"],
    "Real Estate": ["PLD", "AMT", "EQIX", "PSA", "SPG"],
    "Utilities": ["NEE", "DUK", "SO", "D", "AEP"]
}


def fetch_sector_earnings(sectors: List[str] = None) -> EarningsData:
    if sectors is None:
        sectors = list(SECTOR_REPRESENTATIVES.keys())

    try:
        all_earnings: List[CompanyEarnings] = []
        sector_summaries: Dict[str, dict] = {}

        for sector in sectors:
            if sector not in SECTOR_REPRESENTATIVES:
                continue

            tickers = SECTOR_REPRESENTATIVES[sector]
            sector_earnings = []

            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info

                    # Quarterly revenue + net income (last 4 quarters)
                    quarterly_data = []
                    try:
                        qstmt = stock.quarterly_income_stmt
                        if qstmt is not None and not qstmt.empty:
                            for col in list(qstmt.columns)[:4]:
                                rev = qstmt.loc["Total Revenue", col] if "Total Revenue" in qstmt.index else None
                                net = qstmt.loc["Net Income", col] if "Net Income" in qstmt.index else None
                                import math
                                quarterly_data.append(QuarterlySnapshot(
                                    quarter=f"Q{(col.month - 1) // 3 + 1} {col.year}",
                                    revenue_b=round(float(rev) / 1e9, 2) if rev is not None and not math.isnan(float(rev)) else None,
                                    net_income_b=round(float(net) / 1e9, 2) if net is not None and not math.isnan(float(net)) else None,
                                ))
                    except Exception:
                        pass

                    # Get earnings data
                    earnings = CompanyEarnings(
                        ticker=ticker,
                        sector=sector,
                        company_name=info.get("shortName", ticker),
                        market_cap_b=round(info.get("marketCap", 0) / 1e9, 2),
                        pe_ratio=info.get("forwardPE") or info.get("trailingPE"),
                        eps_trailing=info.get("trailingEps"),
                        eps_forward=info.get("forwardEps"),
                        revenue_growth=info.get("revenueGrowth"),
                        earnings_growth=info.get("earningsGrowth"),
                        profit_margin=info.get("profitMargins"),
                        analyst_rating=info.get("recommendationKey"),
                        target_price=info.get("targetMeanPrice"),
                        current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
                        prev_close=info.get("previousClose") or info.get("regularMarketPreviousClose"),
                        open_price=info.get("open") or info.get("regularMarketOpen"),
                        quarterly_data=quarterly_data,
                    )

                    sector_earnings.append(earnings)
                    all_earnings.append(earnings)

                except Exception:
                    continue

            # Summarize sector
            if sector_earnings:
                avg_growth = sum(
                    e.earnings_growth or 0 for e in sector_earnings
                ) / len(sector_earnings)

                positive_growth = sum(
                    1 for e in sector_earnings
                    if e.earnings_growth and e.earnings_growth > 0
                )

                sector_summaries[sector] = {
                    "companies_analyzed": len(sector_earnings),
                    "avg_earnings_growth": round(avg_growth * 100, 2) if avg_growth else None,
                    "positive_growth_count": positive_growth,
                    "companies": [e.ticker for e in sector_earnings]
                }

        # Determine overall health
        healthy_sectors = [
            s for s, data in sector_summaries.items()
            if data.get("avg_earnings_growth", 0) and data["avg_earnings_growth"] > EARNINGS_HEALTHY_GROWTH_MIN
        ]

        return EarningsData(
            companies=all_earnings,
            sector_summaries=sector_summaries,
            healthy_sectors=healthy_sectors,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        return EarningsData(
            companies=[],
            sector_summaries={},
            healthy_sectors=[],
            error=str(e)
        )
