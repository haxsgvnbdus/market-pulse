"""
Data models for market metrics.
Using dataclasses for clean, type-hinted structures.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class VIXData:
    """VIX (Fear Index) data."""
    current: Optional[float] = None
    previous_close: Optional[float] = None
    week_ago: Optional[float] = None
    month_high: Optional[float] = None
    month_low: Optional[float] = None
    fear_level: str = "unknown"  # extreme_fear, high_fear, elevated, moderate, low_fear
    timestamp: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_buy_signal(self) -> bool:
        """VIX > 30 is a potential buy signal (extreme fear)."""
        return self.current is not None and self.current > 30

    def to_dict(self) -> dict:
        return {
            "current": self.current,
            "previous_close": self.previous_close,
            "week_ago": self.week_ago,
            "month_high": self.month_high,
            "month_low": self.month_low,
            "fear_level": self.fear_level,
            "is_buy_signal": self.is_buy_signal,
            "timestamp": self.timestamp,
            "error": self.error
        }


@dataclass
class FedRateData:
    """Federal Reserve interest rate data."""
    current: Optional[float] = None
    month_3_ago: Optional[float] = None
    month_6_ago: Optional[float] = None
    trend: str = "unknown"  # downward, upward, stable, mixed
    trend_description: Optional[str] = None
    change_6m: Optional[float] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_buy_signal(self) -> bool:
        """Downward trend in rates is a buy signal."""
        return self.trend == "downward"

    def to_dict(self) -> dict:
        return {
            "current": self.current,
            "month_3_ago": self.month_3_ago,
            "month_6_ago": self.month_6_ago,
            "trend": self.trend,
            "trend_description": self.trend_description,
            "change_6m": self.change_6m,
            "is_buy_signal": self.is_buy_signal,
            "timestamp": self.timestamp,
            "error": self.error
        }


@dataclass
class MarginDebtData:
    """FINRA Margin Debt data."""
    current: Optional[float] = None
    current_billions: Optional[float] = None
    previous_quarter: Optional[float] = None
    year_ago: Optional[float] = None
    quarterly_change_pct: Optional[float] = None
    yearly_change_pct: Optional[float] = None
    trend: str = "unknown"  # decreasing, slightly_decreasing, stable, increasing
    trend_description: Optional[str] = None
    data_date: Optional[str] = None
    note: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_buy_signal(self) -> bool:
        """Decreasing margin debt is a buy signal (deleveraging)."""
        return self.trend in ["decreasing", "slightly_decreasing"]

    def to_dict(self) -> dict:
        return {
            "current_billions": self.current_billions,
            "quarterly_change_pct": self.quarterly_change_pct,
            "yearly_change_pct": self.yearly_change_pct,
            "trend": self.trend,
            "trend_description": self.trend_description,
            "is_buy_signal": self.is_buy_signal,
            "data_date": self.data_date,
            "note": self.note,
            "error": self.error
        }


@dataclass
class SectorPerformance:
    """Individual sector performance data."""
    ticker: str
    name: str
    current_price: float
    day_return: float
    week_return: float
    month_return: float
    three_month_return: float
    volume_trend_pct: float  # Positive = increasing attention

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "current_price": self.current_price,
            "day_return": self.day_return,
            "week_return": self.week_return,
            "month_return": self.month_return,
            "three_month_return": self.three_month_return,
            "volume_trend_pct": self.volume_trend_pct
        }


@dataclass
class SectorData:
    """Aggregated sector performance data."""
    sectors: List[SectorPerformance] = field(default_factory=list)
    leading_sectors: List[str] = field(default_factory=list)
    lagging_sectors: List[str] = field(default_factory=list)
    high_attention_sectors: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    error: Optional[str] = None

    @property
    def has_clear_leaders(self) -> bool:
        """Check if there are clear leading sectors."""
        if not self.sectors or len(self.sectors) < 3:
            return False
        sorted_sectors = sorted(self.sectors, key=lambda x: x.month_return, reverse=True)
        # Clear leader if top sector outperforms 3rd by >5%
        return (sorted_sectors[0].month_return - sorted_sectors[2].month_return) > 5

    def to_dict(self) -> dict:
        return {
            "sectors": [s.to_dict() for s in self.sectors],
            "leading_sectors": self.leading_sectors,
            "lagging_sectors": self.lagging_sectors,
            "high_attention_sectors": self.high_attention_sectors,
            "has_clear_leaders": self.has_clear_leaders,
            "timestamp": self.timestamp,
            "error": self.error
        }


@dataclass
class CompanyEarnings:
    """Individual company earnings data."""
    ticker: str
    sector: str
    company_name: str
    market_cap_b: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps_trailing: Optional[float] = None
    eps_forward: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    profit_margin: Optional[float] = None
    analyst_rating: Optional[str] = None
    target_price: Optional[float] = None
    current_price: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "sector": self.sector,
            "company_name": self.company_name,
            "market_cap_b": self.market_cap_b,
            "pe_ratio": self.pe_ratio,
            "eps_trailing": self.eps_trailing,
            "eps_forward": self.eps_forward,
            "revenue_growth": f"{self.revenue_growth*100:.1f}%" if self.revenue_growth else None,
            "earnings_growth": f"{self.earnings_growth*100:.1f}%" if self.earnings_growth else None,
            "profit_margin": f"{self.profit_margin*100:.1f}%" if self.profit_margin else None,
            "analyst_rating": self.analyst_rating,
            "target_price": self.target_price,
            "current_price": self.current_price
        }


@dataclass
class EarningsData:
    """Aggregated earnings data for sectors."""
    companies: List[CompanyEarnings] = field(default_factory=list)
    sector_summaries: Dict[str, dict] = field(default_factory=dict)
    healthy_sectors: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    error: Optional[str] = None

    @property
    def has_strong_earnings(self) -> bool:
        """Check if leading sectors show strong earnings growth."""
        return len(self.healthy_sectors) >= 2

    def to_dict(self) -> dict:
        return {
            "companies": [c.to_dict() for c in self.companies],
            "sector_summaries": self.sector_summaries,
            "healthy_sectors": self.healthy_sectors,
            "has_strong_earnings": self.has_strong_earnings,
            "timestamp": self.timestamp,
            "error": self.error
        }


@dataclass
class MarketPulseReport:
    """Complete market pulse report with all metrics."""
    vix: VIXData
    fed_rate: FedRateData
    margin_debt: MarginDebtData
    sectors: SectorData
    earnings: EarningsData
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ai_analysis: Optional[str] = None

    @property
    def buy_signals_count(self) -> int:
        """Count how many of the 5 metrics show buy signals."""
        signals = 0
        if self.vix.is_buy_signal:
            signals += 1
        if self.fed_rate.is_buy_signal:
            signals += 1
        if self.margin_debt.is_buy_signal:
            signals += 1
        if self.sectors.has_clear_leaders:
            signals += 1
        if self.earnings.has_strong_earnings:
            signals += 1
        return signals

    @property
    def signal_strength(self) -> str:
        """Overall signal strength based on buy signals count."""
        count = self.buy_signals_count
        if count >= 4:
            return "STRONG_BUY"
        elif count >= 3:
            return "MODERATE_BUY"
        elif count >= 2:
            return "WEAK_BUY"
        else:
            return "NEUTRAL"

    def to_dict(self) -> dict:
        return {
            "vix": self.vix.to_dict(),
            "fed_rate": self.fed_rate.to_dict(),
            "margin_debt": self.margin_debt.to_dict(),
            "sectors": self.sectors.to_dict(),
            "earnings": self.earnings.to_dict(),
            "buy_signals_count": self.buy_signals_count,
            "signal_strength": self.signal_strength,
            "generated_at": self.generated_at,
            "ai_analysis": self.ai_analysis
        }
