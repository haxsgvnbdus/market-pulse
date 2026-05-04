"""
Federal Reserve Interest Rate Fetcher
Source: FRED (Federal Reserve Economic Data)

Series: DFF (Federal Funds Effective Rate)
"""

import os
import requests
from datetime import datetime, timedelta
from ..models.metrics import FedRateData
from ..thresholds import FED_STABLE_BAND


FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fed_rate() -> FedRateData:
    api_key = os.getenv("FRED_API_KEY")

    if not api_key:
        return FedRateData(
            trend="unknown",
            error="FRED_API_KEY not set. Get one free at https://fred.stlouisfed.org/docs/api/api_key.html"
        )

    try:
        end_date = datetime.now()
        # ~550 calendar days covers 252+ business days (1 year of trading data)
        start_date = end_date - timedelta(days=550)

        params = {
            "series_id": "DFF",
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
            return FedRateData(trend="unknown", error="No observations returned")

        rates = [
            float(obs["value"])
            for obs in observations
            if obs["value"] != "."
        ]

        if not rates:
            return FedRateData(trend="unknown", error="No valid rate data")

        def rate_n_ago(n: int) -> float:
            return rates[min(n, len(rates) - 1)]

        current = rates[0]
        day_60 = rate_n_ago(60)
        day_180 = rate_n_ago(180)

        if current < day_60 < day_180:
            trend = "downward"
            trend_description = "Rates declining (easing cycle)"
        elif current > day_60 > day_180:
            trend = "upward"
            trend_description = "Rates increasing (tightening cycle)"
        elif abs(current - day_180) < FED_STABLE_BAND:
            trend = "stable"
            trend_description = "Rates relatively stable"
        else:
            trend = "mixed"
            trend_description = "Mixed signals in rate direction"

        return FedRateData(
            current=current,
            day_5_ago=rate_n_ago(5),
            day_20_ago=rate_n_ago(20),
            day_60_ago=day_60,
            day_90_ago=rate_n_ago(90),
            day_180_ago=day_180,
            year_ago=rate_n_ago(252),
            trend=trend,
            trend_description=trend_description,
            change_180d=round(current - day_180, 2),
            timestamp=datetime.now().isoformat()
        )

    except requests.RequestException as e:
        return FedRateData(trend="unknown", error=f"API request failed: {str(e)}")
    except Exception as e:
        return FedRateData(trend="unknown", error=str(e))
