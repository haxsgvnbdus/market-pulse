#!/usr/bin/env python3
"""
Market Pulse - Stock Market Buying Opportunity Tracker

Tracks 5 key metrics:
1. VIX > 30 (fear indicator)
2. Fed rate downward trend
3. Margin debt decreasing
4. Clear leading sectors
5. Strong earnings in leading sectors

Usage:
    python main.py              # Run once, print to console
    python main.py --email      # Run once, send email
    python main.py --schedule   # Run on schedule (9:30 AM, 4:00 PM ET)
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.data_fetchers import (
    fetch_vix,
    fetch_fed_rate,
    fetch_margin_debt,
    fetch_sector_performance,
    fetch_sector_earnings
)
from src.models.metrics import MarketPulseReport
from src.analyzer import get_ai_analysis
from src.emailer import send_email_report


def fetch_all_data() -> MarketPulseReport:
    """Fetch all market data and compile report."""
    print("Fetching market data...")

    print("  - VIX...")
    vix = fetch_vix()

    print("  - Fed Rate...")
    fed_rate = fetch_fed_rate()

    print("  - Margin Debt...")
    margin_debt = fetch_margin_debt()

    print("  - Sector Performance...")
    sectors = fetch_sector_performance()

    # Fetch earnings for leading sectors
    leading = sectors.leading_sectors[:3] if sectors.leading_sectors else ["Technology", "Healthcare"]
    print(f"  - Earnings for: {', '.join(leading)}...")
    earnings = fetch_sector_earnings(leading)

    report = MarketPulseReport(
        vix=vix,
        fed_rate=fed_rate,
        margin_debt=margin_debt,
        sectors=sectors,
        earnings=earnings
    )

    print("  - Generating analysis...")
    report.ai_analysis = get_ai_analysis(report)

    return report


def print_report(report: MarketPulseReport):
    """Print report to console."""
    print("\n" + "=" * 60)
    print("MARKET PULSE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    print(f"\n{'OVERALL:':<20} {report.signal_strength} ({report.buy_signals_count}/5 signals)")
    print("-" * 60)

    # VIX
    vix = report.vix
    signal = "[BUY SIGNAL]" if vix.is_buy_signal else ""
    print(f"{'1. VIX:':<20} {vix.current or 'N/A':<10} {vix.fear_level:<15} {signal}")

    # Fed Rate
    fed = report.fed_rate
    signal = "[BUY SIGNAL]" if fed.is_buy_signal else ""
    print(f"{'2. Fed Rate:':<20} {str(fed.current) + '%' if fed.current else 'N/A':<10} {fed.trend:<15} {signal}")

    # Margin Debt
    margin = report.margin_debt
    signal = "[BUY SIGNAL]" if margin.is_buy_signal else ""
    val = f"${margin.current_billions}B" if margin.current_billions else "N/A"
    print(f"{'3. Margin Debt:':<20} {val:<10} {margin.trend:<15} {signal}")

    # Sectors
    sectors = report.sectors
    signal = "[BUY SIGNAL]" if sectors.has_clear_leaders else ""
    leaders = ", ".join(sectors.leading_sectors[:2]) if sectors.leading_sectors else "N/A"
    print(f"{'4. Sector Leaders:':<20} {leaders:<25} {signal}")

    # Earnings
    earnings = report.earnings
    signal = "[BUY SIGNAL]" if earnings.has_strong_earnings else ""
    healthy = ", ".join(earnings.healthy_sectors[:2]) if earnings.healthy_sectors else "N/A"
    print(f"{'5. Strong Earnings:':<20} {healthy:<25} {signal}")

    print("-" * 60)
    print("\nANALYSIS:")
    print(report.ai_analysis or "No analysis available")
    print("=" * 60)


def run_scheduled():
    """Run on a schedule (9:30 AM and 4:00 PM ET)."""
    import schedule
    import time

    def job():
        print(f"\n[{datetime.now()}] Running scheduled report...")
        report = fetch_all_data()
        print_report(report)
        send_email_report(report)

    # Schedule for market open and close (adjust for your timezone)
    schedule.every().monday.at("09:30").do(job)
    schedule.every().tuesday.at("09:30").do(job)
    schedule.every().wednesday.at("09:30").do(job)
    schedule.every().thursday.at("09:30").do(job)
    schedule.every().friday.at("09:30").do(job)

    schedule.every().monday.at("16:00").do(job)
    schedule.every().tuesday.at("16:00").do(job)
    schedule.every().wednesday.at("16:00").do(job)
    schedule.every().thursday.at("16:00").do(job)
    schedule.every().friday.at("16:00").do(job)

    print("Scheduler started. Reports at 9:30 AM and 4:00 PM (Mon-Fri)")
    print("Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Market Pulse - Stock Buying Opportunity Tracker")
    parser.add_argument("--email", action="store_true", help="Send report via email")
    parser.add_argument("--schedule", action="store_true", help="Run on schedule (9:30 AM, 4:00 PM)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.schedule:
        run_scheduled()
        return

    # Single run
    report = fetch_all_data()

    if args.json:
        import json
        print(json.dumps(report.to_dict(), indent=2, default=str))
    else:
        print_report(report)

    if args.email:
        send_email_report(report)


if __name__ == "__main__":
    main()
