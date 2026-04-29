"""
Federal Reserve Interest Rate Fetcher
Source: FRED (Federal Reserve Economic Data)

Series: DFF (Federal Funds Effective Rate)
Looking for: Downward trend (suggests rates were high, now easing)
"""

import os
import requests
from datetime import datetime, timedelta
from ..models.metrics import FedRateData


FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fed_rate() -> FedRateData:
    """
    Fetch Federal Funds Rate from FRED API.
    Analyzes trend over past 6 months.
    """
    api_key = os.getenv("FRED_API_KEY")

    if not api_key:
        return FedRateData(
            current=None,
            trend="unknown",
            error="FRED_API_KEY not set. Get one free at https://fred.stlouisfed.org/docs/api/api_key.html"
        )

    try:
        # Fetch last 6 months of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        params = {
            "series_id": "DFF",  # Federal Funds Effective Rate
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
            return FedRateData(current=None, trend="unknown", error="No observations returned")

        # Parse rates (filter out missing values marked as ".")
        rates = []
        for obs in observations:
            if obs["value"] != ".":
                rates.append({
                    "date": obs["date"],
                    "value": float(obs["value"])
                })

        if not rates:
            return FedRateData(current=None, trend="unknown", error="No valid rate data")

        current_rate = rates[0]["value"]  # Most recent (sorted desc)

        # Get rate from ~3 months ago and ~6 months ago for trend
        month_3_rate = rates[min(60, len(rates)-1)]["value"] if len(rates) > 60 else rates[-1]["value"]
        month_6_rate = rates[-1]["value"]

        # Determine trend
        if current_rate < month_3_rate < month_6_rate:
            trend = "downward"
            trend_description = "Rates declining (easing cycle)"
        elif current_rate > month_3_rate > month_6_rate:
            trend = "upward"
            trend_description = "Rates increasing (tightening cycle)"
        elif abs(current_rate - month_6_rate) < 0.25:
            trend = "stable"
            trend_description = "Rates relatively stable"
        else:
            trend = "mixed"
            trend_description = "Mixed signals in rate direction"

        return FedRateData(
            current=current_rate,
            month_3_ago=month_3_rate,
            month_6_ago=month_6_rate,
            trend=trend,
            trend_description=trend_description,
            change_6m=round(current_rate - month_6_rate, 2),
            timestamp=datetime.now().isoformat()
        )

    except requests.RequestException as e:
        return FedRateData(current=None, trend="unknown", error=f"API request failed: {str(e)}")
    except Exception as e:
        return FedRateData(current=None, trend="unknown", error=str(e))
