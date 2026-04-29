from .vix import fetch_vix
from .fed_rate import fetch_fed_rate
from .margin_debt import fetch_margin_debt
from .sectors import fetch_sector_performance
from .earnings import fetch_sector_earnings

__all__ = [
    'fetch_vix',
    'fetch_fed_rate',
    'fetch_margin_debt',
    'fetch_sector_performance',
    'fetch_sector_earnings'
]
