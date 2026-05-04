"""
FINRA Margin Debt Fetcher

Source: FINRA publishes margin statistics monthly
https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics

Note: FINRA data is released monthly with ~1 month lag.
This module fetches from FRED which tracks FINRA margin debt.
Series: BOGZ1FL663067003Q (Margin debt, quarterly)

Alternative: Scrape FINRA directly for monthly data
"""

import os
import requests
from datetime import datetime, timedelta
from ..models.metrics import MarginDebtData
from ..thresholds import MARGIN_DECREASING_QTR, MARGIN_INCREASING_QTR


FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_margin_debt() -> MarginDebtData:
    """
    Fetch margin debt statistics.
    Looking for: Decreasing margin debt (deleveraging = potential bottom signal)
    """
    api_key = os.getenv("FRED_API_KEY")

    if not api_key:
        return MarginDebtData(
            current=None,
            trend="unknown",
            error="FRED_API_KEY not set"
        )

    try:
        # BOGZ1FL663067003Q is margin accounts debt
        # Alternative series if needed: Look up FINRA margin statistics
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years for trend

        params = {
            "series_id": "BOGZ1FL663067003Q",
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start_date.strftime("%Y-%m-%d"),
            "observation_end": end_date.strftime("%Y-%m-%d"),
            "sort_order": "desc"
        }

        response = requests.get(FRED_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        observations = data.get("observations", [])

        if not observations:
            # Try alternative approach - use placeholder with note
            return MarginDebtData(
                current=None,
                trend="unknown",
                note="FRED series unavailable. Check FINRA directly: https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics",
                error="No data from FRED series"
            )

        # Parse values
        values = []
        for obs in observations:
            if obs["value"] != ".":
                values.append({
                    "date": obs["date"],
                    "value": float(obs["value"])
                })

        if len(values) < 2:
            return MarginDebtData(current=None, trend="unknown", error="Insufficient data points")

        current = values[0]["value"]
        previous_quarter = values[1]["value"] if len(values) > 1 else None
        two_quarters_ago = values[2]["value"] if len(values) > 2 else None
        three_quarters_ago = values[3]["value"] if len(values) > 3 else None
        year_ago = values[4]["value"] if len(values) > 4 else None
        two_years_ago = values[8]["value"] if len(values) > 8 else None

        quarterly_change = ((current - previous_quarter) / previous_quarter) * 100 if previous_quarter else 0
        yearly_change = ((current - year_ago) / year_ago) * 100 if year_ago else 0

        if quarterly_change < MARGIN_DECREASING_QTR and yearly_change < 0:
            trend = "decreasing"
            trend_description = "Significant deleveraging occurring"
        elif quarterly_change < 0:
            trend = "slightly_decreasing"
            trend_description = "Mild deleveraging"
        elif quarterly_change > MARGIN_INCREASING_QTR:
            trend = "increasing"
            trend_description = "Leverage increasing (risk-on behavior)"
        else:
            trend = "stable"
            trend_description = "Margin debt relatively stable"

        # Convert to billions for readability
        current_billions = round(current / 1000, 2)

        return MarginDebtData(
            current=current,
            current_billions=current_billions,
            previous_quarter=previous_quarter,
            two_quarters_ago=two_quarters_ago,
            three_quarters_ago=three_quarters_ago,
            year_ago=year_ago,
            two_years_ago=two_years_ago,
            quarterly_change_pct=round(quarterly_change, 2),
            yearly_change_pct=round(yearly_change, 2),
            trend=trend,
            trend_description=trend_description,
            data_date=values[0]["date"],
            note="Data is quarterly with ~2 month lag. For monthly data, check FINRA directly.",
            timestamp=datetime.now().isoformat()
        )

    except requests.RequestException as e:
        return MarginDebtData(current=None, trend="unknown", error=f"API request failed: {str(e)}")
    except Exception as e:
        return MarginDebtData(current=None, trend="unknown", error=str(e))


def get_finra_margin_url() -> str:
    """Return URL to FINRA margin statistics page for manual checking."""
    return "https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics"
